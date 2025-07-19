# Contenido de scrapers/grupolincea_scraper.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import sys
import time
sys.path.append('.')
import config

START_URL = "https://grupolincea.es/cursos-tenerife-2/"
CENTRO_NOMBRE = "Grupo Lincea"

def _normalize_date(date_string):
    if "No especificado" in date_string: return date_string
    try:
        dt_object = datetime.strptime(date_string, '%d/%m/%y')
        return dt_object.strftime('%Y-%m-%d')
    except ValueError:
        return "Formato de fecha no reconocido"

def _scrape_detail_page(driver, course_url):
    try:
        driver.get(course_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'FECHA DE INICIO')]")))
        fecha_label = driver.find_element(By.XPATH, "//*[contains(text(), 'FECHA DE INICIO')]")
        if not fecha_label: return None
        fecha_data_tag = fecha_label.find_element(By.XPATH, "./following-sibling::h2")
        if not fecha_data_tag or not fecha_data_tag.text.strip(): return None
        nombre = driver.find_element(By.TAG_NAME, 'h1').text.strip()
        fechas_str = fecha_data_tag.text.strip()
        if '–' in fechas_str:
            fecha_inicio_str, fecha_fin_str = [d.strip() for d in fechas_str.split('–')]
        else:
            fecha_inicio_str, fecha_fin_str = fechas_str, "No especificado"
        horario = "No especificado"
        try:
            horario_label = driver.find_element(By.XPATH, "//*[contains(text(), 'HORARIO')]")
            horario_data_tag = horario_label.find_element(By.XPATH, "./following-sibling::h2")
            if horario_data_tag: horario = horario_data_tag.text.strip()
        except:
            pass # Si no hay horario, no es un error crítico
        return {"centro": CENTRO_NOMBRE, "nombre": nombre, "url": course_url, "inicio": _normalize_date(fecha_inicio_str), "fin": _normalize_date(fecha_fin_str), "horario": horario, "horas": 0}
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
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.cmplz-accept"))).click()
            print("  -> Banner de cookies aceptado.")
            time.sleep(2)
        except Exception:
            print("  -> No se encontró banner de cookies o no fue necesario.")
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.elementor-post__card a")))
        print(f"  -> Contenedor de cursos encontrado y visible en {CENTRO_NOMBRE}.")
        course_items = driver.find_elements(By.CSS_SELECTOR, 'div.elementor-post__card a')
        links_a_visitar = [item.get_attribute('href') for item in course_items]
        if not links_a_visitar:
            print(f"No se encontraron enlaces a cursos en {CENTRO_NOMBRE}.")
        else:
            print(f"Descubiertos {len(links_a_visitar)} enlaces a cursos. Procediendo a extraer detalles...")
            unique_links = sorted(list(set(links_a_visitar))) # Evitamos duplicados
            for link in unique_links:
                curso_data = _scrape_detail_page(driver, link)
                if curso_data:
                    cursos_encontrados.append(curso_data)
    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
    finally:
        driver.quit()
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos con fecha encontrados.")
    return cursos_encontrados

if __name__ == '__main__':
    cursos = scrape()
    import pandas as pd
    df = pd.DataFrame(cursos)
    print(df)