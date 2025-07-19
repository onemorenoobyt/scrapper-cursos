# Contenido de app.py
import streamlit as st
import pandas as pd
from datetime import datetime

# --- Configuración de la Página ---
# Esto debe ser lo primero que se ejecuta en el script. Define el título de la pestaña del navegador, el icono y el layout.
st.set_page_config(
    page_title="Cursos SEPE Tenerife",
    page_icon="🎓",
    layout="wide" # 'wide' utiliza todo el ancho de la pantalla, ideal para tablas.
)

# --- Título y Descripción de la App ---
st.title("🎓 Agregador de Cursos SEPE en Tenerife")
st.write("Directorio centralizado y actualizado automáticamente de cursos de formación en Santa Cruz de Tenerife. Falta Eurocampus, CentroFormacionMaster, SomosViernes, Icadepro y Acción Laboral.")

# --- Carga de Datos ---
# @st.cache_data es un "decorador mágico" de Streamlit. Le dice a la app que solo vuelva a cargar el
# fichero CSV si este ha cambiado, lo que hace que la aplicación sea mucho más rápida y eficiente.
@st.cache_data
def load_data():
    """Carga los datos desde el CSV y los prepara para su visualización."""
    try:
        # Leemos el CSV generado por nuestro scraper main.py
        df = pd.read_csv("cursos_actualizados.csv")
        
        # --- Limpieza y Preparación de Datos ---
        # Convertimos las columnas de fecha a un formato de fecha real para poder ordenarlas correctamente.
        # errors='coerce' convierte cualquier valor que no sea una fecha (como 'No disponible') en un espacio vacío (NaT).
        df['fecha_inicio'] = pd.to_datetime(df['fecha_inicio'], errors='coerce')
        df['fecha_fin'] = pd.to_datetime(df['fecha_fin'], errors='coerce')
        
        return df
    except FileNotFoundError:
        # Si el scraper aún no ha creado el fichero, devolvemos una tabla vacía para evitar errores.
        st.error("No se ha encontrado el fichero 'cursos_actualizados.csv'. Ejecuta el scraper (main.py) al menos una vez.")
        return pd.DataFrame()

# Cargamos los datos usando nuestra función cacheada
df = load_data()

# Solo mostramos los filtros y la tabla si el DataFrame no está vacío
if not df.empty:
    # --- Barra Lateral de Filtros ---
    st.sidebar.header("🔍 Filtros")
    
    # Filtro 1: Selección múltiple por Centro de Formación
    centros = sorted(df['centro_formacion'].unique())
    centro_seleccionado = st.sidebar.multiselect(
        "Centro de Formación:",
        options=centros,
        default=centros # Por defecto, todos los centros están seleccionados
    )
    
    # Filtro 2: Búsqueda por texto en el nombre del curso
    nombre_curso_filtro = st.sidebar.text_input("Buscar por nombre del curso:")

    # --- Aplicación de Filtros ---
    # Empezamos con el DataFrame completo y lo vamos reduciendo según los filtros aplicados.
    df_filtrado = df[df['centro_formacion'].isin(centro_seleccionado)]
    
    if nombre_curso_filtro:
        df_filtrado = df_filtrado[df_filtrado['nombre_curso'].str.contains(nombre_curso_filtro, case=False, na=False)]

    # --- Mostrar Resultados en la Página Principal ---
    st.header(f"Resultados Encontrados: {len(df_filtrado)}")
    
    # st.dataframe es la mejor manera de mostrar una tabla en Streamlit.
    # Es interactiva: el usuario puede hacer clic en las cabeceras para ordenar.
    st.dataframe(
        df_filtrado.sort_values(by="fecha_inicio", ascending=False).reset_index(drop=True),
        use_container_width=True, # La tabla usará todo el ancho disponible
        # Configuración para que las fechas se muestren en un formato amigable
        column_config={
            "fecha_inicio": st.column_config.DatetimeColumn("Fecha de Inicio", format="DD/MM/YYYY"),
            "fecha_fin": st.column_config.DatetimeColumn("Fecha de Fin", format="DD/MM/YYYY"),
            "url_curso": st.column_config.LinkColumn("Enlace al Curso", display_text="🔗 Ver Curso")
        },
        # Ocultamos columnas que no son tan relevantes para el usuario final
        hide_index=True,
    )
    
    # --- Pie de Página ---
    st.success(f"Datos actualizados por última vez: {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}")
    st.info("Esta web se actualiza automáticamente. La información es extraída directamente de las webs de los centros de formación.")