# scrapers/focan_scraper.py
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

URL = "https://focan.es/resultados-busqueda/?sede=Tenerife&colectivo=Desempleados&modalidad=&categoria_comercial=&buscar="
CENTRO_NOMBRE = "Focan"

def _normalize_date(date_string):
    try:
        dt_object = datetime.strptime(date_string, '%d/%m/%Y')
        return dt_object.strftime('%Y-%m-%d')
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
            cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "cookie_action_close_header")))
            driver.execute_script("arguments[0].click();", cookie_button)
            print("  -> Banner de cookies aceptado.")
            time.sleep(2)
        except Exception:
            print("  -> No se encontró o no fue necesario hacer clic en el banner de cookies.")
            
        driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(2)
        
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "result-item")))
        print(f"  -> Contenido cargado en {CENTRO_NOMBRE}.")

        course_items = driver.find_elements(By.CLASS_NAME, 'result-item')
        
        if not course_items:
            print(f"  !!! ADVERTENCIA: No se encontraron cursos en {CENTRO_NOMBRE}.")

        for item in course_items:
            try:
                nombre_elements = item.find_elements(By.TAG_NAME, 'h3')
                if not nombre_elements:
                    continue 
                
                nombre = nombre_elements[0].text.strip()
                url_curso = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
                
                info_div = item.find_element(By.CLASS_NAME, 'info')
                info_p = info_div.find_elements(By.TAG_NAME, 'p')
                
                fecha_inicio_str = "No especificado"
                horario = "No especificado"
                
                for p in info_p:
                    text = p.text
                    if "Fecha de Inicio:" in text:
                        fecha_inicio_str = text.replace('Fecha de Inicio:', '').strip()
                    elif "Horario:" in text:
                        horario = text.replace('Horario:', '').strip()
                
                curso_data = { "centro": CENTRO_NOMBRE, "nombre": nombre, "url": url_curso, "inicio": _normalize_date(fecha_inicio_str), "fin": "No disponible en listado", "horario": horario, "horas": 0 }
                cursos_encontrados.append(curso_data)
            except Exception as e:
                print(f"  -> Error al procesar un curso de {CENTRO_NOMBRE}: {e}")
                continue
    
    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
        driver.save_screenshot(f"debug_screenshot_{CENTRO_NOMBRE.lower().replace(' ', '')}.png")
    finally:
        driver.quit()
        
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados