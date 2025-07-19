# Contenido de scrapers/focan_scraper.py (CORREGIDO)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time

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
    options.add_argument('--ignore-certificate-errors')
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    cursos_encontrados = []
    
    try:
        driver.get(URL)
        
        # --- ¡CAMBIO CLAVE! Aceptar cookies ---
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "cookie_action_close_header"))).click()
            print("  -> Banner de cookies aceptado.")
            time.sleep(2)
        except Exception:
            print("  -> No se encontró banner de cookies o no fue necesario.")
            
        # --- ¡CAMBIO CLAVE! Selector de espera actualizado ---
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "result-item")))
        print(f"  -> Conexión exitosa y contenido cargado en {CENTRO_NOMBRE}.")

        # --- ¡CAMBIO CLAVE! Selector de lista actualizado ---
        course_items = driver.find_elements(By.CLASS_NAME, 'result-item')
        
        if not course_items:
            print(f"  !!! ERROR: No se encontraron cursos en {CENTRO_NOMBRE}.")

        for item in course_items:
            try:
                # --- ¡CAMBIO CLAVE! Selectores internos actualizados ---
                nombre = item.find_element(By.TAG_NAME, 'h3').text.strip()
                url_curso = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
                
                # La información ahora está en párrafos dentro de un div.info
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