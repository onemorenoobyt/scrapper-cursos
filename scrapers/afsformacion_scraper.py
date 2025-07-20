# scrapers/afsformacion_scraper.py
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

URL = "https://afsformacion.com/nuestros-cursos/desempleados/tenerife/"
CENTRO_NOMBRE = "AFS Formación"

def _normalize_date(date_string):
    if "INMEDIATO" in date_string.upper(): return "Inicio Inmediato"
    meses = {'ENERO': '01', 'FEBRERO': '02', 'MARZO': '03', 'ABRIL': '04', 'MAYO': '05', 'JUNIO': '06', 'JULIO': '07', 'AGOSTO': '08', 'SEPTIEMBRE': '09', 'OCTUBRE': '10', 'NOVIEMBRE': '11', 'DICIEMBRE': '12'}
    for mes_nombre, mes_num in meses.items():
        if mes_nombre in date_string.upper():
            current_month = datetime.now().month
            current_year = datetime.now().year
            year = current_year if int(mes_num) >= current_month else current_year + 1
            return f"{year}-{mes_num}-01"
    return "No especificado"

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
        
        try:
            cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "wt-cli-accept-all-btn")))
            driver.execute_script("arguments[0].click();", cookie_button)
            print("  -> Banner de cookies aceptado.")
            time.sleep(2)
        except Exception:
            print("  -> No se encontró o no fue necesario hacer clic en el banner de cookies.")

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print("  -> Scroll a la página realizado.")
        time.sleep(3)

        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "article.elementor-post")))
        print(f"  -> Contenedor de cursos encontrado en {CENTRO_NOMBRE}.")

        course_list = driver.find_elements(By.CSS_SELECTOR, "article.elementor-post")
        print(f"  -> {len(course_list)} tarjetas de curso encontradas. Procesando...")
        
        for item in course_list:
            try:
                nombre_element = item.find_element(By.CLASS_NAME, "elementor-post__title")
                nombre = nombre_element.text.strip()
                url_curso = nombre_element.find_element(By.TAG_NAME, "a").get_attribute('href')
                
                datos_container = item.find_element(By.CLASS_NAME, "elementor-post__datos-curso")
                campos = datos_container.find_elements(By.CLASS_NAME, "elementor-post__datos-curso__campo")
                
                datos_dict = {}
                for campo in campos:
                    try:
                        etiqueta = campo.find_element(By.CLASS_NAME, "elementor-post__datos-curso__campo__etiqueta").text.replace(':', '').strip()
                        valor = campo.find_element(By.CLASS_NAME, "elementor-post__datos-curso__campo__valor").text.strip()
                        datos_dict[etiqueta] = valor
                    except:
                        continue

                fecha_str = datos_dict.get("Inicio", "No especificado")
                horario = datos_dict.get("Horario", "No especificado")
                horas_str = ''.join(filter(str.isdigit, datos_dict.get("Duración", "0")))

                if not nombre: continue

                curso_data = {"centro": CENTRO_NOMBRE, "nombre": nombre, "url": url_curso, "inicio": _normalize_date(fecha_str), "fin": "No disponible", "horario": horario, "horas": int(horas_str) if horas_str.isdigit() else 0}
                cursos_encontrados.append(curso_data)
            except Exception as e:
                print(f"    -> ADVERTENCIA: No se pudo procesar una tarjeta de AFS. Razón: {e}")
                continue

    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
        driver.save_screenshot(f"debug_screenshot_{CENTRO_NOMBRE.lower().replace(' ', '')}.png")
    finally:
        driver.quit()
        
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados