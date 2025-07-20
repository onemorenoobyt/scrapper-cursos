# scrapers/icse_scraper.py
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

URL = "https://www.icse.es/cursos?type=2&island=Tenerife"
CENTRO_NOMBRE = "ICSE"

def _normalize_date(date_string):
    try:
        dt_object = datetime.strptime(date_string.split(' - ')[0].strip(), '%d/%m/%Y')
        return dt_object.strftime('%Y-%m-%d')
    except (ValueError, IndexError):
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
        
        time.sleep(5) # Pausa generosa para que Livewire cargue el contenido
        
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.course-card")))
        print(f"  -> Contenido dinámico (Livewire) cargado en {CENTRO_NOMBRE}.")
        
        course_list = driver.find_elements(By.CSS_SELECTOR, 'div.course-card')

        if not course_list:
            print(f"  !!! ADVERTENCIA: No se encontró la lista de cursos en {CENTRO_NOMBRE}.")
            return []

        for item in course_list:
            try:
                sede_tag = item.find_element(By.CLASS_NAME, 'headquarter')
                if "STA. CRUZ DE TENERIFE" in sede_tag.text.upper():
                    title_anchor = item.find_element(By.CSS_SELECTOR, 'h2.text-xl a')
                    nombre = title_anchor.text.strip()
                    url_curso = title_anchor.get_attribute('href')
                    
                    fechas_tag = item.find_element(By.CSS_SELECTOR, 'ul > li:first-child')
                    fechas_str = fechas_tag.text.strip() if fechas_tag else "No especificado"

                    fechas_parts = [d.strip() for d in fechas_str.split(' - ')]
                    fecha_inicio_str = fechas_parts[0]
                    fecha_fin_str = fechas_parts[1] if len(fechas_parts) > 1 else "No disponible"

                    curso_data = {
                        "centro": CENTRO_NOMBRE, "nombre": nombre, "url": url_curso,
                        "inicio": _normalize_date(fecha_inicio_str),
                        "fin": _normalize_date(fecha_fin_str),
                        "horario": "No disponible en listado", "horas": 0
                    }
                    cursos_encontrados.append(curso_data)
            except Exception as e:
                continue
    
    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
        driver.save_screenshot(f"debug_screenshot_{CENTRO_NOMBRE.lower().replace(' ', '')}.png")
    finally:
        driver.quit()
        
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados