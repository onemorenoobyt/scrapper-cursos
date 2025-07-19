# Contenido de scrapers/icse_scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://www.icse.es/cursos?type=2&island=Tenerife"
CENTRO_NOMBRE = "ICSE"

def _normalize_date(date_string):
    """Convierte fechas como '13/10/2025' a 'YYYY-MM-DD'."""
    try:
        dt_object = datetime.strptime(date_string, '%d/%m/%Y')
        return dt_object.strftime('%Y-%m-%d')
    except ValueError:
        return "Formato de fecha no reconocido"

def scrape():
    """Extrae los cursos de ICSE filtrando por Santa Cruz."""
    print(f"Iniciando scraper para {CENTRO_NOMBRE}...")
    try:
        response = requests.get(URL)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error al acceder a {URL}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    cursos_encontrados = []
    
    course_list = soup.find_all('div', class_='course-item')
    if not course_list:
        print(f"No se encontró la lista de cursos en {CENTRO_NOMBRE}.")
        return []

    for item in course_list:
        try:
            sede_tag = item.find('li', class_='locality')
            if sede_tag and "STA. CRUZ DE TENERIFE" in sede_tag.text.upper():
                nombre = item.find('h3').text.strip()
                url_curso = item.find('a')['href']
                
                fechas = item.find('span', class_='date').text.strip()
                fecha_inicio_str, fecha_fin_str = fechas.split(' - ')

                curso_data = {
                    "centro": CENTRO_NOMBRE,
                    "nombre": nombre,
                    "url": url_curso,
                    "inicio": _normalize_date(fecha_inicio_str.strip()),
                    "fin": _normalize_date(fecha_fin_str.strip()),
                    "horario": "No disponible en listado",
                    "horas": 0
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