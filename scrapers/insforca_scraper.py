# Contenido de scrapers/insforca_scraper.py (VERSIÓN FINAL Y ROBUSTA)
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

URL = "https://www.insforca.com/formacion/cursos-gratuitos-prioritariamente-para-desempleados-as/"
CENTRO_NOMBRE = "Insforca"

def _normalize_date(date_string):
    """Convierte una cadena de fecha dd/mm/yyyy a YYYY-MM-DD."""
    try:
        return datetime.strptime(date_string.strip(), '%d/%m/%Y').strftime('%Y-%m-%d')
    except (ValueError, IndexError):
        return "No disponible"

def scrape():
    """Scraper robusto para Insforca que hace clic en la pestaña de Tenerife y espera al contenido."""
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
        
        # --- PASO 1: Hacer clic en la pestaña de Tenerife ---
        try:
            tenerife_tab_xpath = "//span[b[contains(text(), 'TENERIFE')]]"
            tenerife_tab = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, tenerife_tab_xpath))
            )
            driver.execute_script("arguments[0].click();", tenerife_tab)
            print("  -> Clic en la pestaña de 'TENERIFE' realizado.")
        except Exception as e:
            print(f"  -> No se pudo hacer clic en la pestaña de Tenerife. Razón: {e}")
            raise

        # --- PASO 2: Espera explícita para el contenido de la pestaña ---
        # CORRECCIÓN DEFINITIVA: Esperamos a que el contenedor de la pestaña de Tenerife
        # sea visible y que contenga al menos un curso.
        tenerife_pane_selector = "div.su-tabs-pane[data-title*='TENERIFE']"
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"{tenerife_pane_selector} .tlp-portfolio-item"))
        )
        print("  -> Contenido de la pestaña de Tenerife cargado y visible.")

        # --- PASO 3: Extraer los datos ---
        tenerife_pane = driver.find_element(By.CSS_SELECTOR, tenerife_pane_selector)
        course_list = tenerife_pane.find_elements(By.CLASS_NAME, 'tlp-portfolio-item')
        
        print(f"  -> Encontrados {len(course_list)} cursos en la pestaña de Tenerife.")
        
        for item in course_list:
            try:
                details_div = item.find_element(By.CLASS_NAME, 'tlp-portfolio-sd')
                details_text = details_div.text
                
                if "INICIO:" not in details_text: continue

                nombre = item.find_element(By.CSS_SELECTOR, 'h3 a').text.strip()
                url_curso = item.find_element(By.CSS_SELECTOR, 'h3 a').get_attribute('href')
                
                fecha_inicio, fecha_fin, horas = "No disponible", "No disponible", "0"
                
                lines = details_text.split('\n')
                for line in lines:
                    if line.strip().startswith("INICIO:"):
                        fechas_part = line.replace("INICIO:", "").strip()
                        if '|' in fechas_part:
                            fecha_inicio = fechas_part.split('|')[0].strip()
                            fecha_fin = fechas_part.split('|')[1].replace('FIN:', '').strip()
                        else:
                            fecha_inicio = fechas_part
                    elif line.strip().startswith("DURACIÓN:"):
                        horas = ''.join(filter(str.isdigit, line))

                curso_data = {
                    "centro": CENTRO_NOMBRE, "nombre": nombre, "url": url_curso,
                    "inicio": _normalize_date(fecha_inicio), "fin": _normalize_date(fecha_fin),
                    "horario": "No disponible", "horas": int(horas) if horas else 0
                }
                cursos_encontrados.append(curso_data)
            except Exception as e:
                print(f"  -> ADVERTENCIA: Error procesando un curso de Insforca. Saltando. Razón: {e}")
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