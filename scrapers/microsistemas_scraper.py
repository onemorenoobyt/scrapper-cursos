# Contenido de scrapers/microsistemas_scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://microsistemas.es/cursos-gratis-tenerife/"
CENTRO_NOMBRE = "MicroSistemas"

def _normalize_date(date_string):
    """Convierte fechas como '07/07/2025' a 'YYYY-MM-DD'."""
    if "No especificado" in date_string:
        return date_string
    try:
        dt_object = datetime.strptime(date_string, '%d/%m/%Y')
        return dt_object.strftime('%Y-%m-%d')
    except ValueError:
        return "Formato de fecha no reconocido"

def scrape():
    """Extrae los cursos de MicroSistemas."""
    print(f"Iniciando scraper para {CENTRO_NOMBRE}...")
    try:
        response = requests.get(URL)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error al acceder a {URL}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    cursos_encontrados = []
    
    course_list = soup.find_all('article', class_='elementor-post')
    if not course_list:
        print(f"No se encontró la lista de cursos en {CENTRO_NOMBRE}.")
        return []

    for item in course_list:
        try:
            nombre = item.find('h3', class_='elementor-post__title').a.text.strip()
            url_curso = item.find('h3', class_='elementor-post__title').a['href']
            
            meta_data = item.find('div', class_='elementor-post__meta-data').text
            
            fecha_inicio_str = "No especificado"
            fecha_fin_str = "No especificado"
            horario = "No especificado"

            if "Inicio:" in meta_data and "Fin:" in meta_data:
                fechas_part = meta_data.split(' - Fin: ')
                inicio_part = fechas_part[0].replace('Inicio:', '').strip()
                
                # Dividimos la segunda parte para separar fecha de fin y horario
                fin_horario_parts = fechas_part[1].split('Horario:')
                fecha_inicio_str = inicio_part
                fecha_fin_str = fin_horario_parts[0].strip()
                if len(fin_horario_parts) > 1:
                    horario = fin_horario_parts[1].strip()

            elif "Horario:" in meta_data: # Para los cursos que solo tienen horario
                 horario = meta_data.split('Horario:')[1].strip()

            curso_data = {
                "centro": CENTRO_NOMBRE,
                "nombre": nombre,
                "url": url_curso,
                "inicio": _normalize_date(fecha_inicio_str),
                "fin": _normalize_date(fecha_fin_str),
                "horario": horario,
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