# scrapers/insforca_scraper.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
import sys
sys.path.append('.')
import config

URL = "https://www.insforca.com/formacion/cursos-gratuitos-prioritariamente-para-desempleados-as/"
CENTRO_NOMBRE = "Insforca"

def _normalize_date(date_string):
    try:
        return datetime.strptime(date_string, '%d/%m/%Y').strftime('%Y-%m-%d')
    except ValueError:
        return "Formato de fecha no reconocido"

def scrape():
    print(f"Iniciando scraper para {CENTRO_NOMBRE} con Selenium...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f"user-agent={config.HEADERS['User-Agent']}")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    cursos_encontrados = []
    
    try:
        driver.get(URL)
        print(f"  -> Página principal de {CENTRO_NOMBRE} cargada.")

        try:
            cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "cky-btn-accept")))
            driver.execute_script("arguments[0].click();", cookie_button)
            print("  -> Banner de cookies aceptado.")
            time.sleep(2)
        except Exception:
            print("  -> No se encontró el banner de cookies.")
        
        try:
            tenerife_tab = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(b, 'TENERIFE')]")))
            driver.execute_script("arguments[0].click();", tenerife_tab)
            print("  -> Clic en la pestaña de 'TENERIFE' realizado.")
            time.sleep(3)
        except Exception as e:
            print(f"  -> No se pudo hacer clic en la pestaña de Tenerife o ya estaba activa.")

        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[data-title*='TENERIFE'] .tlp-portfolio-item")))
        print(f"  -> Contenido de la pestaña de Tenerife cargado y visible.")
        
        course_list = driver.find_elements(By.CSS_SELECTOR, "div[data-title*='TENERIFE'] .tlp-portfolio-item")
        print(f"  -> Encontrados {len(course_list)} cursos en la pestaña de Tenerife.")
        
        for item in course_list:
            try:
                inicio_tag_text = item.find_element(By.CLASS_NAME, 'tlp-portfolio-sd').text
                if "INICIO:" not in inicio_tag_text.upper():
                    continue

                nombre = item.find_element(By.TAG_NAME, 'h3').text.strip()
                url_curso = item.find_element(By.TAG_NAME, 'a').get_attribute('href')

                fechas_str, horas_str = "", "0"
                for line in inicio_tag_text.split('\n'):
                    if "INICIO:" in line.upper(): fechas_str = line
                    elif "DURACIÓN:" in line.upper(): horas_str = ''.join(filter(str.isdigit, line))

                parts = fechas_str.split('|')
                fecha_inicio_str = parts[0].replace('INICIO:', '').strip()
                fecha_fin_str = parts[1].replace('FIN:', '').strip()

                curso_data = { "centro": CENTRO_NOMBRE, "nombre": nombre, "url": url_curso, "inicio": _normalize_date(fecha_inicio_str), "fin": _normalize_date(fecha_fin_str), "horario": "No disponible en listado", "horas": int(horas_str) if horas_str.isdigit() else 0 }
                cursos_encontrados.append(curso_data)
            except Exception:
                continue
    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
    finally:
        driver.quit()
        
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados