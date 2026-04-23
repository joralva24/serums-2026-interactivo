import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="SERUMS 2026 - Estrategia Pro", layout="wide", page_icon="📍")

# Estilo para las métricas
st.markdown("<style>[data-testid='stMetricValue'] {font-size: 28px; color: #007bff;}</style>", unsafe_allow_html=True)

# 2. CARGA DE DATOS
@st.cache_data
def load_all_data():
    # Cargar Plazas
    df_p = pd.read_csv('plazas_serums_2026_limpio.csv')
    df_p['N° PLAZAS'] = pd.to_numeric(df_p['N° PLAZAS'], errors='coerce').fillna(0).astype(int)
    df_p['CÓDIGO RENIPRESS'] = df_p['CÓDIGO RENIPRESS'].astype(str).str.zfill(8)
    
    # Cargar Coordenadas
    try:
        df_c = pd.read_csv('coordenadas_renipress.csv')
        df_c['CÓDIGO RENIPRESS'] = df_c['CÓDIGO RENIPRESS'].astype(str).str.zfill(8)
    except FileNotFoundError:
        df_c = None
        
    return df_p, df_c

df, df_coords = load_all_data()

# --- 3. BARRA LATERAL (TODOS LOS FILTROS) ---
st.sidebar.header("⚙️ Filtros de Búsqueda")

# 3.1 Profesión
profesion_sel = st.sidebar.multiselect("1. Profesión:", sorted(df['PROFESIÓN'].unique().tolist()))

# 3.2 Ubicación Dinámica (Departamento -> Provincia)
depts_disponibles = sorted(df['DEPARTAMENTO'].unique().tolist())
dept_sel = st.sidebar.multiselect("2. Departamento:", depts_disponibles)

if dept_sel:
    prov_disponibles = sorted(df[df['DEPARTAMENTO'].isin(dept_sel)]['PROVINCIA'].unique().tolist())
else:
    prov_disponibles = sorted(df['PROVINCIA'].unique().tolist())
prov_sel = st.sidebar.multiselect("3. Provincia:", prov_disponibles)

# 3.3 Institución (NUEVO FILTRO)
instituciones = sorted(df['INSTITUCIÓN'].unique().tolist())
inst_sel = st.sidebar.multiselect("4. Institución (MINSA, EsSalud, etc.):", instituciones)

# 3.4 Grado de Dificultad
gd_sel = st.sidebar.multiselect("5. Grado de Dificultad (GD):", sorted(df['GRADO DE DIFICULTAD'].unique().tolist()))

# 3.5 Presupuesto
pres_sel = st.sidebar.multiselect("6. Presupuesto:", sorted(df['PRESUPUESTO'].unique().tolist()))

# 3.6 Bonos
st.sidebar.markdown("---")
zaf_filtro = st.sidebar.checkbox("Solo con Bono ZAF")
ze_filtro = st.sidebar.checkbox("Solo con Bono ZE")

# --- 4. LÓGICA DE FILTRADO ---
df_f = df.copy()

if profesion_sel:
    df_f = df_f[df_f['PROFESIÓN'].isin(profesion_sel)]
if dept_sel:
    df_f = df_f[df_f['DEPARTAMENTO'].isin(dept_sel)]
if prov_sel:
    df_f = df_f[df_f['PROVINCIA'].isin(prov_sel)]
if inst_sel:
    df_f = df_f[df_f['INSTITUCIÓN'].isin(inst_sel)]
if gd_sel:
    df_f = df_f[df_f['GRADO DE DIFICULTAD'].isin(gd_sel)]
if pres_sel:
    df_f = df_f[df_f['PRESUPUESTO'].isin(pres_sel)]
if zaf_filtro:
    df_f = df_f[df_f['ZAF (*)'] == 'SI']
if ze_filtro:
    df_f = df_f[df_f['ZE (**)'] == 'SI']

# --- 5. CUERPO PRINCIPAL ---
st.title("📍 Planificador SERUMS 2026-I")
st.markdown("Encuentra tu plaza ideal cruzando todos los filtros y visualízala en el mapa.")

# Métricas rápidas
c1, c2 = st.columns(2)
c1.metric("Centros de Salud", len(df_f))
c2.metric("Vacantes Totales", int(df_f['N° PLAZAS'].sum()))

# Buscador manual
search = st.text_input("🔍 Buscar por Nombre del Establecimiento o Distrito:", "")
if search:
    df_f = df_f[df_f['NOMBRE DE ESTABLECIMIENTO'].str.contains(search, case=False, na=False) | 
                df_f['DISTRITO'].str.contains(search, case=False, na=False)]

# Tabla interactiva
st.info("💡 Haz clic en el recuadro a la izquierda de las filas para ver el mapa y armar tu lista.")
event = st.dataframe(
    df_f, 
    use_container_width=True, 
    hide_index=True, 
    on_select="rerun", 
    selection_mode="multi-row"
)

# --- 6. MAPA Y FAVORITOS ---
indices_seleccionados = event['selection']['rows']

if indices_seleccionados:
    df_favs = df_f.iloc[indices_seleccionados].copy()
    
    st.divider()
    
    # Mostrar Mapa
    if df_coords is not None:
        df_mapa = pd.merge(df_favs, df_coords[['CÓDIGO RENIPRESS', 'lat', 'lon']], on='CÓDIGO RENIPRESS', how='left')
        df_mapa_clean = df_mapa.dropna(subset=['lat', 'lon'])
        
        if not df_mapa_clean.empty:
            st.subheader("🗺️ Ubicación Geográfica")
            st.map(df_mapa_clean)
        else:
            st.warning("No se encontraron coordenadas para estas plazas.")
            
    # Mostrar Lista de Favoritos
    st.subheader("⭐ Mi Lista Seleccionada")
    st.dataframe(df_favs, use_container_width=True, hide_index=True)
    
    # Descargar Selección
    csv_favs = df_favs.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Descargar mi lista personalizada", csv_favs, "mis_favoritos_serums.csv", "text/csv")
else:
    st.caption("Selecciona plazas para activar el mapa y la lista de favoritos.")
