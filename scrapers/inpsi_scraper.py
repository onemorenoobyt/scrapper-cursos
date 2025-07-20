# scrapers/inpsi_scraper.py (VERSIÓN FINAL SIN VISITAR DETALLES)
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

START_URL = "https://www.inpsi.com/cursos/"
CENTRO_NOMBRE = "INPSI"

def _normalize_date(date_string):
    if "No especificado" in date_string: return date_string
    try:
        return datetime.strptime(date_string.strip(), '%d/%m/%Y').strftime('%Y-%m-%d')
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
        current_url = START_URL
        urls_visitadas = set()
        
        while current_url:
            if current_url in urls_visitadas: break
            
            print(f"Procesando página de listado: {current_url}")
            driver.get(current_url)
            urls_visitadas.add(current_url)
            
            try: # El banner de cookies puede aparecer en cualquier página de la paginación
                cookie_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CLASS_NAME, "cmplz-accept")))
                driver.execute_script("arguments[0].click();", cookie_button)
                print("  -> Banner de cookies aceptado.")
                time.sleep(2)
            except Exception:
                pass # Si no hay banner, continuamos

            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "article.ae-post-list-item")))
            
            course_cards = driver.find_elements(By.CSS_SELECTOR, "article.ae-post-list-item")

            for card in course_cards:
                try:
                    # Filtramos por sede ANTES de procesar para evitar cursos de Candelaria, etc.
                    ubicacion_tags = card.find_elements(By.CSS_SELECTOR, "p.ae-term-item.ae-term-candelaria, p.ae-term-item.ae-term-online")
                    if ubicacion_tags:
                        continue # Si encuentra 'Candelaria' u 'Online', salta esta tarjeta

                    nombre = card.find_element(By.CSS_SELECTOR, 'h2.titulo-curso').text.strip()
                    url_curso = card.find_element(By.CSS_SELECTOR, 'a.elementor-button-link').get_attribute('href')
                    
                    # Extraer fechas y otros datos directamente de la tarjeta
                    fecha_inicio_str = card.find_element(By.CSS_SELECTOR, '.elementor-element-854c6dd h3.date').text.strip()
                    fecha_fin_str = card.find_element(By.CSS_SELECTOR, '.elementor-element-9caebe9 h3.date').text.strip()
                    horario = card.find_element(By.CSS_SELECTOR, '.elementor-element-74ca3a1 h2.ae-acf-content-wrapper').text.replace('Horario:', '').strip()
                    
                    horas_str = "0"
                    try:
                        horas_text = card.find_element(By.CSS_SELECTOR, '.elementor-element-1a6008f h2.ae-acf-content-wrapper').text
                        horas_str = ''.join(filter(str.isdigit, horas_text))
                    except: pass
                        
                    curso_data = { "centro": CENTRO_NOMBRE, "nombre": nombre, "url": url_curso, "inicio": _normalize_date(fecha_inicio_str), "fin": _normalize_date(fecha_fin_str), "horario": horario, "horas": int(horas_str) if horas_str else 0 }
                    cursos_encontrados.append(curso_data)

                except Exception as e:
                    # print(f"  -> Advertencia al procesar una tarjeta de INPSI: {e}")
                    continue

            try:
                next_page_link = driver.find_element(By.CSS_SELECTOR, 'a.next.page-numbers')
                current_url = next_page_link.get_attribute('href')
            except:
                current_url = None
                
    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
        driver.save_screenshot(f"debug_screenshot_{CENTRO_NOMBRE.lower().replace(' ', '')}.png")
    finally:
        driver.quit()
        
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados