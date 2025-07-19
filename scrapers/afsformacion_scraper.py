# Contenido de scrapers/afsformacion_scraper.py (¡NUEVA VERSIÓN CON SELENIUM!)
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

# ... (la función _normalize_date se mantiene igual) ...
def _normalize_date(date_string):
    if "INMEDIATO" in date_string.upper(): return "Inicio Inmediato"
    meses = {'ENERO': '01', 'FEBRERO': '02', 'MARZO': '03', 'ABRIL': '04', 'MAYO': '05', 'JUNIO': '06', 'JULIO': '07', 'AGOSTO': '08', 'SEPTIEMBRE': '09', 'OCTUBRE': '10', 'NOVIEMBRE': '11', 'DICIEMBRE': '12'}
    for mes_nombre, mes_num in meses.items():
        if mes_nombre in date_string.upper():
            return f"{datetime.now().year}-{mes_num}-01"
    return "No especificado"

def scrape():
    print(f"Iniciando scraper para {CENTRO_NOMBRE} con Selenium...")
    
    # Configuración de Selenium para que funcione en GitHub Actions (sin interfaz gráfica)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Instala y gestiona el driver de Chrome automáticamente
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    
    cursos_encontrados = []
    try:
        driver.get(URL)
        # Esperamos un máximo de 20 segundos a que aparezca el primer contenedor de curso
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "elementor-post"))
        )
        print(f"  -> Conexión exitosa y contenido cargado en {CENTRO_NOMBRE}.")

        course_list = driver.find_elements(By.CLASS_NAME, "elementor-post")
        if not course_list:
            print(f"  !!! ERROR: No se encontró la lista de cursos en {CENTRO_NOMBRE} incluso con Selenium.")
            driver.quit()
            return []

        for item in course_list:
            try:
                nombre = item.find_element(By.CLASS_NAME, "elementor-post__title").text.strip()
                url_curso = item.find_element(By.TAG_NAME, "a").get_attribute('href')
                metas = item.find_elements(By.CLASS_NAME, 'elementor-icon-list-item')
                fecha_str, horario, horas_str = "No especificado", "No especificado", "0"
                for meta in metas:
                    text = meta.text.upper()
                    if 'INICIO:' in text: fecha_str = meta.text.replace('Inicio:', '').strip()
                    elif 'HORARIO:' in text: horario = meta.text.replace('Horario:', '').strip()
                    elif 'DURACIÓN:' in text: horas_str = meta.text.replace('Duración:', '').replace('Horas', '').strip()
                
                curso_data = {"centro": CENTRO_NOMBRE, "nombre": nombre, "url": url_curso, "inicio": _normalize_date(fecha_str), "fin": "No disponible", "horario": horario, "horas": int(horas_str) if horas_str.isdigit() else 0}
                cursos_encontrados.append(curso_data)
            except Exception as e:
                print(f"  -> Error al procesar un curso de {CENTRO_NOMBRE}: {e}")
                continue
    
    except Exception as e:
        print(f"  !!! ERROR CRÍTICO en el scraper de {CENTRO_NOMBRE}: {e}")
    finally:
        driver.quit() # Es muy importante cerrar el navegador al final
        
    print(f"Scraper de {CENTRO_NOMBRE} finalizado. {len(cursos_encontrados)} cursos encontrados.")
    return cursos_encontrados

if __name__ == '__main__':
    cursos = scrape()
    for c in cursos:
        print(c)