# Contenido de scrapers/auraformacion_scraper.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import sys
sys.path.append('.')
import config

BASE_URL = "https://www.auraformacion.es"
START_URL = "https://www.auraformacion.es/formacion.html"
CENTRO_NOMBRE = "Aura Formación"

def _normalize_date(date_string):
    if "No especificado" in date_string: return date_string
    meses = {'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04', 'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08', 'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'}
    try:
        parts = date_string.lower().split(' de ')
        day = int(parts[0])
        month = meses[parts[1]]
        year = int(parts[2])
        return f"{year}-{month}-{day:02d}"
    except (ValueError, IndexError, KeyError):
        return "Formato de fecha no reconocido"

def _scrape_detail_page(driver, course_url):
    try:
        driver.get(course_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        center_info = driver.find_elements(By.CLASS_NAME, 'course-center-info')
        if not any("TF" in info.text for info in center_info):
            return None
        nombre = driver.find_element(By.TAG_NAME, 'h1').text.strip()
        features = driver.find_element(By.CLASS_NAME, 'course-features')
        fecha_inicio, fecha_fin, horas, horario = "No especificado", "No especificado", "0", "No especificado"
        items = features.find_elements(By.TAG_NAME, 'li')
        for item in items:
            text = item.text
            if "Fecha inicio:" in text: fecha_inicio = text.replace("Fecha inicio:", "").strip()
            elif "Fecha fin:" in text: fecha_fin = text.replace("Fecha fin:", "").strip()
            elif "Horas totales:" in text: horas = text.replace("Horas totales:", "").replace("horas.", "").strip()
            elif "Horario:" in text: horario = text.replace("Horario:", "").strip()
        return {"centro": CENTRO_NOMBRE, "nombre": nombre, "url": course_url, "inicio": _normalize_date(fecha_inicio), "fin": _normalize_date(fecha_fin), "horario": horario, "horas": int(horas) if horas.isdigit() else 0}
    except Exception as e:
        print(f"  -> Error procesando detalle del curso {course_url}: {e}")
        return None

def scrape():
    print(f"Iniciando scraper para {CENTRO_NOMBRE} con Selenium...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f"user-agent={config.HEADERS['User-Agent']}")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    cursos_encontrados = []
    try:
        driver.get(START_URL)
        print(f"  -> Página principal de {CENTRO_NOMBRE} cargada.")
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.course-item-title h3 a")))
        print(f"  -> Contenedor de cursos encontrado y visible en {CENTRO_NOMBRE}.")
        course_items = driver.find_elements(By.CSS_SELECTOR, 'div.course-item-title h3 a')
        links_a_visitar = [item.get_attribute('href') for item in course_items]
        if not links_a_visitar:
            print(f"No se encontraron enlaces a cursos en {CENTRO_NOMBRE}.")
        else:
            print(f"Descubiertos {len(links_a_visitar)} enlaces a cursos. Procediendo a filtrar y extraer detalles...")
            for link in links_a_visitar:
                curso_data = _scrape_detail_page(driver, link)
                if curso_data:
                    cursos_encontrados.append(curso_data)
    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
    finally:
        driver.quit()
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos de Tenerife encontrados.")
    return cursos_encontrados

if __name__ == '__main__':
    cursos = scrape()
    import pandas as pd
    df = pd.DataFrame(cursos)
    print(df)