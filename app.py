import os
import time
from threading import Thread
import logging
import requests
import telebot
from flask import Flask, request, abort

# -------------------- CONFIGURAÇÕES VIA VARIÁVEL DE AMBIENTE --------------------
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
URL_WEBHOOK   = os.getenv("URL_WEBHOOK")
API_ODDS_KEY  = os.getenv("API_ODDS_KEY")
PORT          = int(os.getenv("PORT", 10000))

if not TOKEN_TELEGRAM:
    raise RuntimeError("A variável de ambiente TOKEN_TELEGRAM não está definida.")

# -------------------- LOGGING --------------------
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# -------------------- INSTÂNCIAS --------------------
bot = telebot.TeleBot(TOKEN_TELEGRAM, parse_mode='HTML')
app = Flask(__name__)
usuarios_ativos = set()

# -------------------- HANDLERS TELEGRAM --------------------
@bot.message_handler(commands=['start'])
def cmd_start(message):
    chat_id = message.chat.id
    if chat_id not in usuarios_ativos:
        usuarios_ativos.add(chat_id)
    bot.send_message(chat_id, '✅ Você está inscrito para receber alertas de apostas valiosas.')

# -------------------- LÓGICA DE NEGÓCIO --------------------
def obter_eventos():
    if not API_ODDS_KEY:
        logger.warning("API_ODDS_KEY não definida; retornando lista vazia.")
        return []
    url = 'https://api.the-odds-api.com/v4/sports/soccer_epl/odds'
    params = {
        'apiKey': API_ODDS_KEY,
        'regions': 'eu',
        'markets': 'h2h',
        'oddsFormat': 'decimal'
    }
    try:
        resposta = requests.get(url, params=params, timeout=10)
        resposta.raise_for_status()
        return resposta.json()
    except requests.RequestException as exc:
        logger.error(f'Erro ao obter eventos: {exc}')
        return []

def calcular_valor(odd_1, odd_2):
    try:
        prob_1 = 1 / odd_1
        prob_2 = 1 / odd_2
        margem = prob_1 + prob_2
        return 1 / margem
    except ZeroDivisionError:
        return 0.0

def enviar_alerta(mensagem):
    for chat_id in list(usuarios_ativos):
        try:
            bot.send_message(chat_id, mensagem)
        except Exception as exc:
            logger.error(f'Falha ao enviar mensagem para {chat_id}: {exc}')

def verificar_apostas_valiosas():
    eventos = obter_eventos()
    if not eventos:
        logger.info('Nenhum evento recebido.')
        return

    for evento in eventos:
        for casa in evento.get('bookmakers', []):
            markets = casa.get('markets', [])
            if not markets:
                continue
            outcomes = markets[0].get('outcomes', [])
            if len(outcomes) < 2:
                continue

            odd_casa = outcomes[0].get('price')
            odd_fora = outcomes[1].get('price')
            if not isinstance(odd_casa, (int, float)) or not isinstance(odd_fora, (int, float)):
                continue

            valor = calcular_valor(odd_casa, odd_fora)
            if valor >= 1.1:
                mensagem = (
                    f"⚽ <b>Jogo:</b> {evento.get('home_team')} x {evento.get('away_team')}
"
                    f"📊 <b>Odds:</b> Casa {odd_casa} · Fora {odd_fora}
"
                    f"💸 <b>Valor estimado:</b> {valor:.2f}"
                )
                enviar_alerta(mensagem)

# -------------------- FLASK / WEBHOOK --------------------
@app.route('/', methods=['GET'])
def status():
    return 'Futzion Bot Online!', 200

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    if request.headers.get('content-type') != 'application/json':
        abort(400)
    try:
        update = telebot.types.Update.de_json(request.data.decode('utf-8'))
        bot.process_new_updates([update])
    except Exception as exc:
        logger.error(f'Erro webhook: {exc}')
        abort(500)
    return 'OK', 200

@'_got_first_request'
def setup_webhook():
    logger.info('Configurando webhook…')
    bot.remove_webhook()
    if URL_WEBHOOK:
        bot.set_webhook(URL_WEBHOOK)
        logger.info('Webhook configurado.')
    else:
        logger.warning('URL_WEBHOOK não definida; webhook não será registrado.')

# -------------------- LOOP DE VERIFICAÇÃO EM THREAD --------------------
def loop_apostas():
    logger.info('Thread de verificação de apostas iniciada.')
    while True:
        try:
            verificar_apostas_valiosas()
        except Exception as exc:
            logger.error(f'Erro no loop de apostas: {exc}')
        time.sleep(300)

# -------------------- MAIN --------------------
if __name__ == '__main__':
    Thread(target=loop_apostas, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)