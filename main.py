from flask import Flask
import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import asyncio
from telegram import Bot
import unicodedata
from datetime import datetime

app = Flask(__name__)

URL = "https://www.portalinmobiliario.com/arriendo/departamento/2-dormitorios/providencia-metropolitana/_OrderId_PRICE_NoIndex_True"
HEADERS = {"User-Agent": "Mozilla/5.0"}
UF_HOY = 39264  # Puedes actualizarlo automáticamente si quieres

def registrar_log():
    print(f"[{datetime.now()}] 🔄 Visita recibida, ejecutando scrapeo...")

# --- Utilidad: normalizar texto ---
def normalizar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    return texto.replace(" ", "")

# --- Verificadores de URLs ya vistas ---
def identificador_ya_visto(identificador):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("https://susanjeann.com/alerta-portal/portal-alerta-55e2387fd1fe.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("Alerta Portal").worksheet("Identificadores vistos")
        identificadores = sheet.col_values(1)
        return identificador in identificadores
    except Exception as e:
        print("Error revisando identificador en Google Sheets:", e)
        return False

def guardar_identificador(identificador):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("https://susanjeann.com/alerta-portal/portal-alerta-55e2387fd1fe.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("Alerta Portal").worksheet("Identificadores vistos")
        sheet.append_row([identificador])
    except Exception as e:
        print("Error guardando identificador en Google Sheets:", e)

# --- Envío de mensaje a Telegram ---
def enviar_telegram_mensaje(mensaje):
    async def enviar():
        TOKEN = "7521216681:AAFp5KoLQqbpdnkkW9uZTsNItARgOFXzEEg"
        CHAT_ID = 692301270
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=mensaje)

    try:
        asyncio.run(enviar())
        print("Mensaje enviado con éxito")
    except Exception as e:
        print("Error al enviar mensaje:", e)

# --- Guardado en Google Sheets ---
def guardar_en_sheets(data):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("https://susanjeann.com/alerta-portal/portal-alerta-55e2387fd1fe.json", scope)
        client = gspread.authorize(creds)

        sheet = client.open("Alerta Portal").sheet1
        for resultado in data:
            sheet.append_row(resultado)
    except Exception as e:
        print("Error al guardar en Google Sheets:", e)

# --- Scraping y lógica principal ---
def buscar_arriendos():
    response = requests.get(URL, headers=HEADERS)

    if response.status_code != 200:
        return f"Error al hacer la petición: {response.status_code}"

    soup = BeautifulSoup(response.text, "html.parser")
    publicaciones = soup.select("li.ui-search-layout__item")

    if not publicaciones:
        return "No se encontraron resultados."

    resultados = []
    resultados_para_sheet = []

    for pub in publicaciones:
        try:
            titulo = pub.select_one("h3").text.strip()
            moneda = pub.select_one(".andes-money-amount__currency-symbol").text.strip()
            precio_str = pub.select_one(".andes-money-amount__fraction").text.strip()
            ubicacion = pub.select_one(".poly-component__location").text.strip()
            link = pub.select_one("a")["href"]

            if moneda == "UF":
                decimal = pub.select_one(".andes-money-amount__cents")
                precio_float = float(precio_str.replace(".", "")) + (float(decimal.text) / 100 if decimal else 0)
                precio_en_pesos = int(precio_float * UF_HOY)
            else:
                precio_en_pesos = int(precio_str.replace(".", "").replace("$", ""))

            # Creamos un identificador único para esta publicación
            identificador = normalizar(f"{titulo}-{ubicacion}-{precio_en_pesos}")

            if precio_en_pesos <= 650000 and not identificador_ya_visto(identificador):
                resultados.append(f"""
                🏠 {titulo}
                💰 ${precio_en_pesos:,}
                📍 {ubicacion}
                🔗 {link}
                -------------------------
                """)

                guardar_identificador(identificador)

                mensaje = f"🏠 {titulo}\n💰 ${precio_en_pesos}\n📍 {ubicacion}\n🔗 {link}"
                enviar_telegram_mensaje(mensaje)

                resultados_para_sheet.append([titulo, precio_en_pesos, ubicacion, link])
        except Exception:
            continue

    if resultados_para_sheet:
        guardar_en_sheets(resultados_para_sheet)

    return "<br>".join(resultados) if resultados else "No hay resultados bajo $650.000."

# --- Flask route ---
@app.route("/")
def home():
    registrar_log()
    return buscar_arriendos()

# --- Inicio ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000) 
