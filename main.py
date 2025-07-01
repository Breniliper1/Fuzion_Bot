import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from keep_alive import keep_alive

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    msg = f"👋 Olá {user_first_name}!"
\nSou o Futzion_Bot, seu assistente de previsões de futebol.\n\nEsta é a versão de testes.\nUse /previsao para ver um exemplo."
    await update.message.reply_text(msg)

# /ajuda
async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📌 *Comandos disponíveis:*\n\n/start – Iniciar o bot\n/previsao – Ver exemplo de previsão\n/ajuda – Ver esta mensagem\n/suporte – Contato com a equipe"
    await update.message.reply_text(msg, parse_mode='Markdown')

# /previsao
async def previsao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🔮 *Previsão de Hoje (Exemplo)*\n\nPartida: Real Madrid x Barcelona\nPalpite: Ambas Marcam ✅\nConfiança: Alta\nHorário: 17h00\nLiga: La Liga\n\n⚠️ Esta é uma simulação de teste."
    await update.message.reply_text(msg, parse_mode='Markdown')

# /suporte
async def suporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📞 *Suporte Oficial:*\n\nTelegram: @ImperioHibridoSuporte\nE-mail: suporte@imperiohibrido.com"
    await update.message.reply_text(msg, parse_mode='Markdown')

def main():
    keep_alive()
    app = ApplicationBuilder().token("7590417028:AAH1vJ6Uk9rrYVFwambLEtncoDQBfU-xv1o").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("previsao", previsao))
    app.add_handler(CommandHandler("suporte", suporte))

    print("✅ Bot rodando no Render...")
    app.run_polling()

if __name__ == "__main__":
    main()
