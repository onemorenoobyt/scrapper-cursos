# Contenido de scrapers/afsformacion_scraper.py (VERSIÓN FINAL)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time

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
    options.add_argument('--headless=new') # Usar el nuevo modo headless
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"]) # Ocultar logs de DevTools
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    cursos_encontrados = []
    
    try:
        driver.get(URL)
        print(f"  -> Página principal de {CENTRO_NOMBRE} cargada.")
        
        try:
            cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "wt-cli-accept-all-btn")))
            driver.execute_script("arguments[0].click();", cookie_button) # Clic con JS, más fiable
            print("  -> Banner de cookies aceptado.")
            time.sleep(2)
        except Exception:
            print("  -> No se encontró o no fue necesario hacer clic en el banner de cookies.")

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print("  -> Scroll a la página realizado para cargar contenido dinámico.")
        time.sleep(3)

        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "article.elementor-post .elementor-post__title a")))
        print(f"  -> Contenedor de cursos encontrado en {CENTRO_NOMBRE}.")

        course_list = driver.find_elements(By.CSS_SELECTOR, "article.elementor-post")
        if not course_list:
            raise Exception("La lista de cursos está vacía después de la espera y el scroll.")
        
        print(f"  -> {len(course_list)} tarjetas de curso encontradas. Procesando...")
        for item in course_list:
            try:
                nombre_element = item.find_element(By.CLASS_NAME, "elementor-post__title")
                nombre = nombre_element.text.strip()
                url_curso = nombre_element.find_element(By.TAG_NAME, "a").get_attribute('href')
                
                meta_container = item.find_element(By.CLASS_NAME, 'elementor-icon-list-items')
                lines = meta_container.find_elements(By.TAG_NAME, 'li')
                
                fecha_str, horario, horas_str = "No especificado", "No especificado", "0"
                
                for line in lines:
                    text = line.text.strip()
                    if 'Inicio:' in text: fecha_str = text.replace('Inicio:', '').strip()
                    elif 'Horario:' in text: horario = text.replace('Horario:', '').strip()
                    elif 'Duración:' in text: horas_str = ''.join(filter(str.isdigit, text))

                if not nombre: continue

                curso_data = {"centro": CENTRO_NOMBRE, "nombre": nombre, "url": url_curso, "inicio": _normalize_date(fecha_str), "fin": "No disponible", "horario": horario, "horas": int(horas_str) if horas_str.isdigit() else 0}
                cursos_encontrados.append(curso_data)
            except Exception as e:
                print(f"    -> ADVERTENCIA: No se pudo procesar una tarjeta de AFS. Razón: {e}")
                continue

    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
        driver.save_screenshot("debug_screenshot.png")
        with open("debug_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    finally:
        driver.quit()
        
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados