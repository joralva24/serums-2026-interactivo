import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="SERUMS 2026 - Estrategia Pro", layout="wide", page_icon="📍")

# Estilo para las métricas
st.markdown("<style>[data-testid='stMetricValue'] {font-size: 28px; color: #007bff;}</style>", unsafe_allow_html=True)

# 2. INICIALIZAR EL "CARRITO" DE FAVORITOS (SESSION STATE)
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

# --- 4. BARRA LATERAL (FILTROS DE BÚSQUEDA) ---
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
st.title("📍 Planificador SERUMS 2026-I")

search = st.text_input("🔍 Buscar en resultados (Establecimiento o Distrito):", "")
if search:
    df_f = df_f[df_f['NOMBRE DE ESTABLECIMIENTO'].str.contains(search, case=False, na=False) | 
                df_f['DISTRITO'].str.contains(search, case=False, na=False)]

# MÉTRICAS
c1, c2 = st.columns(2)
c1.metric("Resultados Filtrados", len(df_f))
c2.metric("Vacantes en esta vista", int(df_f['N° PLAZAS'].sum()))

# TABLA DE BÚSQUEDA
st.write("Selecciona las plazas que quieras guardar:")
event = st.dataframe(df_f, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")

# BOTÓN PARA GUARDAR
indices_seleccionados = event['selection']['rows']
if st.button("➕ Añadir seleccionados a mi lista personal", type="primary"):
    if indices_seleccionados:
        nuevas = df_f.iloc[indices_seleccionados]
        st.session_state.carrito_plazas = pd.concat([st.session_state.carrito_plazas, nuevas]).drop_duplicates(subset=['CÓDIGO RENIPRESS', 'PROFESIÓN'])
        st.success(f"Añadiste {len(nuevas)} plazas.")
    else:
        st.warning("Selecciona al menos una fila primero.")

# --- 7. SECCIÓN DE FAVORITOS (CON ORDENAMIENTO PROPIO) ---
if not st.session_state.carrito_plazas.empty:
    st.divider()
    st.header("⭐ Mi Lista de Postulación")
    
    # NUEVA FUNCIÓN: Ordenar dentro de los seleccionados
    sort_favs = st.selectbox(
        "⬇️ Ordenar mi lista por:", 
        ["Seleccionar orden...", "Grado de Dificultad (Mayor a Menor)", "Grado de Dificultad (Menor a Mayor)", "Departamento", "Institución"]
    )
    
    df_mostrar_favs = st.session_state.carrito_plazas.copy()
    
    if sort_favs == "Grado de Dificultad (Mayor a Menor)":
        df_mostrar_favs = df_mostrar_favs.sort_values(by="GRADO DE DIFICULTAD", ascending=False)
    elif sort_favs == "Grado de Dificultad (Menor a Mayor)":
        df_mostrar_favs = df_mostrar_favs.sort_values(by="GRADO DE DIFICULTAD", ascending=True)
    elif sort_favs == "Departamento":
        df_mostrar_favs = df_mostrar_favs.sort_values(by="DEPARTAMENTO")
    elif sort_favs == "Institución":
        df_mostrar_favs = df_mostrar_favs.sort_values(by="INSTITUCIÓN")

    col_tabla, col_mapa = st.columns([1.2, 1])
    
    with col_tabla:
        st.dataframe(df_mostrar_favs, use_container_width=True, hide_index=True)
        
        c_desc, c_clear = st.columns(2)
        with c_desc:
            csv = df_mostrar_favs.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Descargar mi lista ordenada", csv, "mi_serums_2026.csv", "text/csv")
        with c_clear:
            if st.button("🗑️ Vaciar mi lista"):
                st.session_state.carrito_plazas = pd.DataFrame()
                st.rerun()

    with col_mapa:
        if df_coords is not None:
            df_mapa = pd.merge(df_mostrar_favs, df_coords[['CÓDIGO RENIPRESS', 'lat', 'lon']], on='CÓDIGO RENIPRESS', how='left')
            df_mapa = df_mapa.dropna(subset=['lat', 'lon'])
            if not df_mapa.empty:
                st.map(df_mapa)
