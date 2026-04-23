import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="SERUMS 2026 - Mapa Interactivo", layout="wide", page_icon="📍")

# Estilo para métricas
st.markdown("<style>[data-testid='stMetricValue'] {font-size: 28px; color: #007bff;}</style>", unsafe_allow_html=True)

# 2. FUNCIONES DE CARGA DE DATOS
@st.cache_data
def load_data():
    df = pd.read_csv('plazas_serums_2026_limpio.csv')
    df['N° PLAZAS'] = pd.to_numeric(df['N° PLAZAS'], errors='coerce').fillna(0).astype(int)
    # Estandarizar código RENIPRESS a 8 dígitos
    df['CÓDIGO RENIPRESS'] = df['CÓDIGO RENIPRESS'].astype(str).str.zfill(8)
    return df

@st.cache_data
def load_coords():
    try:
        df_geo = pd.read_csv('coordenadas_renipress.csv')
        df_geo['CÓDIGO RENIPRESS'] = df_geo['CÓDIGO RENIPRESS'].astype(str).str.zfill(8)
        return df_geo
    except FileNotFoundError:
        return None

# Cargar archivos
df = load_data()
df_coords = load_coords()

# --- 3. BARRA LATERAL (FILTROS) ---
st.sidebar.header("⚙️ Filtros de Búsqueda")
profesion_sel = st.sidebar.multiselect("Profesión:", sorted(df['PROFESIÓN'].unique().tolist()))
depts_sel = st.sidebar.multiselect("Departamento:", sorted(df['DEPARTAMENTO'].unique().tolist()))
gd_sel = st.sidebar.multiselect("Grado de Dificultad:", sorted(df['GRADO DE DIFICULTAD'].unique().tolist()))

# Filtros de Bonos
st.sidebar.markdown("---")
zaf_filtro = st.sidebar.checkbox("Solo con Bono ZAF")
ze_filtro = st.sidebar.checkbox("Solo con Bono ZE")

# --- 4. LÓGICA DE FILTRADO ---
df_f = df.copy()
if profesion_sel: df_f = df_f[df_f['PROFESIÓN'].isin(profesion_sel)]
if depts_sel: df_f = df_f[df_f['DEPARTAMENTO'].isin(depts_sel)]
if gd_sel: df_f = df_f[df_f['GRADO DE DIFICULTAD'].isin(gd_sel)]
if zaf_filtro: df_f = df_f[df_f['ZAF (*)'] == 'SI']
if ze_filtro: df_f = df_f[df_f['ZE (**)'] == 'SI']

# --- 5. CUERPO PRINCIPAL ---
st.title("📍 Planificador SERUMS 2026-I")
st.markdown("Busca tus plazas y selecciónalas para verlas en el mapa.")

col1, col2 = st.columns(2)
col1.metric("Establecimientos", len(df_f))
col2.metric("Vacantes Totales", int(df_f['N° PLAZAS'].sum()))

# --- 6. TABLA DE RESULTADOS ---
st.info("💡 Selecciona una o varias filas para activar el mapa y la lista de favoritos.")
event = st.dataframe(
    df_f, 
    use_container_width=True, 
    hide_index=True, 
    on_select="rerun", 
    selection_mode="multi-row"
)

# --- 7. LÓGICA DEL MAPA Y FAVORITOS ---
indices_seleccionados = event['selection']['rows']

if indices_seleccionados:
    df_favs = df_f.iloc[indices_seleccionados].copy()
    
    st.divider()
    
    # Intentar cruzar con coordenadas
    if df_coords is not None:
        # Unimos las plazas seleccionadas con sus coordenadas
        df_mapa = pd.merge(df_favs, df_coords[['CÓDIGO RENIPRESS', 'lat', 'lon']], on='CÓDIGO RENIPRESS', how='left')
        
        # Eliminar las que no tienen coordenadas para no romper el mapa
        df_mapa_clean = df_mapa.dropna(subset=['lat', 'lon'])
        
        if not df_mapa_clean.empty:
            st.subheader("🗺️ Ubicación en el Mapa")
            st.map(df_mapa_clean, size=20)
        else:
            st.warning("⚠️ Las plazas seleccionadas no tienen coordenadas registradas.")
    else:
        st.error("❌ Archivo 'coordenadas_renipress.csv' no encontrado en el servidor.")

    # Lista de favoritos abajo del mapa
    st.subheader("⭐ Mi Lista de Postulación")
    st.dataframe(df_favs, use_container_width=True, hide_index=True)
    
    # Botón de descarga
    csv_favs = df_favs.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Descargar mis favoritos", csv_favs, "mis_favoritos.csv", "text/csv")
else:
    st.caption("Selecciona plazas en la tabla superior para ver el mapa interactivo.")
