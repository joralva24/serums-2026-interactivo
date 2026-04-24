import streamlit as st
import pandas as pd
from streamlit_sortables import sort_items # Librería para arrastrar

# 1. CONFIGURACIÓN
st.set_page_config(page_title="SERUMS 2026 - Ranking Draggable", layout="wide", page_icon="📑")

# 2. INICIALIZAR CARRITO
if 'carrito_plazas' not in st.session_state:
    st.session_state.carrito_plazas = []

# 3. CARGA DE DATOS
@st.cache_data
def load_all_data():
    df_p = pd.read_csv('plazas_serums_2026_limpio.csv')
    df_p['N° PLAZAS'] = pd.to_numeric(df_p['N° PLAZAS'], errors='coerce').fillna(0).astype(int)
    df_p['CÓDIGO RENIPRESS'] = df_p['CÓDIGO RENIPRESS'].astype(str).str.zfill(8)
    
    try:
        df_c = pd.read_csv('coordenadas_renipress.csv')
        df_c['CÓDIGO RENIPRESS'] = df_c['CÓDIGO RENIPRESS'].astype(str).str.zfill(8)
        df_c = df_c.drop_duplicates(subset=['CÓDIGO RENIPRESS'])
    except:
        df_c = None
    return df_p, df_c

df_master, df_coords = load_all_data()

# --- 4. FILTROS LATERALES ---
st.sidebar.header("⚙️ Filtros")
prof_sel = st.sidebar.multiselect("Profesión:", sorted(df_master['PROFESIÓN'].unique().tolist()))
dept_sel = st.sidebar.multiselect("Departamento:", sorted(df_master['DEPARTAMENTO'].unique().tolist()))
inst_sel = st.sidebar.multiselect("Institución:", sorted(df_master['INSTITUCIÓN'].unique().tolist()))
gd_sel = st.sidebar.multiselect("Grado de Dificultad:", sorted(df_master['GRADO DE DIFICULTAD'].unique().tolist()))

# --- 5. LÓGICA DE FILTRADO ---
df_f = df_master.copy()
if prof_sel: df_f = df_f[df_f['PROFESIÓN'].isin(prof_sel)]
if dept_sel: df_f = df_f[df_f['DEPARTAMENTO'].isin(dept_sel)]
if inst_sel: df_f = df_f[df_f['INSTITUCIÓN'].isin(inst_sel)]
if gd_sel: df_f = df_f[df_f['GRADO DE DIFICULTAD'].isin(gd_sel)]

# --- 6. INTERFAZ PRINCIPAL ---
st.title("📍 Planificador SERUMS 2026-I")
st.markdown("Busca tus plazas y arrástralas abajo para crear tu orden de prioridad.")

# Buscador manual
search = st.text_input("🔍 Buscar establecimiento:", "")
if search:
    df_f = df_f[df_f['NOMBRE DE ESTABLECIMIENTO'].str.contains(search, case=False, na=False)]

# Tabla de selección
event = st.dataframe(df_f, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")

# Botón para añadir
indices = event['selection']['rows']
if st.button("➕ Añadir a mi Ranking Personal", type="primary"):
    if indices:
        nuevas = df_f.iloc[indices].to_dict('records')
        for n in nuevas:
            # Evitar duplicados en la lista
            if n not in st.session_state.carrito_plazas:
                st.session_state.carrito_plazas.append(n)
        st.toast("Plazas añadidas al ranking.")
    else:
        st.warning("Selecciona plazas primero.")

# --- 7. RANKING DRAGGABLE (ARRASTRAR Y SOLTAR) ---
if st.session_state.carrito_plazas:
    st.divider()
    st.header("⭐ Mi Ranking de Postulación")
    st.info("🖱️ **Instrucciones:** Arrastra las tarjetas de arriba hacia abajo para definir tu prioridad real.")

    # Preparamos las etiquetas para que sean legibles al arrastrar
    opciones = [f"{i+1}. {p['NOMBRE DE ESTABLECIMIENTO']} ({p['DEPARTAMENTO']} - GD:{p['GRADO DE DIFICULTAD']})" 
                for i, p in enumerate(st.session_state.carrito_plazas)]

    # Componente para ARRASTRAR
    orden_actualizado = sort_items(opciones, direction="vertical", key="ranking_serums")

    # Reordenar nuestra lista interna basada en lo que hizo el usuario
    # Mapeamos el texto de vuelta a los datos originales
    nueva_lista = []
    for item in orden_actualizado:
        # Extraemos el nombre del establecimiento de la etiqueta
        nombre_est = item.split(". ")[1].split(" (")[0]
        # Buscamos la plaza en nuestra lista guardada
        for p in st.session_state.carrito_plazas:
            if p['NOMBRE DE ESTABLECIMIENTO'] == nombre_est:
                nueva_lista.append(p)
                break
    
    st.session_state.carrito_plazas = nueva_lista

    # --- VISUALIZACIÓN FINAL ---
    df_ranking = pd.DataFrame(st.session_state.carrito_plazas)
    
    col_mapa, col_datos = st.columns([1, 1])
    
    with col_datos:
        st.write("### Vista previa del Ranking")
        st.dataframe(df_ranking[['PROFESIÓN', 'DEPARTAMENTO', 'NOMBRE DE ESTABLECIMIENTO', 'GRADO DE DIFICULTAD']], use_container_width=True, hide_index=True)
        
        c_desc, c_clear = st.columns(2)
        with c_desc:
            csv = df_ranking.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Descargar mi Ranking Ordenado", csv, "mi_ranking.csv", "text/csv")
        with c_clear:
            if st.button("🗑️ Borrar lista"):
                st.session_state.carrito_plazas = []
                st.rerun()

    with col_mapa:
        if df_coords is not None:
            df_mapa = pd.merge(df_ranking, df_coords[['CÓDIGO RENIPRESS', 'lat', 'lon']], on='CÓDIGO RENIPRESS', how='left')
            st.map(df_mapa.dropna(subset=['lat', 'lon']))
