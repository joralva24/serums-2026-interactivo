import streamlit as st
import pandas as pd
from streamlit_sortables import sort_items

# 1. CONFIGURACIÓN Y ESTILO PERSONALIZADO (CSS)
st.set_page_config(page_title="SERUMS 2026 - Estrategia", layout="wide", page_icon="🏥")

st.markdown("""
    <style>
    /* Fondo general */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Estilo de los títulos */
    h1 {
        color: #1e3a8a;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800;
    }
    
    /* Tarjetas de Métricas */
    [data-testid="stMetricValue"] {
        color: #1e3a8a;
        background-color: #ffffff;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #3b82f6;
    }

    /* Estilo de la barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    /* Estilo de las tarjetas de ranking (Sortables) */
    .st-sortable-item {
        background: #ffffff !important;
        border-radius: 12px !important;
        padding: 15px !important;
        margin-bottom: 10px !important;
        border: 1px solid #e5e7eb !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        color: #1f2937 !important;
        font-weight: 500 !important;
        cursor: grab !important;
    }
    
    /* Botones principales */
    .stButton>button {
        border-radius: 20px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE DATOS
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

# Inicializar sesión
if 'carrito_plazas' not in st.session_state:
    st.session_state.carrito_plazas = []

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.image("https://www.gob.pe/images/logos/logotipo-gob-pe.png", width=150) # Opcional: Logo institucional
    st.header("🔍 Panel de Control")
    prof_sel = st.multiselect("Profesión:", sorted(df_master['PROFESIÓN'].unique().tolist()))
    dept_sel = st.multiselect("Departamento:", sorted(df_master['DEPARTAMENTO'].unique().tolist()))
    inst_sel = st.multiselect("Institución:", sorted(df_master['INSTITUCIÓN'].unique().tolist()))
    gd_sel = st.multiselect("Grado de Dificultad:", sorted(df_master['GRADO DE DIFICULTAD'].unique().tolist()))
    st.markdown("---")
    st.caption("v2.0 - Desarrollado para Serumistas 2026")

# --- 4. LÓGICA DE FILTRADO ---
df_f = df_master.copy()
if prof_sel: df_f = df_f[df_f['PROFESIÓN'].isin(prof_sel)]
if dept_sel: df_f = df_f[df_f['DEPARTAMENTO'].isin(dept_sel)]
if inst_sel: df_f = df_f[df_f['INSTITUCIÓN'].isin(inst_sel)]
if gd_sel: df_f = df_f[df_f['GRADO DE DIFICULTAD'].isin(gd_sel)]

# --- 5. INTERFAZ PRINCIPAL ---
st.title("🏥 Planificador Estratégico SERUMS")
st.write("Gestiona tus plazas y construye tu ranking oficial de forma visual.")

# Métricas Estilizadas
m1, m2, m3 = st.columns(3)
m1.metric("Establecimientos", len(df_f))
m2.metric("Vacantes Totales", int(df_f['N° PLAZAS'].sum()))
m3.metric("Guardados", len(st.session_state.carrito_plazas))

# Buscador y Tabla
with st.container():
    search = st.text_input("🔍 Buscar por nombre específico:", placeholder="Ej: Puesto de Salud...")
    if search:
        df_f = df_f[df_f['NOMBRE DE ESTABLECIMIENTO'].str.contains(search, case=False, na=False)]
    
    st.markdown("### 📋 Resultados de Búsqueda")
    event = st.dataframe(df_f, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")

# Botón de añadir con estilo
if st.button("✨ Añadir Seleccionados al Ranking", type="primary", use_container_width=True):
    indices = event['selection']['rows']
    if indices:
        nuevas = df_f.iloc[indices].to_dict('records')
        for n in nuevas:
            if n not in st.session_state.carrito_plazas:
                st.session_state.carrito_plazas.append(n)
        st.rerun()

# --- 6. SECCIÓN DE RANKING (TUNEADA) ---
if st.session_state.carrito_plazas:
    st.divider()
    col_rank, col_map = st.columns([1, 1.2])
    
    with col_rank:
        st.subheader("⭐ Mi Ranking de Prioridad")
        st.markdown("_Arrastra las tarjetas para ordenar tus opciones finalistas_")
        
        # Etiquetas estilizadas para las tarjetas
        opciones = [f"📍 {p['NOMBRE DE ESTABLECIMIENTO']} \n\n {p['DEPARTAMENTO']} | GD: {p['GRADO DE DIFICULTAD']}" 
                    for p in st.session_state.carrito_plazas]

        # Componente Draggable
        orden_etiquetas = sort_items(opciones, direction="vertical", key="ranking_visual")

        # Sincronizar orden
        nueva_lista = []
        for etiqueta in orden_etiquetas:
            nombre = etiqueta.split("📍 ")[1].split(" \n\n")[0]
            for p in st.session_state.carrito_plazas:
                if p['NOMBRE DE ESTABLECIMIENTO'] == nombre:
                    nueva_lista.append(p)
                    break
        st.session_state.carrito_plazas = nueva_lista

        # Acciones de la lista
        st.markdown("---")
        c_desc, c_clear = st.columns(2)
        df_final = pd.DataFrame(st.session_state.carrito_plazas)
        csv = df_final.to_csv(index=False).encode('utf-8-sig')
        c_desc.download_button("📥 Descargar Ranking", csv, "mi_ranking.csv", "text/csv")
        if c_clear.button("🗑️ Vaciar Todo"):
            st.session_state.carrito_plazas = []
            st.rerun()

    with col_map:
        st.subheader("🗺️ Vista Geográfica")
        if df_coords is not None:
            df_mapa = pd.merge(df_final, df_coords[['CÓDIGO RENIPRESS', 'lat', 'lon']], on='CÓDIGO RENIPRESS', how='left')
            st.map(df_mapa.dropna(subset=['lat', 'lon']), color="#1e3a8a", size=30)
