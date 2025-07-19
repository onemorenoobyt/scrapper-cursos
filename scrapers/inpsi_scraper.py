# Contenido de scrapers/inpsi_scraper.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import sys
sys.path.append('.')
import config

BASE_URL = "https://www.inpsi.com"
START_URL = "https://www.inpsi.com/cursos/"
CENTRO_NOMBRE = "INPSI"

def _normalize_date(date_string):
    """Convierte fechas como '01/09/2025' a 'YYYY-MM-DD'."""
    if "No especificado" in date_string:
        return date_string
    try:
        dt_object = datetime.strptime(date_string, '%d/%m/%Y')
        return dt_object.strftime('%Y-%m-%d')
    except ValueError:
        return "Formato de fecha no reconocido"

def _scrape_detail_page(course_url):
    """Función auxiliar para extraer datos de la página de detalle de un curso."""
    try:
        response = requests.get(course_url, headers=config.HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        nombre = soup.find('h1', class_='entry-title').text.strip()
        info_box = soup.find('div', class_='info-curso')
        
        sede = "No especificado"
        sede_tag = info_box.select_one('p:contains("Sede:") strong')
        if sede_tag:
             sede = sede_tag.text.strip()
        
        if "Candelaria" in sede or "Online" in sede:
            return None

        fecha_inicio_str = info_box.select_one('p:contains("Inicio:") strong').text.strip() if info_box.select_one('p:contains("Inicio:") strong') else "No especificado"
        fecha_fin_str = info_box.select_one('p:contains("Fin:") strong').text.strip() if info_box.select_one('p:contains("Fin:") strong') else "No especificado"
        horario = info_box.select_one('p:contains("Horario:") strong').text.strip() if info_box.select_one('p:contains("Horario:") strong') else "No especificado"
        
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
    """Scraper dinámico con paginación y "deep scraping" para INPSI."""
    print(f"Iniciando scraper para {CENTRO_NOMBRE}...")
    cursos_encontrados = []
    
    urls_a_visitar = [START_URL]
    urls_visitadas = set()

    while urls_a_visitar:
        current_url = urls_a_visitar.pop(0)
        if current_url in urls_visitadas:
            continue

        print(f"Procesando página de listado: {current_url}")
        try:
            response = requests.get(current_url, headers=config.HEADERS)
            response.raise_for_status()
            urls_visitadas.add(current_url)
            soup_title = BeautifulSoup(response.content, 'html.parser').title
            title_text = soup_title.string if soup_title else "No se encontró título"
            print(f"  -> Conexión exitosa. Título: {title_text}")
        except requests.RequestException as e:
            print(f"  !!! ERROR DE CONEXIÓN en {current_url}: {e}")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')
        
        course_links = [a['href'] for a in soup.select('article.curso h2.entry-title a')]
        
        for link in course_links:
            curso_data = _scrape_detail_page(link)
            if curso_data:
                cursos_encontrados.append(curso_data)

        next_page_link = soup.select_one('a.next.page-numbers')
        if next_page_link and next_page_link['href'] not in urls_visitadas:
            urls_a_visitar.append(next_page_link['href'])
            
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados

if __name__ == '__main__':
    cursos = scrape()
    for c in cursos:
        print(c)