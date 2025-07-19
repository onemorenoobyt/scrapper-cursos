# Contenido de scrapers/afsformacion_scraper.py (VERSIÓN FINAL - CAMUFLADA)
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
    # --- MODO CAMUFLAJE ---
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    # --------------------
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    cursos_encontrados = []
    
    try:
        driver.get(URL)
        print(f"  -> Página principal de {CENTRO_NOMBRE} cargada.")
        time.sleep(3) # Pausa inicial para que carguen los scripts de cookies

        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "wt-cli-accept-all-btn"))).click()
            print("  -> Banner de cookies aceptado.")
            time.sleep(3) # Pausa crucial después de aceptar cookies
        except Exception:
            print("  -> No se encontró banner de cookies o no fue necesario.")

        # --- SIMULACIÓN DE SCROLL ---
        # A veces el contenido solo carga al hacer scroll
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print("  -> Scroll hacia el final de la página realizado.")
        time.sleep(3) # Pausa para que el contenido lazy-load aparezca

        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "article.elementor-post")))
        print(f"  -> Contenedor de cursos encontrado en {CENTRO_NOMBRE}.")

        course_list = driver.find_elements(By.CSS_SELECTOR, "article.elementor-post")
        if not course_list:
            raise Exception("La lista de cursos está vacía después de la espera y el scroll.")
        
        for item in course_list:
            # La lógica de extracción se mantiene igual
            # ... (código interno del bucle)
            try:
                nombre = item.find_element(By.CLASS_NAME, "elementor-post__title").text.strip()
                url_curso = item.find_element(By.TAG_NAME, "a").get_attribute('href')
                meta_data_elements = item.find_elements(By.CLASS_NAME, 'elementor-icon-list-items')
                if not meta_data_elements: continue
                lines = meta_data_elements[0].find_elements(By.TAG_NAME, 'li')
                fecha_str, horario, horas_str = "No especificado", "No especificado", "0"
                for line in lines:
                    text = line.text
                    if 'Inicio:' in text: fecha_str = line.replace('Inicio:', '').strip()
                    elif 'Horario:' in text: horario = line.replace('Horario:', '').strip()
                    elif 'Duración:' in text: horas_str = line.replace('Duración:', '').replace('Horas', '').strip()
                curso_data = {"centro": CENTRO_NOMBRE, "nombre": nombre, "url": url_curso, "inicio": _normalize_date(fecha_str), "fin": "No disponible", "horario": horario, "horas": int(horas_str) if horas_str.isdigit() else 0}
                cursos_encontrados.append(curso_data)
            except Exception:
                continue

    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
        # --- NUESTRA CAJA NEGRA ---
        # Guardamos el estado final de la página para poder analizarlo
        driver.save_screenshot("debug_screenshot.png")
        with open("debug_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        # ------------------------
    finally:
        driver.quit()
        
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados