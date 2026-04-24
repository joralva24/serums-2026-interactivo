import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="SERUMS 2026 - Estrategia Pro", layout="wide", page_icon="📍")

# Estilo para las métricas
st.markdown("<style>[data-testid='stMetricValue'] {font-size: 28px; color: #007bff;}</style>", unsafe_allow_html=True)

# 2. INICIALIZAR EL "CARRITO" DE FAVORITOS (SESSION STATE)
# Esto es lo que permite que los favoritos no se borren al filtrar
if 'carrito_plazas' not in st.session_state:
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

# --- 5. LÓGICA DE FILTRADO Y ORDENAMIENTO ---
df_f = df_master.copy()

if profesion_sel: df_f = df_f[df_f['PROFESIÓN'].isin(profesion_sel)]
if depts_sel: df_f = df_f[df_f['DEPARTAMENTO'].isin(depts_sel)]
if prov_sel: df_f = df_f[df_f['PROVINCIA'].isin(prov_sel)]
if inst_sel: df_f = df_f[df_f['INSTITUCIÓN'].isin(inst_sel)]
if gd_sel: df_f = df_f[df_f['GRADO DE DIFICULTAD'].isin(gd_sel)]

# BUSCADOR Y ORDENAMIENTO
st.title("📍 Planificador SERUMS 2026-I")

col_search, col_sort = st.columns([2, 1])
with col_search:
    search = st.text_input("🔍 Buscar por Establecimiento o Distrito:", "")
with col_sort:
    # NUEVA FUNCIÓN: Ordenar resultados
    sort_by = st.selectbox("⬇️ Ordenar resultados por:", ["Sin orden", "Grado de Dificultad", "Departamento", "Institución"])

if search:
    df_f = df_f[df_f['NOMBRE DE ESTABLECIMIENTO'].str.contains(search, case=False, na=False) | 
                df_f['DISTRITO'].str.contains(search, case=False, na=False)]

if sort_by != "Sin orden":
    df_f = df_f.sort_values(by=sort_by)

# MÉTRICAS
c1, c2 = st.columns(2)
c1.metric("Resultados", len(df_f))
c2.metric("Vacantes", int(df_f['N° PLAZAS'].sum()))

# --- 6. TABLA INTERACTIVA CON "GUARDADO" ---
st.info("💡 Selecciona las plazas y haz clic en 'Añadir a mi lista' para que no se borren.")

# Mostrar tabla con selección
event = st.dataframe(df_f, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")

# BOTÓN PARA AGREGAR AL CARRITO
indices_seleccionados = event['selection']['rows']
if st.button("➕ Añadir seleccionados a mi lista permanente", type="primary"):
    if indices_seleccionados:
        nuevas_plazas = df_f.iloc[indices_seleccionados]
        # Concatenamos y eliminamos duplicados por RENIPRESS y Profesión
        st.session_state.carrito_plazas = pd.concat([st.session_state.carrito_plazas, nuevas_plazas]).drop_duplicates(subset=['CÓDIGO RENIPRESS', 'PROFESIÓN'])
        st.toast(f"Se añadieron {len(nuevas_plazas)} plazas a tu lista.")
    else:
        st.warning("Primero selecciona filas en la tabla.")

# --- 7. SECCIÓN PERMANENTE (FAVORITOS Y MAPA) ---
if not st.session_state.carrito_plazas.empty:
    st.divider()
    st.header("⭐ Mi Lista de Postulación")
    
    col_favs, col_map = st.columns([1, 1])
    
    with col_favs:
        st.write("Estas plazas están guardadas, aunque cambies los filtros:")
        st.dataframe(st.session_state.carrito_plazas, use_container_width=True, hide_index=True)
        
        # Botones de acción para el carrito
        c_desc, c_clear = st.columns(2)
        with c_desc:
            csv = st.session_state.carrito_plazas.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Descargar mi lista", csv, "mi_serums_2026.csv", "text/csv")
        with c_clear:
            if st.button("🗑️ Borrar toda mi lista"):
                st.session_state.carrito_plazas = pd.DataFrame()
                st.rerun()

    with col_map:
        if df_coords is not None:
            df_mapa = pd.merge(st.session_state.carrito_plazas, df_coords[['CÓDIGO RENIPRESS', 'lat', 'lon']], on='CÓDIGO RENIPRESS', how='left')
            df_mapa = df_mapa.dropna(subset=['lat', 'lon'])
            if not df_mapa.empty:
                st.subheader("🗺️ Mapa de tu Selección")
                st.map(df_mapa)
