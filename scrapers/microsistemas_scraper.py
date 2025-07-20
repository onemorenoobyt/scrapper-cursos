# scrapers/microsistemas_scraper.py
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
        time.sleep(5) 

        try:
            chat_iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "lbContactIframe")))
            driver.switch_to.frame(chat_iframe)
            close_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "lbContactHeaderMinimize")))
            close_button.click()
            print("  -> Pop-up de chat minimizado.")
            driver.switch_to.default_content()
            time.sleep(2)
        except Exception:
            print("  -> No se encontró o no fue necesario cerrar el pop-up de chat.")

        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.tablepress")))
        print(f"  -> Contenedor de cursos (tablas) encontrado en {CENTRO_NOMBRE}.")
        
        tablas = driver.find_elements(By.CSS_SELECTOR, 'table.tablepress')
        
        if not tablas:
            print(f"  !!! ADVERTENCIA: No se encontraron tablas de cursos en {CENTRO_NOMBRE}.")
            return []

        for tabla in tablas:
            try:
                rows = tabla.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, 'td')
                    if len(cols) < 5: continue

                    nombre = cols[0].text.strip()
                    try:
                        url_curso = cols[1].find_element(By.TAG_NAME, 'a').get_attribute('href')
                    except:
                        url_curso = URL

                    fecha_inicio_str = cols[2].text.strip()
                    fecha_fin_str = cols[3].text.strip()
                    horario = cols[4].text.strip()

                    curso_data = { "centro": CENTRO_NOMBRE, "nombre": nombre, "url": url_curso, "inicio": _normalize_date(fecha_inicio_str), "fin": _normalize_date(fecha_fin_str), "horario": horario, "horas": 0 }
                    cursos_encontrados.append(curso_data)
            except Exception as e:
                print(f"  -> Error procesando una tabla de {CENTRO_NOMBRE}: {e}")
                continue
    
    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
        driver.save_screenshot(f"debug_screenshot_{CENTRO_NOMBRE.lower().replace(' ', '')}.png")
    finally:
        driver.quit()
        
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados