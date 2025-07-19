# Contenido de scrapers/afsformacion_scraper.py (VERSIÓN 3 - ROBUSTA)
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
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    cursos_encontrados = []
    
    try:
        driver.get(URL)
        print(f"  -> Página principal de {CENTRO_NOMBRE} cargada.")

        # --- MEJORA 1: GESTIÓN DE COOKIES ---
        # Esperamos hasta 5 segundos a que aparezca el botón de cookies y hacemos clic.
        # Si no aparece en 5 segundos, el 'except' evita que el programa se rompa y continúa.
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "wt-cli-accept-all-btn"))).click()
            print("  -> Banner de cookies aceptado.")
            time.sleep(2) # Damos un respiro para que la página reaccione
        except Exception:
            print("  -> No se encontró banner de cookies, o no fue necesario hacer clic.")

        # --- MEJORA 2: ESPERA MÁS INTELIGENTE ---
        # Ahora esperamos hasta 20 segundos a que la LISTA de cursos sea visible.
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.elementor-posts-container"))
        )
        print(f"  -> Contenedor de cursos encontrado y visible en {CENTRO_NOMBRE}.")

        course_list = driver.find_elements(By.CSS_SELECTOR, "article.elementor-post")
        if not course_list:
            print(f"  !!! ERROR: No se encontró la lista de cursos en {CENTRO_NOMBRE}.")
        
        for item in course_list:
            try:
                nombre = item.find_element(By.CLASS_NAME, "elementor-post__title").text.strip()
                url_curso = item.find_element(By.TAG_NAME, "a").get_attribute('href')
                
                # --- MEJORA 3: SELECTOR MÁS PRECISO ---
                # Buscamos la lista de características, que es un selector más fiable
                meta_data_list = item.find_element(By.CLASS_NAME, 'elementor-icon-list-items')
                lines = meta_data_list.find_elements(By.TAG_NAME, 'li')

                fecha_str, horario, horas_str = "No especificado", "No especificado", "0"
                for line in lines:
                    text = line.text.upper()
                    if 'INICIO:' in text: fecha_str = line.text.replace('Inicio:', '').strip()
                    elif 'HORARIO:' in text: horario = line.text.replace('Horario:', '').strip()
                    elif 'DURACIÓN:' in text: horas_str = line.text.replace('Duración:', '').replace('Horas', '').strip()

                curso_data = {"centro": CENTRO_NOMBRE, "nombre": nombre, "url": url_curso, "inicio": _normalize_date(fecha_str), "fin": "No disponible", "horario": horario, "horas": int(horas_str) if horas_str.isdigit() else 0}
                cursos_encontrados.append(curso_data)
            except Exception as e:
                print(f"  -> Error al procesar un curso de {CENTRO_NOMBRE}: {e}")
                continue
    
    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
    finally:
        driver.quit()
        
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados

if __name__ == '__main__':
    cursos = scrape()
    import pandas as pd
    df = pd.DataFrame(cursos)
    print(df)