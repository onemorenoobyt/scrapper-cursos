# Contenido de scrapers/auraformacion_scraper.py (VERSIÓN FINAL Y ROBUSTA)
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

START_URL = "https://www.auraformacion.es/formacion.html"
CENTRO_NOMBRE = "Aura Formación"

def _normalize_date(date_string):
    """Convierte una cadena de texto 'dd de mes de yyyy' a 'YYYY-MM-DD'."""
    if "No especificado" in date_string or not date_string: return "No disponible"
    meses = {'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04', 'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08', 'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'}
    try:
        parts = date_string.lower().split(' de ')
        day = int(parts[0])
        month = meses[parts[1]]
        year = int(parts[2])
        return f"{year}-{month}-{day:02d}"
    except (ValueError, IndexError, KeyError):
        return "No disponible"

def _scrape_detail_page(driver, course_url):
    """Extrae datos de la página de detalle de un curso."""
    try:
        driver.get(course_url)
        # Espera a que el contenedor principal de la información sea visible
        info_box = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "cuadro_informacion"))
        )
        
        # --- Filtro de Sede: Buscamos la palabra clave "Ramón y Cajal" o "TF" ---
        if "Ramón y Cajal" not in info_box.text and "TF" not in info_box.text:
            return None

        # --- Si pasa el filtro, extraemos los datos ---
        nombre = driver.find_element(By.TAG_NAME, 'h1').text.strip()
        
        fecha_inicio, fecha_fin, horas, horario = "No especificado", "No especificado", "0", "No especificado"
        
        # Leemos el texto de los párrafos dentro del cuadro de información
        paragraphs = info_box.find_elements(By.TAG_NAME, 'p')
        for p in paragraphs:
            text = p.text
            if text.startswith("Fecha inicio:"):
                fecha_inicio = text.replace("Fecha inicio:", "").strip()
            elif text.startswith("Fecha fin:"):
                fecha_fin = text.replace("Fecha fin:", "").strip()
            elif text.startswith("Horas totales:"):
                horas = ''.join(filter(str.isdigit, text))
            elif text.startswith("Horario:"):
                horario = text.replace("Horario:", "").strip()
        
        if fecha_inicio == "No especificado":
            return None

        return {
            "centro": CENTRO_NOMBRE, "nombre": nombre, "url": course_url,
            "inicio": _normalize_date(fecha_inicio),
            "fin": _normalize_date(fecha_fin),
            "horario": horario,
            "horas": int(horas) if horas else 0
        }
    except Exception as e:
        print(f"  -> ADVERTENCIA: Error procesando detalle {course_url}. Razón: {e}")
        return None

def scrape():
    """Scraper dinámico en dos fases para Aura Formación."""
    print(f"Iniciando scraper para {CENTRO_NOMBRE} con Selenium...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    cursos_encontrados = []
    # Usamos un set para evitar procesar cursos duplicados
    cursos_unicos = set()
    
    try:
        driver.get(START_URL)
        print(f"  -> Página principal de {CENTRO_NOMBRE} cargada.")

        try:
            cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")))
            driver.execute_script("arguments[0].click();", cookie_button)
            print("  -> Banner de cookies aceptado.")
        except Exception:
            print("  -> No se encontró el banner de cookies.")
        
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "lista_productos")))
        course_items = driver.find_elements(By.CSS_SELECTOR, 'div.blog_curso a')
        
        links_a_visitar = sorted(list(set([item.get_attribute('href') for item in course_items if item.get_attribute('href')])))
        
        print(f"Descubiertos {len(links_a_visitar)} enlaces únicos. Extrayendo y deduplicando...")
        for link in links_a_visitar:
            curso_data = _scrape_detail_page(driver, link)
            if curso_data:
                clave_unica = (curso_data['nombre'], curso_data['inicio'], curso_data['horario'])
                if clave_unica not in cursos_unicos:
                    cursos_encontrados.append(curso_data)
                    cursos_unicos.add(clave_unica)
                    print(f"    -> EXTRAÍDO: {curso_data['nombre']}")
    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
        driver.save_screenshot(f"debug_screenshot_{CENTRO_NOMBRE.lower().replace(' ', '')}.png")
    finally:
        driver.quit()
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos de Tenerife encontrados.")
    return cursos_encontrados

if __name__ == '__main__':
    cursos = scrape()
    print(cursos)