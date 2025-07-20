# Contenido de scrapers/focan_scraper.py (VERSIÓN FINAL CORREGIDA Y ROBUSTA)
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

URL = "https://focan.es/resultados-busqueda/?sede=Tenerife&colectivo=Desempleados&modalidad=&categoria_comercial=&buscar="
CENTRO_NOMBRE = "Focan"

def _normalize_date(date_string):
    """Convierte una cadena de fecha dd/mm/yyyy a YYYY-MM-DD."""
    try:
        return datetime.strptime(date_string.strip(), '%d/%m/%Y').strftime('%Y-%m-%d')
    except (ValueError, IndexError):
        return "No disponible"

def scrape():
    """Scraper robusto para Focan que extrae datos de la estructura HTML real."""
    print(f"Iniciando scraper para {CENTRO_NOMBRE} con Selenium...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    cursos_encontrados = []
    
    try:
        driver.get(URL)
        print(f"  -> Página principal de {CENTRO_NOMBRE} cargada.")
        
        try:
            cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "cookie_action_close_header")))
            driver.execute_script("arguments[0].click();", cookie_button)
            print("  -> Banner de cookies aceptado.")
        except Exception:
            print("  -> No se encontró el banner de cookies.")
            
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CLASS_NAME, "result-item")))
        print(f"  -> Contenido dinámico cargado en {CENTRO_NOMBRE}.")

        course_items = driver.find_elements(By.CLASS_NAME, 'result-item')
        
        for item in course_items:
            try:
                # CORRECCIÓN DEFINITIVA: El título está dentro de la imagen, en el atributo 'alt'
                title_element = item.find_element(By.CLASS_NAME, 'result-image')
                nombre = title_element.get_attribute('alt').replace('Imagen del curso', '').strip()
                url_curso = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
                
                # Extracción robusta de los datos del 'result-info'
                info_div = item.find_element(By.CLASS_NAME, 'result-info')
                info_text = info_div.text
                
                fecha_inicio, fecha_fin, horario = "No disponible", "No disponible", "No disponible"
                
                lines = info_text.split('\n')
                for line in lines:
                    if "Inicio:" in line:
                        fecha_inicio = line.split(':')[1].strip()
                    elif "Fin:" in line:
                        fecha_fin = line.split(':')[1].strip()
                    elif "Horario:" in line:
                        horario = line.split(':')[1].strip()

                curso_data = {
                    "centro": CENTRO_NOMBRE,
                    "nombre": nombre,
                    "url": url_curso,
                    "inicio": _normalize_date(fecha_inicio),
                    "fin": _normalize_date(fecha_fin),
                    "horario": horario,
                    "horas": 0
                }
                cursos_encontrados.append(curso_data)
            except Exception as e:
                print(f"  -> ADVERTENCIA: Error procesando un curso de Focan. Saltando. Razón: {e}")
                continue
    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
        driver.save_screenshot(f"debug_screenshot_{CENTRO_NOMBRE.lower().replace(' ', '')}.png")
    finally:
        driver.quit()
        
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados

if __name__ == '__main__':
    cursos = scrape()
    print(cursos)