from flask import Flask
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

URL = "https://www.portalinmobiliario.com/arriendo/departamento/2-dormitorios/providencia-metropolitana/_OrderId_PRICE_NoIndex_True"
HEADERS = {"User-Agent": "Mozilla/5.0"}
UF_HOY = 37000  # Valor de la UF, puedes actualizarlo automáticamente después

def buscar_arriendos():
    response = requests.get(URL, headers=HEADERS)

    if response.status_code != 200:
        return f"Error al hacer la petición: {response.status_code}"

    soup = BeautifulSoup(response.text, "html.parser")
    publicaciones = soup.select("li.ui-search-layout__item")

    if not publicaciones:
        return "No se encontraron resultados."

    resultados = []

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

            if precio_en_pesos <= 650000:
                resultados.append(f"""
                🏠 {titulo}
                💰 ${precio_en_pesos:,}
                📍 {ubicacion}
                🔗 {link}
                -------------------------
                """)
        except Exception:
            continue

    return "<br>".join(resultados) if resultados else "No hay resultados bajo $650.000."

@app.route("/")
def home():
    return buscar_arriendos()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
