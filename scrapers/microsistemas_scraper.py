# Contenido de scrapers/microsistemas_scraper.py (VERSIÓN FINAL - MIGRADO A SELENIUM)
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

URL = "https://microsistemas.es/cursos-gratis-tenerife/"
CENTRO_NOMBRE = "MicroSistemas"

def _normalize_date(date_string):
    if "No especificado" in date_string: return date_string
    try:
        return datetime.strptime(date_string, '%d/%m/%Y').strftime('%Y-%m-%d')
    except ValueError:
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
        driver.get(URL)
        print(f"  -> Página principal de {CENTRO_NOMBRE} cargada.")

        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "article.elementor-post")))
        print(f"  -> Contenedor de cursos encontrado en {CENTRO_NOMBRE}.")
        course_list = driver.find_elements(By.CSS_SELECTOR, 'article.elementor-post')
        
        if not course_list:
            print(f"  !!! ADVERTENCIA: No se encontró la lista de cursos en {CENTRO_NOMBRE}.")
            return []

        for item in course_list:
            try:
                nombre = item.find_element(By.CSS_SELECTOR, 'h3.elementor-post__title a').text.strip()
                url_curso = item.find_element(By.CSS_SELECTOR, 'h3.elementor-post__title a').get_attribute('href')
                
                meta_data_div = item.find_element(By.CLASS_NAME, 'elementor-post__meta-data')
                meta_data = meta_data_div.text
                
                fecha_inicio_str, fecha_fin_str, horario = "No especificado", "No especificado", "No especificado"

                parts = [p.strip() for p in meta_data.split(' - ')]
                for part in parts:
                    if part.startswith("Inicio:"): fecha_inicio_str = part.replace("Inicio:", "").strip()
                    elif part.startswith("Fin:"): fecha_fin_str = part.replace("Fin:", "").strip()
                    elif part.startswith("Horario:"): horario = part.replace("Horario:", "").strip()

                curso_data = {
                    "centro": CENTRO_NOMBRE, "nombre": nombre, "url": url_curso,
                    "inicio": _normalize_date(fecha_inicio_str), "fin": _normalize_date(fecha_fin_str),
                    "horario": horario, "horas": 0
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