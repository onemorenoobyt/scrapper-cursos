# Contenido de scrapers/cep_scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

BASE_URL = "https://cursostenerife.es/"
CENTRO_NOMBRE = "CEP"

def _normalize_date(date_string):
    """Convierte fechas como '13 de Enero de 2025' a 'YYYY-MM-DD'."""
    meses = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04', 'mayo': '05', 'junio': '06',
        'julio': '07', 'agosto': '08', 'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }
    try:
        parts = date_string.lower().split(' de ')
        day = int(parts[0])
        month = meses[parts[1]]
        year = int(parts[2])
        return f"{year}-{month}-{day:02d}"
    except (ValueError, IndexError, KeyError):
        return "Formato de fecha no reconocido"

def scrape():
    """Extrae los cursos de CEP."""
    print(f"Iniciando scraper para {CENTRO_NOMBRE}...")
    try:
        response = requests.get(BASE_URL)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error al acceder a {BASE_URL}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    cursos_encontrados = []
    
    # Buscamos la tabla que contiene los cursos
    tabla = soup.find('table')
    if not tabla:
        print(f"No se encontró la tabla de cursos en {CENTRO_NOMBRE}.")
        return []
    
    rows = tabla.find('tbody').find_all('tr')
    
    for row in rows:
        try:
            cols = row.find_all('td')
            if len(cols) < 5: # Si la fila no tiene suficientes columnas, la saltamos
                continue

            # El filtro clave es la sede
            sede = cols[5].text.strip()
            if "SANTA CRUZ" not in sede.upper():
                continue

            fecha_inicio_str = cols[0].text.strip()
            nombre = cols[1].text.strip()
            url_curso = urljoin(BASE_URL, cols[1].find('a')['href'])
            horas_str = cols[2].text.strip()
            horario = cols[4].text.strip()

            curso_data = {
                "centro": CENTRO_NOMBRE,
                "nombre": nombre,
                "url": url_curso,
                "inicio": _normalize_date(fecha_inicio_str),
                "fin": "No disponible en listado", # Este dato no está en la tabla
                "horario": horario,
                "horas": int(horas_str) if horas_str.isdigit() else 0
            }
            cursos_encontrados.append(curso_data)
        except (AttributeError, IndexError, ValueError) as e:
            print(f"Error al procesar una fila de {CENTRO_NOMBRE}: {e}")
            continue
            
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados

if __name__ == '__main__':
    cursos = scrape()
    for c in cursos:
        print(c)