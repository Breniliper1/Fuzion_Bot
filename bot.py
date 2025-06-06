import sqlite3
import time
import telebot
from flask import Flask, request
import requests
import os
from threading import Thread

# Variáveis de ambiente
TOKEN = os.environ.get('BOT_TOKEN')
ODDS_API_KEY = os.environ.get('ODDS_API_KEY')
URL_WEBHOOK = os.environ.get('WEBHOOK_URL')  # ex: https://seu-bot.onrender.com/webhook

# Banco de dados
os.makedirs('db', exist_ok=True)
conn = sqlite3.connect('db/users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        telegram_id TEXT PRIMARY KEY,
        nome TEXT,
        data_expiracao INTEGER
    )
''')
conn.commit()

# Telegram bot
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    telegram_id = str(message.chat.id)
    cursor.execute('SELECT * FROM users WHERE telegram_id=?', (telegram_id,))
    user = cursor.fetchone()

    if user and int(user[2]) > int(time.time()):
        bot.reply_to(message, "✅ <b>Acesso liberado.</b> Você receberá os alertas em tempo real!")
    elif user:
        bot.reply_to(message, "⛔ <b>Seu plano expirou.</b>")
    else:
        bot.reply_to(message, "👋 <b>Olá!</b> Você ainda não tem acesso. Em breve estará disponível.")

def enviar_alerta_para_ativos(texto):
    cursor.execute("SELECT telegram_id FROM users WHERE data_expiracao > ?", (int(time.time()),))
    usuarios = cursor.fetchall()
    for u in usuarios:
        try:
            bot.send_message(u[0], texto)
        except Exception:
            continue

def verificar_apostas_valiosas():
    url = f'https://api.the-odds-api.com/v4/sports/?apiKey={ODDS_API_KEY}'
    esportes = requests.get(url).json()

    for esporte in esportes:
        esporte_key = esporte['key']
        url_odds = f'https://api.the-odds-api.com/v4/sports/{esporte_key}/odds/?regions=us&markets=h2h,spreads,totals&apiKey={ODDS_API_KEY}'
        odds_data = requests.get(url_odds).json()

        for evento in odds_data:
            if 'bookmakers' in evento:
                for bookmaker in evento['bookmakers']:
                    odds = bookmaker['markets'][0]['outcomes']
                    if len(odds) >= 2:
                        odd_1 = odds[0]['price']
                        odd_2 = odds[1]['price']
                        valor_estimado = calcular_valor(odd_1, odd_2)
                        if valor_estimado >= 1.1:
                            mensagem = f"⚽ <b>Jogo:</b> {evento['home_team']} x {evento['away_team']}\n"                                        f"📊 <b>Casa:</b> {odd_1} | <b>Fora:</b> {odd_2}\n"                                        f"📈 <b>Valor estimado:</b> {valor_estimado:.2f}"
                            enviar_alerta_para_ativos(mensagem)

def calcular_valor(odd1, odd2):
    prob1 = 1 / odd1
    prob2 = 1 / odd2
    valor_total = prob1 + prob2
    return 1 / valor_total if valor_total != 0 else 0

# Flask
app = Flask(__name__)

@app.route('/')
def home():
    return 'Futzion Bot Online!'

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return 'OK', 200

@app.before_first_request
def activate_webhook():
    bot.remove_webhook()
    bot.set_webhook(URL_WEBHOOK)

if __name__ == '__main__':
    def loop_apostas():
        while True:
            verificar_apostas_valiosas()
            time.sleep(300)  # 5 minutos
    Thread(target=loop_apostas, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)