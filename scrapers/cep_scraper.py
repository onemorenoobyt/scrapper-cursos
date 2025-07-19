# Contenido de scrapers/cep_scraper.py (CORREGIDO)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
from urllib.parse import urljoin
import sys
import time
sys.path.append('.')
import config

BASE_URL = "https://cursostenerife.es/"
CENTRO_NOMBRE = "CEP"

def _normalize_date(date_string):
    meses = {'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04', 'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08', 'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'}
    try:
        parts = date_string.lower().split(' de ')
        day = int(parts[0])
        month = meses[parts[1]]
        year = int(parts[2])
        return f"{year}-{month}-{day:02d}"
    except (ValueError, IndexError, KeyError):
        return "Formato de fecha no reconocido"

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
        driver.get(BASE_URL)
        print(f"  -> Página principal de {CENTRO_NOMBRE} cargada.")

        # --- ¡CAMBIO CLAVE! Aceptar cookies ---
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CLASS_NAME, "cookie_action_close_header"))).click()
            print("  -> Banner de cookies aceptado.")
            time.sleep(2)
        except Exception:
            print("  -> No se encontró banner de cookies o no fue necesario.")

        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.TAG_NAME, "table")))
        print(f"  -> Contenedor de cursos encontrado y visible en {CENTRO_NOMBRE}.")
        
        tabla = driver.find_element(By.TAG_NAME, 'table')
        rows = tabla.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')
        if not rows:
            print(f"  !!! ERROR: No se encontraron filas en la tabla de cursos de {CENTRO_NOMBRE}.")
        
        for row in rows:
            try:
                cols = row.find_elements(By.TAG_NAME, 'td')
                if len(cols) < 6: continue
                
                sede = cols[5].text.strip()
                if "SANTA CRUZ" not in sede.upper(): continue
                
                fecha_inicio_str = cols[0].text.strip()
                nombre = cols[1].text.strip()
                url_curso = urljoin(BASE_URL, cols[1].find_element(By.TAG_NAME, 'a').get_attribute('href'))
                horas_str = cols[2].text.strip()
                horario = cols[4].text.strip()
                
                curso_data = {"centro": CENTRO_NOMBRE, "nombre": nombre, "url": url_curso, "inicio": _normalize_date(fecha_inicio_str), "fin": "No disponible en listado", "horario": horario, "horas": int(horas_str) if horas_str.isdigit() else 0}
                cursos_encontrados.append(curso_data)
            except Exception as e:
                print(f"  -> Error al procesar una fila de {CENTRO_NOMBRE}: {e}")
                continue
    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
    finally:
        driver.quit()
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados