# Contenido de scrapers/icse_scraper.py (VERSIÓN FINAL Y ROBUSTA)
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

URL = "https://www.icse.es/cursos?type=2&island=Tenerife"
CENTRO_NOMBRE = "ICSE"

def _normalize_date(date_string):
    """Convierte una cadena de fecha dd/mm/yyyy a YYYY-MM-DD."""
    if not date_string or date_string.isspace():
        return "No disponible"
    try:
        return datetime.strptime(date_string.strip(), '%d/%m/%Y').strftime('%Y-%m-%d')
    except (ValueError, IndexError):
        return "No disponible"

def scrape():
    """Scraper robusto para ICSE que extrae datos directamente de la página de listado."""
    print(f"Iniciando scraper para {CENTRO_NOMBRE} con Selenium...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f"user-agent={config.HEADERS['User-Agent']}")
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    cursos_encontrados = []
    
    try:
        driver.get(URL)
        print(f"  -> Página principal de {CENTRO_NOMBRE} cargada.")
        
        # CORRECCIÓN DEFINITIVA: Espera explícita para el contenido de Livewire.
        # Esperamos a que el texto de la sede dentro de la primera tarjeta sea visible.
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.course-card span.headquarter"))
        )
        print(f"  -> Contenido dinámico (Livewire) cargado en {CENTRO_NOMBRE}.")
        
        course_cards = driver.find_elements(By.CSS_SELECTOR, 'div.course-card')
        
        print(f"  -> {len(course_cards)} tarjetas de curso encontradas. Filtrando por Tenerife...")

        for card in course_cards:
            try:
                # --- Filtro de Sede ---
                sede_tag = card.find_element(By.CLASS_NAME, 'headquarter')
                if "STA. CRUZ DE TENERIFE" not in sede_tag.text.upper():
                    continue

                # --- Extracción de Datos ---
                title_anchor = card.find_element(By.CSS_SELECTOR, 'h2.text-xl')
                nombre = title_anchor.text.strip()
                url_curso = card.find_element(By.TAG_NAME, 'a').get_attribute('href')
                
                # Buscamos la fecha dentro del 'li' que contiene el icono del calendario
                fechas_li = card.find_element(By.XPATH, ".//li[contains(., '/')]") # Busca un li que contenga una barra
                fechas_str = fechas_li.text.strip()
                
                fecha_inicio, fecha_fin = "No disponible", "No disponible"
                if ' - ' in fechas_str:
                    fechas_parts = [d.strip() for d in fechas_str.split(' - ')]
                    fecha_inicio = fechas_parts[0]
                    fecha_fin = fechas_parts[1]

                curso_data = {
                    "centro": CENTRO_NOMBRE,
                    "nombre": nombre,
                    "url": url_curso,
                    "inicio": _normalize_date(fecha_inicio),
                    "fin": _normalize_date(fecha_fin),
                    "horario": "No disponible en listado",
                    "horas": 0  # Este dato no está en la tarjeta
                }
                cursos_encontrados.append(curso_data)

            except Exception as e:
                print(f"  -> ADVERTENCIA: Error procesando una tarjeta de ICSE. Saltando. Razón: {e}")
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