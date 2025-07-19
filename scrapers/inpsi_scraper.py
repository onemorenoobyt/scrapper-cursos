# Contenido de scrapers/inpsi_scraper.py (VERSIÓN FINAL - MIGRADO A SELENIUM)
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

BASE_URL = "https://www.inpsi.com"
START_URL = "https://www.inpsi.com/cursos/"
CENTRO_NOMBRE = "INPSI"

def _normalize_date(date_string):
    if "No especificado" in date_string: return date_string
    try:
        return datetime.strptime(date_string, '%d/%m/%Y').strftime('%Y-%m-%d')
    except ValueError:
        return "Formato de fecha no reconocido"

def _scrape_detail_page(driver, course_url):
    try:
        driver.get(course_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "entry-title")))
        
        nombre = driver.find_element(By.CLASS_NAME, 'entry-title').text.strip()
        info_box = driver.find_element(By.CLASS_NAME, 'info-curso')
        
        sede_elements = info_box.find_elements(By.XPATH, ".//p[contains(.,'Sede:')]//strong")
        if sede_elements:
            sede = sede_elements[0].text.strip()
            if "Candelaria" in sede or "Online" in sede:
                return None
        
        def get_info(keyword):
            try:
                element = info_box.find_element(By.XPATH, f".//p[contains(.,'{keyword}')]//strong")
                return element.text.strip()
            except:
                return "No especificado"

        fecha_inicio_str = get_info("Inicio:")
        fecha_fin_str = get_info("Fin:")
        horario = get_info("Horario:")
        
        return {
            "centro": CENTRO_NOMBRE, "nombre": nombre, "url": course_url,
            "inicio": _normalize_date(fecha_inicio_str), "fin": _normalize_date(fecha_fin_str),
            "horario": horario, "horas": 0
        }
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
        current_url = START_URL
        while current_url:
            print(f"Procesando página de listado: {current_url}")
            driver.get(current_url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "article.curso h2.entry-title a")))
            
            course_links = [a.get_attribute('href') for a in driver.find_elements(By.CSS_SELECTOR, 'article.curso h2.entry-title a')]
            
            for link in course_links:
                curso_data = _scrape_detail_page(driver, link)
                if curso_data:
                    cursos_encontrados.append(curso_data)
            
            try:
                next_page_link = driver.find_element(By.CSS_SELECTOR, 'a.next.page-numbers')
                current_url = next_page_link.get_attribute('href')
            except:
                current_url = None # No more pages
                
    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
    finally:
        driver.quit()
        
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados