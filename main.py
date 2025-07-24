# Contenido de main.py (VERSIÓN FINAL CON ACTUALIZACIÓN PARCIAL)
import pandas as pd
import sqlite3
import database
import sys
from datetime import datetime
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
    scrape_start_time = datetime.now()
    print(f"--- INICIANDO PROCESO DE SCRAPING a las {scrape_start_time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    database.setup_database()
    
    todos_los_cursos = []
    
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
    
    scraper_a_ejecutar_nombre = None
    if len(sys.argv) > 1:
        scraper_a_ejecutar_nombre = sys.argv[1]

    if scraper_a_ejecutar_nombre:
        print(f"--- MODO DEPURACIÓN: Ejecutando únicamente el scraper '{scraper_a_ejecutar_nombre}' ---")
        scraper_module = scrapers_disponibles.get(scraper_a_ejecutar_nombre)
        if scraper_module:
            scrapers_a_ejecutar = [scraper_module]
        else:
            print(f"---! ERROR: El scraper '{scraper_a_ejecutar_nombre}' no existe. Scrapers disponibles: {list(scrapers_disponibles.keys())} !---")
            return
    else:
        print("--- MODO NORMAL: Ejecutando todos los scrapers ---")
        scrapers_a_ejecutar = list(scrapers_disponibles.values())
    
    successful_centers = set()

    for scraper_module in scrapers_a_ejecutar:
        cursos_del_scraper = []
        try:
            print(f"\n>>> Ejecutando: {scraper_module.__name__}")
            cursos_del_scraper = scraper_module.scrape()
            todos_los_cursos.extend(cursos_del_scraper)
            
            if cursos_del_scraper:
                center_name = cursos_del_scraper[0]['centro']
                successful_centers.add(center_name)
        except Exception as e:
            print(f"---! ERROR CRÍTICO en el scraper {scraper_module.__name__}: {e} !---")

    print(f"\nProceso de scraping finalizado. Total de cursos nuevos/actualizados en esta ejecución: {len(todos_los_cursos)}")
    
    if todos_los_cursos:
        print("Insertando y actualizando datos en la base de datos...")
        for curso in todos_los_cursos:
            database.insert_curso(curso)
        print("Datos insertados correctamente.")
    
    # --- LÓGICA DE PURGA ---
    # Si estamos en modo normal, purgamos los cursos antiguos de los centros que funcionaron.
    # Si estamos en modo depuración, TAMBIÉN purgamos, pero solo para el centro que hemos ejecutado.
    if successful_centers:
        print("\nIniciando purga de cursos antiguos de los centros scrapeados con éxito...")
        database.purge_old_courses_by_center(successful_centers, scrape_start_time)
    
    print("\nExportando la base de datos completa a CSV...")
    conn = sqlite3.connect(database.DB_NAME)
    df = pd.read_sql_query("SELECT * FROM cursos ORDER BY fecha_inicio DESC", conn)
    conn.close()

    if not df.empty:
        df.to_csv("cursos_actualizados.csv", index=False)
        print("Exportación finalizada. Revisa el fichero 'cursos_actualizados.csv'")
    else:
        print("La base de datos está vacía. No se ha generado el CSV.")

    print("--- PROCESO COMPLETADO ---")

if __name__ == '__main__':
    main()