# Contenido de scrapers/icse_scraper.py (CORREGIDO)
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys
sys.path.append('.')
import config

URL = "https://www.icse.es/cursos?type=2&island=Tenerife"
CENTRO_NOMBRE = "ICSE"

def _normalize_date(date_string):
    """Convierte fechas como '13/10/2025' a 'YYYY-MM-DD'."""
    try:
        # La web ahora puede no tener fecha de fin, así que solo tomamos la primera
        dt_object = datetime.strptime(date_string.split(' - ')[0].strip(), '%d/%m/%Y')
        return dt_object.strftime('%Y-%m-%d')
    except (ValueError, IndexError):
        return "Formato de fecha no reconocido"

def scrape():
    """Extrae los cursos de ICSE filtrando por Santa Cruz."""
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
    
    # --- ¡CAMBIO CLAVE! El selector de la lista de cursos ahora es 'course-item-wrapper' ---
    course_list = soup.find_all('div', class_='course-item-wrapper')
    if not course_list:
        print(f"  !!! ERROR: No se encontró la lista de cursos en {CENTRO_NOMBRE} con el nuevo selector.")
        return []

    for item in course_list:
        try:
            # El filtro de sede sigue siendo válido, pero nos aseguramos de que la etiqueta exista
            sede_tag = item.find('li', class_='course-locality')
            if sede_tag and "STA. CRUZ DE TENERIFE" in sede_tag.text.upper():
                
                # --- ¡CAMBIO CLAVE! Selectores internos actualizados ---
                title_anchor = item.find('h3', class_='course-title').find('a')
                nombre = title_anchor.text.strip()
                url_curso = title_anchor['href']
                
                # --- ¡CAMBIO CLAVE! La clase para la fecha ahora es 'course-date' ---
                fechas_tag = item.find('span', class_='course-date')
                fechas_str = fechas_tag.text.strip() if fechas_tag else "No especificado"

                # La web ahora no siempre muestra fecha de fin en la lista
                fechas_parts = [d.strip() for d in fechas_str.split(' - ')]
                fecha_inicio_str = fechas_parts[0]
                fecha_fin_str = fechas_parts[1] if len(fechas_parts) > 1 else "No disponible"

                curso_data = {
                    "centro": CENTRO_NOMBRE,
                    "nombre": nombre,
                    "url": url_curso,
                    "inicio": _normalize_date(fecha_inicio_str),
                    "fin": _normalize_date(fecha_fin_str),
                    "horario": "No disponible en listado",
                    "horas": 0
                }
                cursos_encontrados.append(curso_data)
        except Exception as e:
            # Añadimos un print en el error para saber qué curso falló
            print(f"  -> Error al procesar un curso de {CENTRO_NOMBRE}: {e}")
            continue
            
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados

if __name__ == '__main__':
    cursos = scrape()
    import pandas as pd
    df = pd.DataFrame(cursos)
    print(df)