# Contenido de main.py
import pandas as pd
import sqlite3
import database
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
    scrapers_a_ejecutar = [
        afsformacion_scraper, auraformacion_scraper, cep_scraper,
        focan_scraper, grupolincea_scraper, icse_scraper, inpsi_scraper,
        insforca_scraper, microsistemas_scraper, formacionline_scraper
    ]
    
    for scraper_module in scrapers_a_ejecutar:
        try:
            todos_los_cursos.extend(scraper_module.scrape())
        except Exception as e:
            print(f"---! ERROR CRÍTICO en el scraper {scraper_module.__name__}: {e} !---")

    print(f"\nProceso de scraping finalizado. Total de cursos encontrados: {len(todos_los_cursos)}")
    
    print("Insertando y actualizando datos en la base de datos...")
    for curso in todos_los_cursos:
        database.insert_curso(curso)
    print("Datos insertados correctamente.")
    
    print("Exportando resultados a CSV...")
    conn = sqlite3.connect(database.DB_NAME)
    df = pd.read_sql_query("SELECT * FROM cursos ORDER BY fecha_inicio", conn)
    conn.close()
    
    df.to_csv("cursos_actualizados.csv", index=False)
    print("Exportación finalizada. Revisa el fichero 'cursos_actualizados.csv'")
    print("--- PROCESO COMPLETADO ---")

if __name__ == '__main__':
    main()