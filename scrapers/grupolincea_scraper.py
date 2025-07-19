# Contenido de scrapers/grupolincea_scraper.py (CORREGIDO)
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
    if "No especificado" in date_string: return date_string
    try:
        # El formato ahora es DD/MM/YYYY
        dt_object = datetime.strptime(date_string, '%d/%m/%Y')
        return dt_object.strftime('%Y-%m-%d')
    except ValueError:
        # Intentar con formato corto de año si el anterior falla
        try:
            dt_object = datetime.strptime(date_string, '%d/%m/%y')
            return dt_object.strftime('%Y-%m-%d')
        except ValueError:
            return "Formato de fecha no reconocido"

def _scrape_detail_page(driver, course_url):
    try:
        driver.get(course_url)
        # Esperar un elemento que sea probable que esté en la página de detalle
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        
        nombre = driver.find_element(By.TAG_NAME, 'h1').text.strip()
        
        # La información de fecha ahora puede estar en diferentes elementos
        fecha_inicio_str, fecha_fin_str, horario = "No especificado", "No especificado", "No especificado"
        
        # Búsqueda más robusta de la información
        elements_with_text = driver.find_elements(By.XPATH, "//*[contains(text(), 'FECHA DE INICIO') or contains(text(), 'HORARIO')]")
        
        if not elements_with_text:
            return None # Si no hay fecha, no nos interesa

        # Extraer fecha
        try:
            fecha_label = driver.find_element(By.XPATH, "//*[contains(text(), 'FECHA DE INICIO')]")
            fecha_data_tag = fecha_label.find_element(By.XPATH, "./following-sibling::*[1]")
            fechas_str = fecha_data_tag.text.strip()
            if '–' in fechas_str:
                fecha_inicio_str, fecha_fin_str = [d.strip() for d in fechas_str.split('–')]
            else:
                fecha_inicio_str = fechas_str
        except:
             return None # Sin fecha de inicio, descartamos el curso

        # Extraer horario (opcional)
        try:
            horario_label = driver.find_element(By.XPATH, "//*[contains(text(), 'HORARIO')]")
            horario_data_tag = horario_label.find_element(By.XPATH, "./following-sibling::*[1]")
            horario = horario_data_tag.text.strip()
        except:
            pass
            
        return {"centro": CENTRO_NOMBRE, "nombre": nombre, "url": course_url, "inicio": _normalize_date(fecha_inicio_str), "fin": _normalize_date(fecha_fin_str), "horario": horario, "horas": 0}
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
        driver.get(START_URL)
        print(f"  -> Página principal de {CENTRO_NOMBRE} cargada.")
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.cmplz-accept"))).click()
            print("  -> Banner de cookies aceptado.")
            time.sleep(2)
        except Exception:
            print("  -> No se encontró banner de cookies o no fue necesario.")

        # --- ¡CAMBIO CLAVE! Selector de espera y búsqueda actualizado ---
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "article.elementor-post a")))
        print(f"  -> Contenedor de cursos encontrado y visible en {CENTRO_NOMBRE}.")
        
        course_items = driver.find_elements(By.CSS_SELECTOR, 'article.elementor-post a')
        links_a_visitar = [item.get_attribute('href') for item in course_items]
        
        if not links_a_visitar:
            print(f"No se encontraron enlaces a cursos en {CENTRO_NOMBRE}.")
        else:
            unique_links = sorted(list(set(links_a_visitar)))
            print(f"Descubiertos {len(unique_links)} enlaces únicos a cursos. Procediendo a extraer detalles...")
            for link in unique_links:
                curso_data = _scrape_detail_page(driver, link)
                if curso_data:
                    cursos_encontrados.append(curso_data)
    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
    finally:
        driver.quit()
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos con fecha encontrados.")
    return cursos_encontrados