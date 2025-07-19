# Contenido de scrapers/formacionline_scraper.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

BASE_URL = "https://formacionline.com"
START_URL = "https://formacionline.com/formacion/cursos/"
CENTRO_NOMBRE = "FormacionLine"

def _normalize_date(date_string):
    """Convierte fechas como '07/07/2025' a 'YYYY-MM-DD'."""
    if "Próximamente" in date_string or not date_string:
        return "Próximamente"
    try:
        dt_object = datetime.strptime(date_string, '%d/%m/%Y')
        return dt_object.strftime('%Y-%m-%d')
    except ValueError:
        return "Formato de fecha no reconocido"

def _scrape_detail_page(course_url):
    """Función auxiliar para extraer datos de la página de detalle de un curso."""
    try:
        response = requests.get(course_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        nombre = soup.find('h1', class_='course-title').text.strip()
        
        horas_tag = soup.select_one('ul.course-features span.feature-text:contains("horas")')
        horas = horas_tag.text.replace('horas', '').strip() if horas_tag else "0"
        
        fecha_inicio = "No especificado"
        fecha_fin = "No especificado"
        horario = "No especificado"
        
        details_section = soup.find('div', id='tab-course-curriculum')
        if details_section:
            strong_tags = details_section.find_all('strong')
            for tag in strong_tags:
                # El texto que buscamos está después de la etiqueta <strong>, como un nodo de texto.
                next_sibling_text = tag.next_sibling.strip() if tag.next_sibling and isinstance(tag.next_sibling, str) else ""
                
                if "Fecha de inicio:" in tag.text:
                    fecha_inicio = next_sibling_text
                elif "Fecha de fin:" in tag.text:
                    fecha_fin = next_sibling_text
                elif "Horario:" in tag.text:
                    horario = next_sibling_text

        return {
            "centro": CENTRO_NOMBRE,
            "nombre": nombre,
            "url": course_url,
            "inicio": _normalize_date(fecha_inicio),
            "fin": _normalize_date(fecha_fin),
            "horario": horario,
            "horas": int(horas) if horas.isdigit() else 0
        }
    except (requests.RequestException, AttributeError, IndexError) as e:
        print(f"  -> Error al procesar detalle del curso {course_url}: {e}")
        return None

def scrape():
    """Scraper dinámico en dos fases para FormacionLine."""
    print(f"Iniciando scraper para {CENTRO_NOMBRE}...")
    try:
        response = requests.get(START_URL)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error al acceder a la página principal de {CENTRO_NOMBRE}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    
    links_a_visitar = []
    course_items = soup.find_all('div', class_='course-item')
    
    for item in course_items:
        try:
            location_tag = item.find('div', class_='meta-item-location')
            if location_tag and "Santa Cruz de Tenerife" in location_tag.text:
                link = item.find('a')['href']
                full_url = urljoin(BASE_URL, link)
                links_a_visitar.append(full_url)
        except (AttributeError, IndexError):
            continue
            
    if not links_a_visitar:
        print(f"No se encontraron cursos para Santa Cruz en {CENTRO_NOMBRE}.")
        return []
        
    print(f"Descubiertos {len(links_a_visitar)} cursos en Santa Cruz. Procediendo a extraer detalles...")

    cursos_encontrados = []
    for link in links_a_visitar:
        curso_data = _scrape_detail_page(link)
        if curso_data:
            cursos_encontrados.append(curso_data)
            
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos procesados.")
    return cursos_encontrados

if __name__ == '__main__':
    cursos = scrape()
    for c in cursos:
        print(c)