# Contenido de scrapers/afsformacion_scraper.py (VERSIÓN 2 - CORREGIDA)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

URL = "https://afsformacion.com/nuestros-cursos/desempleados/tenerife/"
CENTRO_NOMBRE = "AFS Formación"

def _normalize_date(date_string):
    """Convierte una cadena de texto de mes a formato YYYY-MM-DD."""
    if "INMEDIATO" in date_string.upper():
        return "Inicio Inmediato"
    meses = {'ENERO': '01', 'FEBRERO': '02', 'MARZO': '03', 'ABRIL': '04', 'MAYO': '05', 'JUNIO': '06', 'JULIO': '07', 'AGOSTO': '08', 'SEPTIEMBRE': '09', 'OCTUBRE': '10', 'NOVIEMBRE': '11', 'DICIEMBRE': '12'}
    for mes_nombre, mes_num in meses.items():
        if mes_nombre in date_string.upper():
            # Asumimos que los cursos son para el próximo año si el mes ya pasó
            current_month = datetime.now().month
            current_year = datetime.now().year
            year = current_year if int(mes_num) >= current_month else current_year + 1
            return f"{year}-{mes_num}-01"
    return "No especificado"

def scrape():
    print(f"Iniciando scraper para {CENTRO_NOMBRE} con Selenium...")
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    
    cursos_encontrados = []
    try:
        driver.get(URL)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "elementor-post"))
        )
        print(f"  -> Conexión exitosa y contenido cargado en {CENTRO_NOMBRE}.")

        course_list = driver.find_elements(By.CLASS_NAME, "elementor-post")
        if not course_list:
            print(f"  !!! ERROR: No se encontró la lista de cursos en {CENTRO_NOMBRE} incluso con Selenium.")
            driver.quit()
            return []

        for item in course_list:
            try:
                nombre = item.find_element(By.CLASS_NAME, "elementor-post__title").text.strip()
                url_curso = item.find_element(By.TAG_NAME, "a").get_attribute('href')
                
                # --- LÓGICA DE EXTRACCIÓN CORREGIDA ---
                # 1. Encontramos el bloque de metadatos completo
                meta_data_element = item.find_element(By.CLASS_NAME, 'elementor-post__meta-data')
                
                # 2. Obtenemos todo el texto y lo separamos por líneas
                lines = meta_data_element.text.split('\n')
                
                # 3. Extraemos cada dato buscando en las líneas
                fecha_str = "No especificado"
                horario = "No especificado"
                horas_str = "0"

                for line in lines:
                    if line.upper().startswith('INICIO:'):
                        fecha_str = line.replace('Inicio:', '').strip()
                    elif line.upper().startswith('HORARIO:'):
                        horario = line.replace('Horario:', '').strip()
                    elif line.upper().startswith('DURACIÓN:'):
                        horas_str = line.replace('Duración:', '').replace('Horas', '').strip()
                # --- FIN DE LA LÓGICA CORREGIDA ---

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
            except Exception as e:
                print(f"  -> Error al procesar un curso de {CENTRO_NOMBRE}: {e}")
                continue
    
    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
    finally:
        driver.quit()
        
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados

if __name__ == '__main__':
    cursos = scrape()
    # Para una mejor visualización de la prueba
    import pandas as pd
    df = pd.DataFrame(cursos)
    print(df)