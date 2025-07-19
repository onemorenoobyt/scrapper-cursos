# Contenido de scrapers/insforca_scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://www.insforca.com/formacion/cursos-gratuitos-prioritariamente-para-desempleados-as/"
CENTRO_NOMBRE = "Insforca"

def _normalize_date(date_string):
    """Convierte fechas como '13/08/2025' a 'YYYY-MM-DD'."""
    try:
        dt_object = datetime.strptime(date_string, '%d/%m/%Y')
        return dt_object.strftime('%Y-%m-%d')
    except ValueError:
        return "Formato de fecha no reconocido"

def scrape():
    """
    Extrae los cursos de Insforca para desempleados en Tenerife
    que tienen una fecha de inicio especificada.
    """
    print(f"Iniciando scraper para {CENTRO_NOMBRE}...")
    try:
        response = requests.get(URL)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error al acceder a {URL}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    cursos_encontrados = []
    
    course_list = soup.find_all('div', class_='item-curso')
    if not course_list:
        print(f"No se encontró la lista de cursos en {CENTRO_NOMBRE}.")
        return []

    for item in course_list:
        try:
            participantes_tag = item.find('div', class_='participantes-curso')
            if not participantes_tag or "Tenerife" not in participantes_tag.text:
                continue

            inicio_tag = item.find('div', class_='inicio-curso')
            if not inicio_tag or "INICIO:" not in inicio_tag.text.upper():
                continue

            nombre = item.find('h2').text.strip()
            
            fechas_str = inicio_tag.text.strip()
            parts = fechas_str.split('|')
            fecha_inicio_str = parts[0].replace('INICIO:', '').strip()
            fecha_fin_str = parts[1].replace('FIN:', '').strip()

            horas_tag = item.find('div', class_='duracion-curso')
            horas_str = horas_tag.text.replace('DURACIÓN:', '').replace('horas', '').strip()

            curso_data = {
                "centro": CENTRO_NOMBRE,
                "nombre": nombre,
                "url": f"{URL}#{nombre.replace(' ', '-')}",
                "inicio": _normalize_date(fecha_inicio_str),
                "fin": _normalize_date(fecha_fin_str),
                "horario": "No disponible en listado",
                "horas": int(horas_str) if horas_str.isdigit() else 0
            }
            cursos_encontrados.append(curso_data)
        except (AttributeError, IndexError, ValueError) as e:
            print(f"Error al procesar un curso de {CENTRO_NOMBRE}: {e}")
            continue
            
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados

if __name__ == '__main__':
    cursos = scrape()
    for c in cursos:
        print(c)