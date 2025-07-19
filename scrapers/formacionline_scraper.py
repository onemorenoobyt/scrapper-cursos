# Contenido de scrapers/formacionline_scraper.py (VERSIÓN FINAL)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time

BASE_URL = "https://formacionline.com"
START_URL = "https://formacionline.com/formacion/cursos/"
CENTRO_NOMBRE = "FormacionLine"

def _normalize_date(date_string):
    if "Próximamente" in date_string or not date_string: return "Próximamente"
    try:
        dt_object = datetime.strptime(date_string, '%d/%m/%Y')
        return dt_object.strftime('%Y-%m-%d')
    except ValueError:
        return "Formato de fecha no reconocido"

def _scrape_detail_page(driver, course_url):
    try:
        driver.get(course_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "course-title")))
        
        nombre = driver.find_element(By.CLASS_NAME, 'course-title').text.strip()
        
        horas = "0"
        try:
            horas_element = driver.find_element(By.XPATH, "//span[contains(text(), 'horas')]")
            horas = ''.join(filter(str.isdigit, horas_element.text))
        except:
             pass # Si no hay horas, no es un problema

        fecha_inicio, fecha_fin, horario = "No especificado", "No especificado", "No especificado"
        
        details_section = driver.find_element(By.ID, 'tab-course-curriculum')
        if details_section:
            strong_tags = details_section.find_elements(By.TAG_NAME, 'strong')
            for tag in strong_tags:
                try:
                    next_sibling_text = driver.execute_script("return arguments[0].nextSibling.textContent", tag).strip().replace(':',"")
                    if "Fecha de inicio" in tag.text:
                        fecha_inicio = next_sibling_text
                    elif "Fecha de fin" in tag.text:
                        fecha_fin = next_sibling_text
                    elif "Horario" in tag.text:
                        horario = next_sibling_text
                except:
                    continue
        
        return {"centro": CENTRO_NOMBRE, "nombre": nombre, "url": course_url, "inicio": _normalize_date(fecha_inicio), "fin": _normalize_date(fecha_fin), "horario": horario, "horas": int(horas) if horas.isdigit() else 0}
    except Exception as e:
        print(f"  -> Error procesando detalle del curso {course_url}: {e}")
        return None

def scrape():
    print(f"Iniciando scraper para {CENTRO_NOMBRE} con Selenium...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    cursos_encontrados = []
    
    try:
        driver.get(START_URL)
        print(f"  -> Página principal de {CENTRO_NOMBRE} cargada.")

        try:
            cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "wt-cli-accept-all-btn")))
            cookie_button.click()
            print("  -> Banner de cookies aceptado.")
            time.sleep(2)
        except Exception:
            print("  -> No se encontró o no fue necesario hacer clic en el banner de cookies.")

        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "course-item")))
        print(f"  -> Contenedor de cursos encontrado en {CENTRO_NOMBRE}.")
        
        links_a_visitar = []
        course_items = driver.find_elements(By.CLASS_NAME, 'course-item')
        for item in course_items:
            try:
                location_tag = item.find_element(By.CLASS_NAME, 'meta-item-location')
                if "Santa Cruz de Tenerife" in location_tag.text:
                    link = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    links_a_visitar.append(link)
            except:
                continue
                
        if not links_a_visitar:
            print(f"No se encontraron cursos para Santa Cruz en {CENTRO_NOMBRE}.")
        else:
            print(f"Descubiertos {len(links_a_visitar)} cursos en Santa Cruz. Procediendo a extraer detalles...")
            for link in links_a_visitar:
                curso_data = _scrape_detail_page(driver, link)
                if curso_data:
                    cursos_encontrados.append(curso_data)
                    
    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
    finally:
        driver.quit()
        
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos procesados.")
    return cursos_encontrados