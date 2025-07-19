# Contenido de scrapers/focan_scraper.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

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
    print(f"Iniciando scraper para {CENTRO_NOMBRE} con Selenium...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Añadimos una opción para ignorar los errores de certificado SSL
    options.add_argument('--ignore-certificate-errors')
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    cursos_encontrados = []
    
    try:
        driver.get(URL)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "module-content")))
        print(f"  -> Conexión exitosa y contenido cargado en {CENTRO_NOMBRE}.")

        course_list_container = driver.find_element(By.CLASS_NAME, 'module-content')
        course_items = course_list_container.find_elements(By.CLASS_NAME, 'item')
        
        if not course_items:
            print(f"  !!! ERROR: No se encontraron cursos en {CENTRO_NOMBRE}.")

        for item in course_items:
            try:
                nombre = item.find_element(By.TAG_NAME, 'h2').text.strip()
                url_curso = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
                
                info_p = item.find_elements(By.TAG_NAME, 'p')
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
    import pandas as pd
    df = pd.DataFrame(cursos)
    print(df)