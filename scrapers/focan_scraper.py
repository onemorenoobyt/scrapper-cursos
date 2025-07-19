# Contenido de scrapers/focan_scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys
sys.path.append('.')
import config

URL = "https://focan.es/resultados-busqueda/?sede=Tenerife&colectivo=Desempleados&modalidad=&categoria_comercial=&buscar="
CENTRO_NOMBRE = "Focan"

def _normalize_date(date_string):
    """Convierte fechas como '22/07/2024' a 'YYYY-MM-DD'."""
    try:
        dt_object = datetime.strptime(date_string, '%d/%m/%Y')
        return dt_object.strftime('%Y-%m-%d')
    except ValueError:
        return "Formato de fecha no reconocido"

def scrape():
    """Extrae los cursos de Focan."""
    print(f"Iniciando scraper para {CENTRO_NOMBRE}...")
    try:
        response = requests.get(URL, headers=config.HEADERS)
        response.raise_for_status()
        soup_title = BeautifulSoup(response.content, 'html.parser').title
        title_text = soup_title.string if soup_title else "No se encontró título"
        print(f"  -> Conexión exitosa con {CENTRO_NOMBRE}. Título de la página: {title_text}")
    except requests.RequestException as e:
        print(f"  !!! ERROR DE CONEXIÓN en {CENTRO_NOMBRE}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    cursos_encontrados = []
    
    course_list = soup.find('div', class_='module-content')
    if not course_list:
        print(f"  !!! ERROR: No se encontró el contenedor de cursos en {CENTRO_NOMBRE}. La estructura de la página puede haber cambiado o estamos bloqueados.")
        return []

    for item in course_list.find_all('div', class_='item'):
        try:
            nombre = item.find('h2').text.strip()
            url_curso = item.find('a')['href']
            info_p = item.find_all('p')
            fecha_inicio_str = info_p[0].text.replace('Fecha de Inicio:', '').strip()
            horario = info_p[1].text.replace('Horario:', '').strip()
            
            curso_data = {
                "centro": CENTRO_NOMBRE,
                "nombre": nombre,
                "url": url_curso,
                "inicio": _normalize_date(fecha_inicio_str),
                "fin": "No disponible en listado",
                "horario": horario,
                "horas": 0
            }
            cursos_encontrados.append(curso_data)
        except (AttributeError, IndexError) as e:
            print(f"  -> Error al procesar un curso de {CENTRO_NOMBRE}: {e}")
            continue
            
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados

if __name__ == '__main__':
    cursos = scrape()
    for c in cursos:
        print(c)