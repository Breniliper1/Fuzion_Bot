# Futzion Bot – Deploy no Render.com

## 🚀 Sobre

Este é um bot de Telegram que consulta odds de partidas (via The Odds API) e envia alertas de apostas valiosas automaticamente.

## ✅ Requisitos para rodar no [Render.com](https://render.com)

### 1. Variáveis de Ambiente

Configure no painel do Render (Settings > Environment):

| Variável         | Descrição                            |
|------------------|--------------------------------------|
| `TOKEN_TELEGRAM` | Token do seu bot Telegram            |
| `URL_WEBHOOK`    | URL do seu app + `/webhook`          |
| `API_ODDS_KEY`   | Chave de acesso da The Odds API      |

Exemplo de URL_WEBHOOK:
```
https://seu-projeto.onrender.com/webhook
```

---

### 2. Deploy

1. Faça upload do projeto ou conecte via GitHub.
2. Render detectará o `Procfile` e instalará os requisitos.
3. Após o deploy, envie `/start` para o seu bot no Telegram.
4. Pronto! Você receberá alertas automaticamente.

---

### 3. Testes

Você pode verificar se o bot está online acessando:

```
https://seu-projeto.onrender.com/
```

Se tudo estiver certo, você verá:

```
Futzion Bot Online!
```
