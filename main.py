# Contenido de main.py (VERSIÓN MODIFICADA PARA DEPURACIÓN)
import pandas as pd
import sqlite3
import database
import sys  # Importamos el módulo sys para leer argumentos de la línea de comandos
from scrapers import (
    afsformacion_scraper,
    auraformacion_scraper,
    cep_scraper,
    focan_scraper,
    grupolincea_scraper,
    icse_scraper,
    inpsi_scraper,
    insforca_scraper,
    microsistemas_scraper,
    formacionline_scraper
)

def main():
    """Función principal del programa de scraping."""
    print("--- INICIANDO PROCESO DE SCRAPING ---")
    database.setup_database()
    
    todos_los_cursos = []
    
    # Creamos un diccionario que mapea nombres de string a los módulos de scraper
    scrapers_disponibles = {
        "afs": afsformacion_scraper,
        "aura": auraformacion_scraper,
        "cep": cep_scraper,
        "focan": focan_scraper,
        "lincea": grupolincea_scraper,
        "icse": icse_scraper,
        "inpsi": inpsi_scraper,
        "insforca": insforca_scraper,
        "microsistemas": microsistemas_scraper,
        "formacionline": formacionline_scraper
    }
    
    # Comprobamos si se ha pasado un argumento desde la línea de comandos
    scraper_a_ejecutar_nombre = None
    if len(sys.argv) > 1:
        scraper_a_ejecutar_nombre = sys.argv[1]

    if scraper_a_ejecutar_nombre:
        # Si se especificó un scraper, ejecutamos solo ese
        print(f"--- MODO DEPURACIÓN: Ejecutando únicamente el scraper '{scraper_a_ejecutar_nombre}' ---")
        scraper_module = scrapers_disponibles.get(scraper_a_ejecutar_nombre)
        if scraper_module:
            scrapers_a_ejecutar = [scraper_module]
        else:
            print(f"---! ERROR: El scraper '{scraper_a_ejecutar_nombre}' no existe. Scrapers disponibles: {list(scrapers_disponibles.keys())} !---")
            return # Salimos del script si el nombre es incorrecto
    else:
        # Si no se especifica ninguno, se ejecutan todos (comportamiento normal)
        print("--- MODO NORMAL: Ejecutando todos los scrapers ---")
        scrapers_a_ejecutar = list(scrapers_disponibles.values())

    # El resto del código no cambia
    for scraper_module in scrapers_a_ejecutar:
        try:
            # Usamos __name__ para obtener el nombre del archivo (ej: scrapers.afsformacion_scraper)
            print(f"\n>>> Ejecutando: {scraper_module.__name__}")
            todos_los_cursos.extend(scraper_module.scrape())
        except Exception as e:
            print(f"---! ERROR CRÍTICO en el scraper {scraper_module.__name__}: {e} !---")

    print(f"\nProceso de scraping finalizado. Total de cursos encontrados: {len(todos_los_cursos)}")
    
    if todos_los_cursos:
        print("Insertando y actualizando datos en la base de datos...")
        for curso in todos_los_cursos:
            database.insert_curso(curso)
        print("Datos insertados correctamente.")
    
    print("Exportando resultados a CSV...")
    conn = sqlite3.connect(database.DB_NAME)
    # Seleccionamos solo los cursos scrapeados en esta ejecución
    # Esto es opcional, pero útil para ver solo el resultado del scraper que probaste
    df = pd.read_sql_query("SELECT * FROM cursos ORDER BY last_scraped DESC", conn)
    conn.close()
    
    df.to_csv("cursos_actualizados.csv", index=False)
    print("Exportación finalizada. Revisa el fichero 'cursos_actualizados.csv'")
    print("--- PROCESO COMPLETADO ---")

if __name__ == '__main__':
    main()