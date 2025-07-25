from flask import Flask, jsonify
import requests
import smtplib
from email.message import EmailMessage
from datetime import datetime

app = Flask(__name__)

API_URL = "https://api.hooklab.com.br/offers?offset=0&limit=100"
API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.ST7vv73vv70BJO-_vdKJBe-_ve-_ve-_vUbvv71p.LDy2xFueZDZwlWcmOZIOQ96eG74qQ0N1Rc_9bxPvDYs"
EMAIL_REMETENTE = "comercial@singularbaby.com.br"
EMAIL_SENHA = "dkvk ghme rkmu imia"
EMAIL_DESTINO = "luissilva@madeiranit.com.br"

WHATSAPP_API_URL = ""
WHATSAPP_NUMERO = ""

def consultar_precos():
    # Opção 1: Header com "Authorization: Bearer"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }

    # 👉 Se a opção 1 não funcionar, comente ela e ative a opção 2:
    # headers = {
    #     "access_token": API_TOKEN
    # }

    # 👉 Se nenhuma funcionar, tente a opção 3 com token na URL:
    # url = f"https://api.hooklab.com.br/offers?offset=0&limit=100&access-token={API_TOKEN}"
    # res = requests.get(url)
    # return ...

    res = requests.get(API_URL, headers=headers)
    res.raise_for_status()
    data = res.json().get("data", [])
    alertas = []
    for oferta in data:
        preco = oferta.get("price")
        min_preco = oferta.get("markups", {}).get("monetary_min_price")
        max_preco = oferta.get("markups", {}).get("monetary_max_price")
        if preco is None or min_preco is None or max_preco is None:
            continue
        if preco < min_preco or preco > max_preco:
            alertas.append({
                "cliente": oferta.get("store", {}).get("name"),
                "produto": oferta.get("title"),
                "link": oferta.get("offer_link"),
                "preco_atual": preco,
                "preco_ideal_min": min_preco,
                "preco_ideal_max": max_preco
            })
    return alertas

def formatar_mensagem(alertas):
    texto = f"Alertas de preços fora do ideal ({datetime.now().strftime('%d/%m/%Y %H:%M')}):\n"
    for a in alertas:
        texto += f"""
Cliente: {a['cliente']}
Produto: {a['produto']}
Link: {a['link']}
Preço atual: R$ {a['preco_atual']}
Faixa ideal: R$ {a['preco_ideal_min']} ~ R$ {a['preco_ideal_max']}\n"""
    return texto

def enviar_email(mensagem):
    msg = EmailMessage()
    msg['Subject'] = 'Alerta de Preços Fora do Ideal - Hooklab'
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINO
    msg.set_content(mensagem)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_REMETENTE, EMAIL_SENHA)
        smtp.send_message(msg)

def enviar_whatsapp(mensagem):
    if WHATSAPP_API_URL and WHATSAPP_NUMERO:
        payload = {"phone": WHATSAPP_NUMERO, "message": mensagem}
        headers = {"Content-Type": "application/json"}
        requests.post(WHATSAPP_API_URL, json=payload, headers=headers)

@app.route("/", methods=["GET"])
def home():
    return "Servidor Flask rodando com sucesso!"

@app.route("/executar-alerta", methods=["POST"])
def executar_alerta():
    try:
        alertas = consultar_precos()
        if alertas:
            mensagem = formatar_mensagem(alertas)
            try:
                enviar_email(mensagem)
            except Exception as e:
                print("Erro ao enviar email:", str(e))
            try:
                enviar_whatsapp(mensagem)
            except Exception as e:
                print("Erro ao enviar WhatsApp:", str(e))
            return jsonify({"status": "ok", "mensagem": "Alertas processados com sucesso"}), 200
        else:
            return jsonify({"status": "ok", "mensagem": "Todos os preços estão corretos"}), 200
    except Exception as e:
        print("Erro geral:", str(e))
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
