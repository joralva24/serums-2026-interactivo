import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="SERUMS 2026 - Ranking Personal", layout="wide", page_icon="📑")

# Estilo para las métricas
st.markdown("<style>[data-testid='stMetricValue'] {font-size: 28px; color: #007bff;}</style>", unsafe_allow_html=True)

# 2. INICIALIZAR EL CARRITO (SESSION STATE)
if 'carrito_plazas' not in st.session_state:
    # Ahora el carrito incluye una columna de 'Prioridad'
    st.session_state.carrito_plazas = pd.DataFrame()

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

# --- 4. BARRA LATERAL (FILTROS) ---
st.sidebar.header("⚙️ Filtros de Búsqueda")
profesion_sel = st.sidebar.multiselect("1. Profesión:", sorted(df_master['PROFESIÓN'].unique().tolist()))
depts_sel = st.sidebar.multiselect("2. Departamento:", sorted(df_master['DEPARTAMENTO'].unique().tolist()))

if depts_sel:
    prov_disponibles = sorted(df_master[df_master['DEPARTAMENTO'].isin(depts_sel)]['PROVINCIA'].unique().tolist())
else:
    prov_disponibles = sorted(df_master['PROVINCIA'].unique().tolist())
prov_sel = st.sidebar.multiselect("3. Provincia:", prov_disponibles)

inst_sel = st.sidebar.multiselect("4. Institución:", sorted(df_master['INSTITUCIÓN'].unique().tolist()))
gd_sel = st.sidebar.multiselect("5. Grado de Dificultad:", sorted(df_master['GRADO DE DIFICULTAD'].unique().tolist()))

# --- 5. LÓGICA DE FILTRADO ---
df_f = df_master.copy()
if profesion_sel: df_f = df_f[df_f['PROFESIÓN'].isin(profesion_sel)]
if depts_sel: df_f = df_f[df_f['DEPARTAMENTO'].isin(depts_sel)]
if prov_sel: df_f = df_f[df_f['PROVINCIA'].isin(prov_sel)]
if inst_sel: df_f = df_f[df_f['INSTITUCIÓN'].isin(inst_sel)]
if gd_sel: df_f = df_f[df_f['GRADO DE DIFICULTAD'].isin(gd_sel)]

# --- 6. INTERFAZ PRINCIPAL ---
st.title("📍 Planificador y Ranking SERUMS 2026-I")

search = st.text_input("🔍 Buscar establecimiento:", "")
if search:
    df_f = df_f[df_f['NOMBRE DE ESTABLECIMIENTO'].str.contains(search, case=False, na=False)]

# Métrica de resultados
st.metric("Plazas encontradas", len(df_f))

# TABLA DE BÚSQUEDA
event = st.dataframe(df_f, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")

# BOTÓN PARA GUARDAR
indices = event['selection']['rows']
if st.button("➕ Añadir a mi Ranking Personal", type="primary"):
    if indices:
        nuevas = df_f.iloc[indices].copy()
        # Inicializamos la prioridad en 999 para que las nuevas vayan al final
        nuevas['Tu Prioridad'] = 999 
        
        # Combinar con lo que ya existe y evitar duplicados
        df_total = pd.concat([st.session_state.carrito_plazas, nuevas]).drop_duplicates(subset=['CÓDIGO RENIPRESS', 'PROFESIÓN'])
        st.session_state.carrito_plazas = df_total
        st.success("Plazas añadidas. Desliza hacia abajo para ordenarlas.")
    else:
        st.warning("Selecciona plazas en la tabla.")

# --- 7. SECCIÓN DE RANKING MANUAL (EDITABLE) ---
if not st.session_state.carrito_plazas.empty:
    st.divider()
    st.header("⭐ Mi Orden de Preferencia")
    st.info("✍️ **Instrucciones:** Haz doble clic en la columna **'Tu Prioridad'** y escribe el orden (1, 2, 3...). La tabla se ordenará sola.")

    # Usamos DATA EDITOR para permitir la edición manual
    df_editable = st.data_editor(
        st.session_state.carrito_plazas.sort_values(by="Tu Prioridad"),
        column_order=("Tu Prioridad", "PROFESIÓN", "DEPARTAMENTO", "PROVINCIA", "NOMBRE DE ESTABLECIMIENTO", "GRADO DE DIFICULTAD"),
        hide_index=True,
        use_container_width=True,
        key="editor_ranking"
    )

    # Actualizar el session_state con los cambios del editor
    st.session_state.carrito_plazas = df_editable

    col_mapa, col_acciones = st.columns([1.5, 1])

    with col_mapa:
        if df_coords is not None:
            df_mapa = pd.merge(df_editable, df_coords[['CÓDIGO RENIPRESS', 'lat', 'lon']], on='CÓDIGO RENIPRESS', how='left')
            st.map(df_mapa.dropna(subset=['lat', 'lon']))

    with col_acciones:
        st.write("### Acciones")
        csv = df_editable.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Descargar mi Ranking Final (CSV)", csv, "mi_ranking_serums.csv", "text/csv")
        
        if st.button("🗑️ Borrar lista"):
            st.session_state.carrito_plazas = pd.DataFrame()
            st.rerun()
