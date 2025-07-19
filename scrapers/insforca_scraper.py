# Contenido de scrapers/insforca_scraper.py (VERSIÓN FINAL - MIGRADO A SELENIUM)
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
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f"user-agent={config.HEADERS['User-Agent']}")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    cursos_encontrados = []
    
    try:
        driver.get(URL)
        print(f"  -> Página principal de {CENTRO_NOMBRE} cargada.")

        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "item-curso-desempleados")))
        print(f"  -> Contenedor de cursos encontrado en {CENTRO_NOMBRE}.")
        course_list = driver.find_elements(By.CLASS_NAME, 'item-curso-desempleados')
        
        if not course_list:
            print(f"  !!! ADVERTENCIA: No se encontró la lista de cursos en {CENTRO_NOMBRE}.")
            return []

        for item in course_list:
            try:
                participantes_tag = item.find_element(By.CLASS_NAME, 'participantes-curso')
                if "Tenerife" not in participantes_tag.text:
                    continue

                inicio_tag = item.find_element(By.CLASS_NAME, 'inicio-curso')
                if not inicio_tag or "INICIO:" not in inicio_tag.text.upper():
                    continue

                nombre = item.find_element(By.TAG_NAME, 'h2').text.strip()
                
                fechas_str = inicio_tag.text.strip()
                parts = fechas_str.split('|')
                fecha_inicio_str = parts[0].replace('INICIO:', '').strip()
                fecha_fin_str = parts[1].replace('FIN:', '').strip()

                horas_tag = item.find_element(By.CLASS_NAME, 'duracion-curso')
                horas_str = ''.join(filter(str.isdigit, horas_tag.text))

                curso_data = {
                    "centro": CENTRO_NOMBRE, "nombre": nombre, "url": f"{URL}#{nombre.replace(' ', '-')}",
                    "inicio": _normalize_date(fecha_inicio_str), "fin": _normalize_date(fecha_fin_str),
                    "horario": "No disponible en listado", "horas": int(horas_str) if horas_str.isdigit() else 0
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