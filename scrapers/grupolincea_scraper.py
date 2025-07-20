# Contenido de scrapers/grupolincea_scraper.py (VERSIÓN FINAL Y ROBUSTA)
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

START_URL = "https://grupolincea.es/cursos-tenerife-2/"
CENTRO_NOMBRE = "Grupo Lincea"

def _normalize_date(date_string):
    """
    Función robusta que intenta parsear múltiples formatos de fecha.
    Maneja formatos como 'dd/mm/yyyy', 'dd/mm/yy', y texto como "POR DETERMINAR".
    """
    if not date_string or "DETERMINAR" in date_string.upper():
        return "No disponible"
    
    cleaned_date = date_string.strip().replace(' ', '')
    
    # Lista de formatos a probar, del más específico al más general
    formats_to_try = [
        '%d/%m/%Y', # Ejemplo: 12/02/2025
        '%d/%m/%y', # Ejemplo: 12/02/25
    ]
    
    for fmt in formats_to_try:
        try:
            return datetime.strptime(cleaned_date, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue # Si el formato no coincide, prueba el siguiente
            
    # Si ninguno de los formatos estándar funcionó, podría ser un error o un formato de texto
    return "No disponible"

def _scrape_detail_page(driver, course_url):
    """Extrae los datos de la página de detalle de un curso."""
    try:
        driver.get(course_url)
        # Espera a que el título de la página cargue, es una buena señal de que la página está lista
        WebDriverWait(driver, 20).until(lambda d: d.title != "Cursos Tenerife")
        
        nombre = driver.title.split('-')[0].strip()
        
        # Extraemos todo el texto del contenedor principal para procesarlo
        content_area = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "entry-content"))
        )
        all_text = content_area.text
        lines = all_text.split('\n')

        fecha_inicio_str, fecha_fin_str, horario = "No disponible", "No disponible", "No disponible"

        for i, line in enumerate(lines):
            # Buscamos las etiquetas y extraemos el valor de la línea siguiente
            if "FECHA DE INICIO" in line.upper() and i + 1 < len(lines):
                fechas_raw = lines[i+1]
                if '–' in fechas_raw:
                    parts = fechas_raw.split('–')
                    fecha_inicio_str = parts[0].strip()
                    fecha_fin_str = parts[1].strip()
                else:
                    fecha_inicio_str = fechas_raw.strip()
            elif "HORARIO" in line.upper() and i + 1 < len(lines):
                horario = lines[i+1].strip()

        # Si no encontramos fecha de inicio, no nos interesa el curso
        if fecha_inicio_str == "No disponible":
            return None

        return {
            "centro": CENTRO_NOMBRE, "nombre": nombre, "url": course_url,
            "inicio": _normalize_date(fecha_inicio_str),
            "fin": _normalize_date(fecha_fin_str),
            "horario": horario, "horas": 0
        }
    except Exception as e:
        print(f"  -> ADVERTENCIA: Error procesando detalle {course_url}. Razón: {e}")
        return None

def scrape():
    """Scraper dinámico en dos fases para Grupo Lincea."""
    print(f"Iniciando scraper para {CENTRO_NOMBRE} con Selenium...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    cursos_encontrados = []
    try:
        driver.get(START_URL)
        print(f"  -> Página principal de {CENTRO_NOMBRE} cargada.")
        
        try:
            cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.cmplz-accept")))
            driver.execute_script("arguments[0].click();", cookie_button)
            print("  -> Banner de cookies aceptado.")
        except Exception:
            print("  -> No se encontró el banner de cookies.")
        
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "figure.wp-block-image a")))
        
        course_links_elements = driver.find_elements(By.CSS_SELECTOR, 'figure.wp-block-image a')
        links_a_visitar = sorted(list(set([elem.get_attribute('href') for elem in course_links_elements if elem.get_attribute('href')])))
        
        print(f"Descubiertos {len(links_a_visitar)} enlaces únicos. Extrayendo detalles...")

        for link in links_a_visitar:
            curso_data = _scrape_detail_page(driver, link)
            if curso_data:
                cursos_encontrados.append(curso_data)
                print(f"  -> EXTRAÍDO: {curso_data['nombre']}")
                
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