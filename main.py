import requests
from bs4 import BeautifulSoup

# Valor UF actual (puedes hacer esto dinámico luego con una API o scraping)
VALOR_UF = 37000

URL = "https://www.portalinmobiliario.com/arriendo/departamento/2-dormitorios/providencia-metropolitana/_OrderId_PRICE_NoIndex_True"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def buscar_arriendos():
    OFFSET = 0
    RESULTADOS_POR_PAGINA = 48
    SEGUIR = True

    while SEGUIR:
        url_pagina = f"{URL}/_Desde_{OFFSET}" if OFFSET > 0 else URL
        response = requests.get(url_pagina, headers=HEADERS)

        if response.status_code != 200:
            print(f"Error al hacer la petición: {response.status_code}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        publicaciones = soup.select("li.ui-search-layout__item")

        if not publicaciones:
            print("🔚 No hay más publicaciones.")
            break

        for pub in publicaciones:
            try:
                titulo = pub.select_one("h3").text.strip()
                precio_element = pub.select_one(".andes-money-amount")
                moneda = precio_element.select_one(".andes-money-amount__currency-symbol").text.strip()
                fraccion = precio_element.select_one(".andes-money-amount__fraction").text.strip()
                link = pub.select_one("a")["href"]
                ubicacion = pub.select_one(".poly-component__location").text.strip()

                if moneda == "UF":
                    centavos = precio_element.select_one(".andes-money-amount__cents")
                    centavos = centavos.text.strip() if centavos else "0"
                    precio_uf = float(f"{fraccion}.{centavos}")
                    valor = int(precio_uf * VALOR_UF)
                else:
                    valor = int(fraccion.replace(".", "").replace("$", ""))

                if valor > 650000:
                    SEGUIR = False
                    break  # Sal del bucle interno también

                print("🏠", titulo)
                print("💰", f"${int(valor):,}".replace(",", "."))
                print("📍", ubicacion)
                print("🔗", link)
                print("-" * 40)

            except Exception as e:
                continue

        OFFSET += RESULTADOS_POR_PAGINA


if __name__ == "__main__":
    buscar_arriendos()
