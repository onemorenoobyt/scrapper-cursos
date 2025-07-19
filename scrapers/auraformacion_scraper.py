# Contenido de scrapers/auraformacion_scraper.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

BASE_URL = "https://www.auraformacion.es"
START_URL = "https://www.auraformacion.es/formacion.html"
CENTRO_NOMBRE = "Aura Formación"

def _normalize_date(date_string):
    """Convierte fechas como '17 de Noviembre de 2025' a 'YYYY-MM-DD'."""
    if "No especificado" in date_string:
        return date_string
    
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
        return "Formato de fecha no reconocido" # Devuelve un error si el formato cambia

def _scrape_detail_page(course_url):
    """Función auxiliar para extraer datos de la página de detalle de un curso."""
    try:
        response = requests.get(course_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        center_info = soup.find('div', class_='course-center-info')
        if not center_info or "TF" not in center_info.text:
            return None

        nombre = soup.find('h1').text.strip()
        features = soup.find('ul', class_='course-features')
        
        fecha_inicio_tag = features.find('strong', string="Fecha inicio:")
        fecha_inicio_str = fecha_inicio_tag.find_next_sibling('span').text.strip() if fecha_inicio_tag else "No especificado"

        fecha_fin_tag = features.find('strong', string="Fecha fin:")
        fecha_fin_str = fecha_fin_tag.find_next_sibling('span').text.strip() if fecha_fin_tag else "No especificado"

        horas_tag = features.find('strong', string="Horas totales:")
        horas_str = horas_tag.find_next_sibling('span').text.replace('horas.', '').strip() if horas_tag else "0"
        
        horario_tag = features.find('strong', string="Horario:")
        horario = horario_tag.find_next_sibling('span').text.strip() if horario_tag else "No especificado"

        return {
            "centro": CENTRO_NOMBRE,
            "nombre": nombre,
            "url": course_url,
            "inicio": _normalize_date(fecha_inicio_str),
            "fin": _normalize_date(fecha_fin_str),
            "horario": horario,
            "horas": int(horas_str) if horas_str.isdigit() else 0
        }
    except (requests.RequestException, AttributeError, IndexError) as e:
        print(f"  -> Error procesando detalle del curso {course_url}: {e}")
        return None

def scrape():
    """Scraper dinámico en dos fases para Aura Formación."""
    print(f"Iniciando scraper para {CENTRO_NOMBRE}...")
    try:
        response = requests.get(START_URL)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error al acceder a la página principal de {CENTRO_NOMBRE}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    
    links_a_visitar = []
    course_items = soup.select('div.course-item-title h3 a')
    for link in course_items:
        full_url = urljoin(BASE_URL, link['href'])
        if full_url not in links_a_visitar:
             links_a_visitar.append(full_url)
            
    if not links_a_visitar:
        print(f"No se encontraron enlaces a cursos en {CENTRO_NOMBRE}.")
        return []
        
    print(f"Descubiertos {len(links_a_visitar)} enlaces a cursos. Procediendo a filtrar y extraer detalles...")

    cursos_encontrados = []
    for link in links_a_visitar:
        curso_data = _scrape_detail_page(link)
        if curso_data:
            cursos_encontrados.append(curso_data)
            
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos de Tenerife encontrados.")
    return cursos_encontrados

if __name__ == '__main__':
    cursos = scrape()
    for c in cursos:
        print(c)