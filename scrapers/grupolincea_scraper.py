# scrapers/grupolincea_scraper.py (VERSIÓN FINAL CON EXTRACCIÓN DE TEXTO BRUTO)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import sys
import time
sys.path.append('.')
import config

START_URL = "https://grupolincea.es/cursos-tenerife-2/"
CENTRO_NOMBRE = "Grupo Lincea"

def _normalize_date(date_string):
    if not date_string or date_string.isspace() or "determinar" in date_string.lower():
        return "No especificado"
    cleaned_date = date_string.strip().replace(' ', '')
    for fmt in ('%d/%m/%Y', '%-d/%m/%Y', '%d/%m/%y'):
        try:
            return datetime.strptime(cleaned_date, fmt).strftime('%Y-%m-%d')
        except ValueError:
            pass
    return "Formato de fecha no reconocido"

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
            cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.cmplz-accept")))
            driver.execute_script("arguments[0].click();", cookie_button)
            print("  -> Banner de cookies aceptado.")
            time.sleep(2)
        except Exception:
            print("  -> No se encontró o no fue necesario hacer clic en el banner de cookies.")

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "figure.wp-block-image a")))
        print(f"  -> Contenedor de cursos encontrado y visible.")
        
        course_links_elements = driver.find_elements(By.CSS_SELECTOR, 'figure.wp-block-image a')
        links_a_visitar = [elem.get_attribute('href') for elem in course_links_elements if elem.get_attribute('href') and 'grupolincea.es' in elem.get_attribute('href')]
        unique_links = sorted(list(set(links_a_visitar)))
        print(f"Descubiertos {len(unique_links)} enlaces únicos. Procediendo a extraer detalles...")

        for link in unique_links:
            try:
                driver.get(link)
                # Esperamos a que el título de la pestaña cargue
                WebDriverWait(driver, 20).until_not(EC.title_contains("CURSOS TENERIFE"))
                time.sleep(2) # Pausa extra para que el JS termine de renderizar

                # --- LÓGICA DE EXTRACCIÓN FINAL ---
                
                # 1. Título desde la pestaña del navegador (más fiable)
                nombre = driver.title.split('-')[0].strip()
                
                # 2. Extraemos todo el texto del contenedor principal
                content_area = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "entry-content"))
                )
                all_text = content_area.text
                lines = all_text.split('\n')

                fecha_inicio_str = "No especificado"
                fecha_fin_str = "No especificado"
                horario = "No especificado"

                # 3. Procesamos el texto línea por línea
                for i, line in enumerate(lines):
                    if "FECHA INICIO" in line.upper() and i + 1 < len(lines):
                        fecha_inicio_str = lines[i+1]
                    elif "FECHA FIN" in line.upper() and i + 1 < len(lines):
                        fecha_fin_str = lines[i+1]
                    elif "HORARIO" in line.upper() and i + 1 < len(lines):
                        horario = lines[i+1]

                # Si solo encontramos una fecha, la asignamos a inicio
                if fecha_inicio_str == "No especificado" and fecha_fin_str != "No especificado":
                    fecha_inicio_str = fecha_fin_str
                    fecha_fin_str = "No especificado"

                curso_data = {
                    "centro": CENTRO_NOMBRE, "nombre": nombre, "url": link,
                    "inicio": _normalize_date(fecha_inicio_str), "fin": _normalize_date(fecha_fin_str),
                    "horario": horario, "horas": 0
                }
                cursos_encontrados.append(curso_data)
                print(f"  -> Añadido curso: '{nombre}'")

            except Exception as e:
                print(f"  -> Error procesando detalle del curso {link}: {e}")
                continue

    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
        driver.save_screenshot(f"debug_screenshot_{CENTRO_NOMBRE.lower().replace(' ', '')}.png")
    finally:
        driver.quit()
        
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos con fecha encontrados.")
    return cursos_encontrados