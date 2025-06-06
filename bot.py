import os
import time
from threading import Thread
import logging
import requests
import telebot
from flask import Flask, request, abort

# Configurações via variáveis de ambiente
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
URL_WEBHOOK = os.getenv("URL_WEBHOOK")
API_ODDS_KEY = os.getenv("API_ODDS_KEY")
PORT = int(os.getenv("PORT", 10000))

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s"
)
logger = logging.getLogger()

# Instanciando bot e app Flask
bot = telebot.TeleBot(TOKEN_TELEGRAM, parse_mode="HTML")
app = Flask(__name__)

# Armazena os usuários ativos que enviaram /start (em memória)
usuarios_ativos = set()

@bot.message_handler(commands=["start"])
def registrar_usuario(message):
    chat_id = message.chat.id
    usuarios_ativos.add(chat_id)
    bot.send_message(chat_id, "Olá! Você está registrado para receber alertas de apostas valiosas.")

def obter_eventos() -> list:
    """Consulta eventos da The Odds API."""
    url = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"
    params = {
        "apiKey": API_ODDS_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }
    try:
        resposta = requests.get(url, params=params, timeout=10)
        resposta.raise_for_status()
        eventos = resposta.json()
        return eventos
    except requests.RequestException as e:
        logger.error(f"Erro ao obter eventos: {e}")
        return []

def calcular_valor(odd_1: float, odd_2: float) -> float:
    """Calcula o valor estimado da aposta."""
    try:
        prob_1 = 1 / odd_1
        prob_2 = 1 / odd_2
        margem = prob_1 + prob_2
        return 1 / margem
    except ZeroDivisionError:
        logger.error("Divisão por zero no cálculo de valor.")
        return 0

def enviar_alerta_para_ativos(mensagem: str) -> None:
    """Envia mensagem para todos os usuários ativos."""
    for chat_id in usuarios_ativos:
        try:
            bot.send_message(chat_id, mensagem)
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para {chat_id}: {e}")

def verificar_apostas_valiosas() -> None:
    eventos = obter_eventos()
    if not eventos:
        logger.info("Nenhum evento encontrado.")
        return

    for evento in eventos:
        for casa in evento.get("bookmakers", []):
            mercados = casa.get("markets", [])
            if not mercados:
                continue
            odds = mercados[0].get("outcomes", [])
            if len(odds) < 2:
                continue

            odd_casa = odds[0].get("price")
            odd_fora = odds[1].get("price")

            if odd_casa is None or odd_fora is None:
                continue

            valor_estimado = calcular_valor(odd_casa, odd_fora)

            if valor_estimado >= 1.1:
                mensagem = (
                    f"⚽ <b>Jogo:</b> {evento.get('home_team')} x {evento.get('away_team')}\n"
                    f"📊 <b>Odds:</b> Casa {odd_casa} | Fora {odd_fora}\n"
                    f"📈 <b>Valor estimado:</b> {valor_estimado:.2f}"
                )
                enviar_alerta_para_ativos(mensagem)

@app.route("/", methods=["GET"])
def pagina_inicial():
    return "Futzion Bot Online!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") != "application/json":
        abort(400)
    try:
        update = telebot.types.Update.de_json(request.data.decode("utf-8"))
        bot.process_new_updates([update])
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {e}")
        abort(500)
    return "OK", 200

@app._got_first_request
def ativar_webhook():
    logger.info("Configurando webhook...")
    bot.remove_webhook()
    bot.set_webhook(URL_WEBHOOK)
    logger.info(f"Webhook definido em: {URL_WEBHOOK}")

def loop_verificacao():
    logger.info("Thread de verificação iniciada.")
    while True:
        try:
            verificar_apostas_valiosas()
        except Exception as e:
            logger.error(f"Erro no loop de verificação: {e}")
        time.sleep(300)  # pausa de 5 minutos

if __name__ == "__main__":
    Thread(target=loop_verificacao, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)