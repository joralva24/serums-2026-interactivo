import streamlit as st
import pandas as pd

# 1. Configuración de la página
st.set_page_config(page_title="Buscador SERUMS Pro", layout="wide", page_icon="🏥")

# Estilo para mejorar la visualización de métricas
st.markdown("<style>[data-testid='stMetricValue'] {font-size: 28px; color: #007bff;}</style>", unsafe_allow_html=True)

st.title("🏥 Buscador Profesional SERUMS 2026-I")
st.markdown("Utiliza el panel de la izquierda para realizar filtros complejos y encontrar tu plaza ideal.")

# 2. Carga y preparación de datos
@st.cache_data
def load_data():
    # Usamos el archivo limpio que generamos antes
    df = pd.read_csv('plazas_serums_2026_limpio.csv')
    df['N° PLAZAS'] = pd.to_numeric(df['N° PLAZAS'], errors='coerce').fillna(0).astype(int)
    return df

df = load_data()

# --- BARRA LATERAL (FILTROS MAESTROS) ---
st.sidebar.header("⚙️ Panel de Filtros")

# Filtro 1: Profesión
profesion_sel = st.sidebar.multiselect("1. Profesión:", sorted(df['PROFESIÓN'].unique().tolist()))

# Filtro 2: Ubicación Dinámica (Departamento -> Provincia)
depts_disponibles = sorted(df['DEPARTAMENTO'].unique().tolist())
dept_sel = st.sidebar.multiselect("2. Departamento:", depts_disponibles)

# Lógica dinámica para Provincias
if dept_sel:
    prov_disponibles = sorted(df[df['DEPARTAMENTO'].isin(dept_sel)]['PROVINCIA'].unique().tolist())
else:
    prov_disponibles = sorted(df['PROVINCIA'].unique().tolist())
prov_sel = st.sidebar.multiselect("3. Provincia:", prov_disponibles)

# Filtro 3: Grado de Dificultad
gd_disponibles = sorted(df['GRADO DE DIFICULTAD'].unique().tolist())
gd_sel = st.sidebar.multiselect("4. Grado de Dificultad (GD):", gd_disponibles)

# Filtro 4: Presupuesto
pres_disponibles = sorted(df['PRESUPUESTO'].unique().tolist())
pres_sel = st.sidebar.multiselect("5. Tipo de Presupuesto:", pres_disponibles)

# Filtro 5: Bonos
st.sidebar.markdown("---")
st.sidebar.subheader("🎁 Bonificaciones")
zaf_filtro = st.sidebar.checkbox("Solo con Bono ZAF (Zona Alejada)")
ze_filtro = st.sidebar.checkbox("Solo con Bono ZE (VRAEM)")

# --- APLICACIÓN DE FILTROS ---
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

# Buscador de texto global (para nombres de puestos específicos)
search = st.text_input("🔍 Buscar por Nombre de Establecimiento o Distrito:", "")
if search:
    df_f = df_f[
        df_f['NOMBRE DE ESTABLECIMIENTO'].str.contains(search, case=False, na=False) |
        df_f['DISTRITO'].str.contains(search, case=False, na=False)
    ]

# --- VISUALIZACIÓN DE RESULTADOS ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Establecimientos", len(df_f))
with col2:
    st.metric("Vacantes Totales", int(df_f['N° PLAZAS'].sum()))
with col3:
    st.write("") # Espacio
    # Botón de descarga
    csv_data = df_f.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Descargar Excel de esta selección", csv_data, "mi_seleccion_serums.csv", "text/csv")

# Tabla Interactiva Principal
st.dataframe(df_f, use_container_width=True, hide_index=True)

if df_f.empty:
    st.warning("No se encontraron plazas con esos filtros. Intenta ampliar tu búsqueda.")
