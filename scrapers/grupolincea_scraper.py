# Contenido de scrapers/grupolincea_scraper.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

BASE_URL = "https://grupolincea.es"
START_URL = "https://grupolincea.es/cursos-tenerife-2/"
CENTRO_NOMBRE = "Grupo Lincea"

def _normalize_date(date_string):
    """Convierte fechas como '10/07/25' a 'YYYY-MM-DD'."""
    if "No especificado" in date_string:
        return date_string
    try:
        # El año es de dos dígitos, '25' se interpretará como 2025
        dt_object = datetime.strptime(date_string, '%d/%m/%y')
        return dt_object.strftime('%Y-%m-%d')
    except ValueError:
        return "Formato de fecha no reconocido"

def _scrape_detail_page(course_url):
    """Función auxiliar para extraer datos de la página de detalle de un curso."""
    try:
        response = requests.get(course_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        fecha_label = soup.find('h2', string=lambda text: 'FECHA DE INICIO' in text if text else False)
        if not fecha_label:
            return None 

        fecha_data_tag = fecha_label.find_next_sibling('h2')
        if not fecha_data_tag or not fecha_data_tag.text.strip():
            return None

        nombre = soup.find('h1', class_='elementor-heading-title').text.strip()
        
        fechas_str = fecha_data_tag.text.strip()
        if '–' in fechas_str:
            fecha_inicio_str, fecha_fin_str = [d.strip() for d in fechas_str.split('–')]
        else:
            fecha_inicio_str = fechas_str
            fecha_fin_str = "No especificado"
            
        horario = "No especificado"
        horario_label = soup.find('h2', string=lambda text: 'HORARIO' in text if text else False)
        if horario_label:
            horario_data_tag = horario_label.find_next_sibling('h2')
            if horario_data_tag:
                horario = horario_data_tag.text.strip()

        return {
            "centro": CENTRO_NOMBRE,
            "nombre": nombre,
            "url": course_url,
            "inicio": _normalize_date(fecha_inicio_str),
            "fin": _normalize_date(fecha_fin_str),
            "horario": horario,
            "horas": 0
        }
    except (requests.RequestException, AttributeError, IndexError) as e:
        print(f"  -> Error procesando detalle del curso {course_url}: {e}")
        return None

def scrape():
    """Scraper dinámico en dos fases para Grupo Lincea."""
    print(f"Iniciando scraper para {CENTRO_NOMBRE}...")
    try:
        response = requests.get(START_URL)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error al acceder a la página principal de {CENTRO_NOMBRE}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    
    links_a_visitar = []
    course_items = soup.select('div.elementor-post__card a')
    for link in course_items:
        full_url = urljoin(BASE_URL, link['href'])
        if full_url not in links_a_visitar:
             links_a_visitar.append(full_url)
            
    if not links_a_visitar:
        print(f"No se encontraron enlaces a cursos en {CENTRO_NOMBRE}.")
        return []
        
    print(f"Descubiertos {len(links_a_visitar)} enlaces a cursos. Procediendo a extraer detalles...")

    cursos_encontrados = []
    for link in links_a_visitar:
        curso_data = _scrape_detail_page(link)
        if curso_data:
            cursos_encontrados.append(curso_data)
            
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos con fecha encontrados.")
    return cursos_encontrados

if __name__ == '__main__':
    cursos = scrape()
    for c in cursos:
        print(c)