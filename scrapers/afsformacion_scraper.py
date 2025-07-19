# Contenido de scrapers/afsformacion_scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://afsformacion.com/nuestros-cursos/desempleados/tenerife/"
CENTRO_NOMBRE = "AFS Formación"

def _normalize_date(date_string):
    """Convierte una cadena de texto de mes a formato YYYY-MM-DD."""
    if "INMEDIATO" in date_string.upper():
        return "Inicio Inmediato"
        
    meses = {
        'ENERO': '01', 'FEBRERO': '02', 'MARZO': '03', 'ABRIL': '04', 'MAYO': '05', 'JUNIO': '06',
        'JULIO': '07', 'AGOSTO': '08', 'SEPTIEMBRE': '09', 'OCTUBRE': '10', 'NOVIEMBRE': '11', 'DICIEMBRE': '12'
    }
    for mes_nombre, mes_num in meses.items():
        if mes_nombre in date_string.upper():
            current_year = datetime.now().year
            return f"{current_year}-{mes_num}-01"
    return "No especificado"

def scrape():
    """Extrae los cursos de AFS Formación."""
    print(f"Iniciando scraper para {CENTRO_NOMBRE}...")
    try:
        response = requests.get(URL)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error al acceder a {URL}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    cursos_encontrados = []
    
    course_list = soup.find_all('div', class_='elementor-post')
    if not course_list:
        print(f"No se encontró la lista de cursos en {CENTRO_NOMBRE}.")
        return []

    for item in course_list:
        try:
            nombre = item.find('h2', class_='elementor-post__title').a.text.strip()
            url_curso = item.find('h2', class_='elementor-post__title').a['href']
            
            metas = item.find_all('div', class_='elementor-icon-list-item')
            
            fecha_str = "No especificado"
            horario = "No especificado"
            horas_str = "0"

            for meta in metas:
                text = meta.text.upper()
                if 'INICIO:' in text:
                    fecha_str = meta.text.replace('Inicio:', '').strip()
                elif 'HORARIO:' in text:
                    horario = meta.text.replace('Horario:', '').strip()
                elif 'DURACIÓN:' in text:
                    horas_str = meta.text.replace('Duración:', '').replace('Horas', '').strip()

            curso_data = {
                "centro": CENTRO_NOMBRE,
                "nombre": nombre,
                "url": url_curso,
                "inicio": _normalize_date(fecha_str),
                "fin": "No disponible",
                "horario": horario,
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