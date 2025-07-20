# Contenido de scrapers/inpsi_scraper.py (VERSIÓN FINAL Y ROBUSTA)
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
    """Convierte una cadena de fecha dd/mm/yyyy a YYYY-MM-DD."""
    if not date_string or date_string.isspace():
        return "No disponible"
    try:
        return datetime.strptime(date_string.strip(), '%d/%m/%Y').strftime('%Y-%m-%d')
    except (ValueError, IndexError):
        return "No disponible"

def scrape():
    """Scraper dinámico para INPSI que maneja paginación y extrae detalles."""
    print(f"Iniciando scraper para {CENTRO_NOMBRE} con Selenium...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    cursos_encontrados = []
    
    try:
        driver.get(START_URL)
        print(f"  -> Página principal de {CENTRO_NOMBRE} cargada.")
        
        try:
            cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "cmplz-accept")))
            driver.execute_script("arguments[0].click();", cookie_button)
            print("  -> Banner de cookies aceptado.")
        except Exception:
            print("  -> No se encontró el banner de cookies.")

        current_page = 1
        while True:
            print(f"  -> Procesando página {current_page}...")
            
            # CORRECCIÓN DEFINITIVA: Esperamos a que el contenedor principal esté presente
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.ae-post-list-wrapper")))
            time.sleep(2) # Pausa extra para que el JS renderice las tarjetas
            
            course_cards = driver.find_elements(By.CSS_SELECTOR, 'article.ae-post-list-item')
            if not course_cards:
                print("  -> No se encontraron tarjetas de curso en la página actual.")
                break

            for card in course_cards:
                try:
                    # Filtro de Sede/Modalidad
                    if card.find_elements(By.CSS_SELECTOR, "p.ae-term-candelaria, p.ae-term-online"):
                        continue
                    
                    nombre = card.find_element(By.CSS_SELECTOR, 'p.elementor-heading-title').text.strip()
                    url_curso = card.find_element(By.CSS_SELECTOR, 'a.elementor-button').get_attribute('href')
                    
                    fechas_elements = card.find_elements(By.CSS_SELECTOR, 'h3.date')
                    fecha_inicio = fechas_elements[0].text if len(fechas_elements) > 0 else "No disponible"
                    fecha_fin = fechas_elements[1].text if len(fechas_elements) > 1 else "No disponible"

                    horario = "No disponible"
                    try:
                        horario_element = card.find_element(By.XPATH, ".//h2[contains(., 'Horario:')]")
                        horario = horario_element.text.replace('Horario:', '').strip()
                    except Exception:
                        pass
                    
                    horas = "0"
                    try:
                        horas_element = card.find_element(By.XPATH, ".//h2[contains(., 'horas')]")
                        horas = ''.join(filter(str.isdigit, horas_element.text))
                    except Exception:
                        pass

                    curso_data = {
                        "centro": CENTRO_NOMBRE, "nombre": nombre, "url": url_curso,
                        "inicio": _normalize_date(fecha_inicio), "fin": _normalize_date(fecha_fin),
                        "horario": horario, "horas": int(horas) if horas else 0
                    }
                    cursos_encontrados.append(curso_data)
                except Exception as e:
                    print(f"  -> ADVERTENCIA: Error procesando tarjeta de INPSI. Saltando. Razón: {e}")
                    continue

            # Paginación
            try:
                next_page_link = driver.find_element(By.CSS_SELECTOR, 'a.next.page-numbers')
                print(f"  -> Navegando a la página {current_page + 1}...")
                driver.execute_script("arguments[0].click();", next_page_link)
                WebDriverWait(driver, 20).until(EC.staleness_of(course_cards[0]))
                current_page += 1
            except Exception:
                print("  -> No hay más páginas. Finalizando paginación.")
                break
                
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