        for bookmaker in evento.get("bookmakers", []):More actions
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
app = Flask(name)Add commentMore actions

@app.route("/") def home(): return "Futzion Bot Online!"

@app.route("/webhook", methods=["POST"]) def webhook(): update = telebot.types.Update.de_json(request.data.decode("utf-8")) bot.process_new_updates([update]) return "OK", 200

@app.before_first_request def activate_webhook(): bot.remove_webhook() bot.set_webhook(URL_WEBHOOK)
Execução local/RenderAdd commentMore actions
if name == "main": # Loop em thread paralela para consultas à The Odds API def loop_apostas(): while True: try: verificar_apostas_valiosas() except Exception: pass time.sleep(300)  # 5 minAdd commentMore actions

Thread(target=loop_apostas, daemon=True).start()
app.run(host="0.0.0.0", port=10000)
~