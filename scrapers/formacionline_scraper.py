# scrapers/formacionline_scraper.py (VERSIÓN FINAL Y DEFINITIVA v2)
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

START_URL = "https://formacionline.com/formacion/cursos/"
CENTRO_NOMBRE = "FormacionLine"

def _normalize_date(date_string):
    if "Próximamente" in date_string or not date_string or date_string.isspace():
        return "Próximamente"
    try:
        cleaned_date = date_string.split(' ')[0]
        dt_object = datetime.strptime(cleaned_date, '%d/%m/%Y')
        return dt_object.strftime('%Y-%m-%d')
    except (ValueError, IndexError):
        return "Formato de fecha no reconocido"

def _scrape_detail_page(driver, course_url, course_title_from_list):
    try:
        driver.get(course_url)
        
        # Esperamos a que el título de la pestaña del navegador contenga el nombre del curso.
        WebDriverWait(driver, 20).until(
            EC.title_contains(course_title_from_list.split(' ')[0])
        )

        # --- ¡LA CORRECCIÓN MÁGICA ESTÁ AQUÍ! ---
        # 1. Esperamos por el contenedor correcto: .custom-content
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "custom-content"))
        )
        details_container = driver.find_element(By.CLASS_NAME, "custom-content")

        # 2. Buscamos los datos de una forma más estructurada
        nombre = course_title_from_list # Usamos el que ya tenemos, es más fiable
        horas = "0"
        fecha_inicio = "No especificado"
        fecha_fin = "No especificado"
        horario = "No especificado"
        
        # Buscamos cada campo por el texto de su etiqueta <strong>
        try:
            horas_element = details_container.find_element(By.XPATH, ".//strong[contains(text(), 'Horas')]/parent::div/following-sibling::div")
            horas = horas_element.text.strip()
        except: pass
        
        try:
            inicio_element = details_container.find_element(By.XPATH, ".//strong[contains(text(), 'Fecha de inicio')]/parent::div/following-sibling::div")
            fecha_inicio = inicio_element.text.strip()
        except: pass
            
        try:
            fin_element = details_container.find_element(By.XPATH, ".//strong[contains(text(), 'Fecha de finalización')]/parent::div/following-sibling::div")
            fecha_fin = fin_element.text.strip()
        except: pass
        
        try:
            horario_element = details_container.find_element(By.XPATH, ".//strong[contains(text(), 'Horario')]/parent::div/following-sibling::div")
            horario = horario_element.text.strip()
        except: pass

        return {
            "centro": CENTRO_NOMBRE,
            "nombre": nombre,
            "url": course_url,
            "inicio": _normalize_date(fecha_inicio),
            "fin": _normalize_date(fecha_fin),
            "horario": horario,
            "horas": int(''.join(filter(str.isdigit, horas))) if horas else 0
        }
    except Exception as e:
        print(f"  -> Error procesando detalle del curso {course_url}: {e}")
        driver.save_screenshot(f"debug_detail_page_{course_title_from_list[:10]}.png")
        return None

def scrape():
    print(f"Iniciando scraper para {CENTRO_NOMBRE} con Selenium...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f"user-agent={config.HEADERS['User-Agent']}")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    cursos_encontrados = []
    
    try:
        driver.get(START_URL)
        print(f"  -> Página principal de {CENTRO_NOMBRE} cargada.")

        try:
            cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "cmplz-accept")))
            driver.execute_script("arguments[0].click();", cookie_button)
            print("  -> Banner de cookies aceptado.")
            time.sleep(2)
        except Exception:
            print("  -> No se encontró o no fue necesario hacer clic en el banner de cookies.")

        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".custom-courses-item")))
        print(f"  -> Contenedor de cursos encontrado en {CENTRO_NOMBRE}.")
        
        cursos_a_visitar = []
        course_items = driver.find_elements(By.CLASS_NAME, 'custom-courses-item')
        for item in course_items:
            try:
                location_tag = item.find_element(By.CSS_SELECTOR, 'ul > li:first-child')
                if "Santa Cruz de Tenerife" in location_tag.text:
                    link = item.find_element(By.CSS_SELECTOR, 'a.btn-outline-primary').get_attribute('href')
                    title = item.find_element(By.CLASS_NAME, 'title').text.strip()
                    cursos_a_visitar.append({'url': link, 'title': title})
            except:
                continue
                
        if not cursos_a_visitar:
            print(f"No se encontraron cursos para Santa Cruz en {CENTRO_NOMBRE}.")
        else:
            print(f"Descubiertos {len(cursos_a_visitar)} cursos en Santa Cruz. Procediendo a extraer detalles...")
            for curso in cursos_a_visitar:
                curso_data = _scrape_detail_page(driver, curso['url'], curso['title'])
                if curso_data:
                    cursos_encontrados.append(curso_data)
                    
    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
        driver.save_screenshot(f"debug_screenshot_{CENTRO_NOMBRE.lower().replace(' ', '')}.png")
    finally:
        driver.quit()
        
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos procesados.")
    return cursos_encontrados