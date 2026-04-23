
import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="SERUMS 2026 - Estrategia", layout="wide", page_icon="🏥")

# Estilo visual para las métricas
st.markdown("<style>[data-testid='stMetricValue'] {font-size: 28px; color: #007bff;}</style>", unsafe_allow_html=True)

st.title("🏥 Buscador y Planificador SERUMS 2026-I")
st.markdown("Filtra las plazas, selecciona tus favoritas y descarga tu lista de postulación.")

# 2. CARGA DE DATOS
@st.cache_data
def load_data():
    df = pd.read_csv('plazas_serums_2026_limpio.csv')
    df['N° PLAZAS'] = pd.to_numeric(df['N° PLAZAS'], errors='coerce').fillna(0).astype(int)
    return df

df = load_data()

# --- 3. BARRA LATERAL (TODOS TUS FILTROS) ---
st.sidebar.header("⚙️ Filtros de Búsqueda")

# Filtro: Profesión
profesion_sel = st.sidebar.multiselect("1. Profesión:", sorted(df['PROFESIÓN'].unique().tolist()))

# Filtro: Ubicación (Departamento -> Provincia)
depts_disponibles = sorted(df['DEPARTAMENTO'].unique().tolist())
dept_sel = st.sidebar.multiselect("2. Departamento:", depts_disponibles)

if dept_sel:
    prov_disponibles = sorted(df[df['DEPARTAMENTO'].isin(dept_sel)]['PROVINCIA'].unique().tolist())
else:
    prov_disponibles = sorted(df['PROVINCIA'].unique().tolist())
prov_sel = st.sidebar.multiselect("3. Provincia:", prov_disponibles)

# Filtro: Grado de Dificultad
gd_sel = st.sidebar.multiselect("4. Grado de Dificultad (GD):", sorted(df['GRADO DE DIFICULTAD'].unique().tolist()))

# Filtro: Presupuesto
pres_sel = st.sidebar.multiselect("5. Presupuesto:", sorted(df['PRESUPUESTO'].unique().tolist()))

# Filtros de Bonos
st.sidebar.markdown("---")
zaf_filtro = st.sidebar.checkbox("Bono ZAF (Zona Alejada)")
ze_filtro = st.sidebar.checkbox("Bono ZE (VRAEM)")

# --- 4. LÓGICA DE FILTRADO ---
df_f = df.copy()

if profesion_sel:
    df_f = df_f[df_f['PROFESIÓN'].isin(profesion_sel)]
if dept_sel:
    df_f = df_f[df_f['DEPARTAMENTO'].isin(dept_sel)]
if prov_sel:
    df_f = df_f[df_f['PROVINCIA'].isin(prov_sel)]
if gd_sel:
    df_f = df_f[df_f['GRADO DE DIFICULTAD'].isin(gd_sel)]
if pres_sel:
    df_f = df_f[df_f['PRESUPUESTO'].isin(pres_sel)]
if zaf_filtro:
    df_f = df_f[df_f['ZAF (*)'] == 'SI']
if ze_filtro:
    df_f = df_f[df_f['ZE (**)'] == 'SI']

# Buscador de texto
search = st.text_input("🔍 Buscar por Establecimiento o Distrito:", "")
if search:
    df_f = df_f[df_f['NOMBRE DE ESTABLECIMIENTO'].str.contains(search, case=False, na=False) | 
                df_f['DISTRITO'].str.contains(search, case=False, na=False)]

# --- 5. VISUALIZACIÓN Y MÉTRICAS ---
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    st.metric("Establecimientos", len(df_f))
with c2:
    st.metric("Vacantes Totales", int(df_f['N° PLAZAS'].sum()))
with c3:
    csv_todo = df_f.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Descargar búsqueda completa", csv_todo, "busqueda_serums.csv", "text/csv")

# --- 6. TABLA INTERACTIVA ---
st.info("💡 Selecciona las filas en el cuadro de la izquierda para agregarlas a tu 'Lista de Postulación' abajo.")

event = st.dataframe(
    df_f, 
    use_container_width=True, 
    hide_index=True, 
    on_select="rerun", 
    selection_mode="multi-row" # <--- CAMBIO: Ahora con guion medio (-)
)
# --- 7. SECCIÓN DE FAVORITOS ---
indices_seleccionados = event['selection']['rows']

if indices_seleccionados:
    st.divider()
    st.header("⭐ Mi Lista de Postulación (Favoritos)")
    
    # Extraemos solo las filas elegidas
    df_favoritos = df_f.iloc[indices_seleccionados]
    
    st.dataframe(df_favoritos, use_container_width=True, hide_index=True)
    
    # Botón para descargar solo los elegidos
    csv_favs = df_favoritos.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Descargar mi lista de favoritos", csv_favs, "mis_favoritos_serums.csv", "text/csv")
else:
    st.caption("Usa la tabla de arriba para marcar las plazas que más te interesan.")
