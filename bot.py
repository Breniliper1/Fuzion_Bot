import os import sqlite3 import time from threading import Thread

import requests import telebot from flask import Flask, request

"""bot.py – Futzion Bot pronto para Render

Cria/usa banco SQLite em ./db/users.db

Recebe webhook do Telegram via Flask

Consulta The Odds API para apostas de valor

Envia alertas a usuários ativos """

Variáveis de ambiente (Render)

TOKEN        = os.environ.get("BOT_TOKEN")       # token do Telegram ODDS_API_KEY = os.environ.get("ODDS_API_KEY")    # key da The Odds API URL_WEBHOOK  = os.environ.get("WEBHOOK_URL")     # https://<service>.onrender.com/webhook

Validação simples para evitar falhas silenciosas

for var, value in {"BOT_TOKEN": TOKEN, "ODDS_API_KEY": ODDS_API_KEY, "WEBHOOK_URL": URL_WEBHOOK}.items(): if not value: raise RuntimeError(f"Variável de ambiente obrigatória não definida: {var}")

Banco de dados SQLite (efêmero)

os.makedirs("db", exist_ok=True) conn   = sqlite3.connect("db/users.db", check_same_thread=False) cursor = conn.cursor() cursor.execute( """ CREATE TABLE IF NOT EXISTS users ( telegram_id     TEXT PRIMARY KEY, nome            TEXT, data_expiracao  INTEGER ) """ ) conn.commit()

Bot Telegram

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

@bot.message_handler(commands=["start"]) def send_welcome(message): telegram_id = str(message.chat.id) cursor.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)) user = cursor.fetchone()

if user and int(user[2]) > int(time.time()):
    bot.reply_to(message, "✅ <b>Acesso liberado.</b> Você receberá os alertas em tempo real!")
elif user:
    bot.reply_to(message, "⛔ <b>Seu plano expirou.</b>")
else:
    bot.reply_to(message, "👋 <b>Olá!</b> Você ainda não tem acesso. Em breve estará disponível.")

def enviar_alerta_para_ativos(texto: str): cursor.execute("SELECT telegram_id FROM users WHERE data_expiracao > ?", (int(time.time()),)) for (telegram_id,) in cursor.fetchall(): try: bot.send_message(telegram_id, texto) except Exception: continue

def calcular_valor(odd1: float, odd2: float) -> float: """Retorna o valor estimado arbitrário (>1 indica aposta de valor).""" prob1, prob2 = (1 / odd1), (1 / odd2) soma_prob    = prob1 + prob2 return 1 / soma_prob if soma_prob else 0

def verificar_apostas_valiosas(): """Consulta The Odds API e envia alertas para odds de valor.""" esportes = requests.get( f"https://api.the-odds-api.com/v4/sports/?apiKey={ODDS_API_KEY}", timeout=10, ).json()

for esporte in esportes:
    esporte_key = esporte["key"]
    odds_data = requests.get(
        f"https://api.the-odds-api.com/v4/sports/{esporte_key}/odds/"
        f"?regions=us&markets=h2h,spreads,totals&apiKey={ODDS_API_KEY}",
        timeout=10,
    ).json()

    for evento in odds_data:
        for bookmaker in evento.get("bookmakers", []):
            odds_list = bookmaker["markets"][0]["outcomes"]
            if len(odds_list) < 2:
                continue
            odd_1, odd_2 = odds_list[0]["price"], odds_list[1]["price"]
            valor_estimado = calcular_valor(odd_1, odd_2)
            if valor_estimado >= 1.1:
                mensagem = (
                    f"⚽ <b>Jogo:</b> {evento['home_team']} x {evento['away_team']}\n"
                    f"📊 <b>Casa:</b> {odd_1} | <b>Fora:</b> {odd_2}\n"
                    f"📈 <b>Valor estimado:</b> {valor_estimado:.2f}"
                )
                enviar_alerta_para_ativos(mensagem)

Flask Webhook

app = Flask(name)

@app.route("/") def home(): return "Futzion Bot Online!"

@app.route("/webhook", methods=["POST"]) def webhook(): update = telebot.types.Update.de_json(request.data.decode("utf-8")) bot.process_new_updates([update]) return "OK", 200

@app.before_first_request def activate_webhook(): bot.remove_webhook() bot.set_webhook(URL_WEBHOOK)

Execução local/Render

if name == "main": # Loop em thread paralela para consultas à The Odds API def loop_apostas(): while True: try: verificar_apostas_valiosas() except Exception: pass time.sleep(300)  # 5 min

Thread(target=loop_apostas, daemon=True).start()
app.run(host="0.0.0.0", port=10000)

