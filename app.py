import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN Y DISEÑO (CSS MÁS OSCURO)
st.set_page_config(page_title="SERUMS 2026 | Estrategia", layout="wide", page_icon="🏥")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Fondo más grisáceo para contraste */
    .stApp { background-color: #f1f5f9; }
    
    /* Tarjetas de Métricas con bordes más fuertes */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 2px solid #cbd5e0; /* Gris más oscuro */
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* Tarjetas de Ranking más contrastadas */
    .plaza-card {
        background-color: #ffffff;
        border: 2px solid #94a3b8; /* Gris azulado oscuro */
        padding: 1.2rem;
        border-radius: 10px;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .plaza-name { color: #0f172a; font-weight: 800; font-size: 1.1rem; }
    .plaza-detail { color: #475569; font-size: 0.95rem; font-weight: 500; }
    
    /* Barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #e2e8f0;
        border-right: 2px solid #cbd5e0;
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
    except: df_c = None
    return df_p, df_c

df_master, df_coords = load_all_data()

if 'lista_ranking' not in st.session_state:
    st.session_state.lista_ranking = []

# --- 3. BARRA LATERAL (TODOS LOS FILTROS RECUPERADOS) ---
with st.sidebar:
    st.title("🏥 SERUMS 2026")
    st.subheader("Filtros Maestros")
    
    prof_sel = st.multiselect("1. Profesión", sorted(df_master['PROFESIÓN'].unique()))
    
    # Ubicación Dinámica
    depts = sorted(df_master['DEPARTAMENTO'].unique())
    dept_sel = st.multiselect("2. Departamento", depts)
    
    if dept_sel:
        provs = sorted(df_master[df_master['DEPARTAMENTO'].isin(dept_sel)]['PROVINCIA'].unique())
    else:
        provs = sorted(df_master['PROVINCIA'].unique())
    prov_sel = st.multiselect("3. Provincia", provs)
    
    inst_sel = st.multiselect("4. Institución", sorted(df_master['INSTITUCIÓN'].unique()))
    gd_sel = st.multiselect("5. Grado de Dificultad", sorted(df_master['GRADO DE DIFICULTAD'].unique()))
    pres_sel = st.multiselect("6. Presupuesto", sorted(df_master['PRESUPUESTO'].unique()))
    
    st.markdown("---")
    st.subheader("Bonificaciones")
    zaf_filtro = st.checkbox("Bono ZAF (Zona Alejada)")
    ze_filtro = st.checkbox("Bono ZE (VRAEM)")

# --- 4. LÓGICA DE FILTRADO ---
df_f = df_master.copy()
if prof_sel: df_f = df_f[df_f['PROFESIÓN'].isin(prof_sel)]
if dept_sel: df_f = df_f[df_f['DEPARTAMENTO'].isin(dept_sel)]
if prov_sel: df_f = df_f[df_f['PROVINCIA'].isin(prov_sel)]
if inst_sel: df_f = df_f[df_f['INSTITUCIÓN'].isin(inst_sel)]
if gd_sel: df_f = df_f[df_f['GRADO DE DIFICULTAD'].isin(gd_sel)]
if pres_sel: df_f = df_f[df_f['PRESUPUESTO'].isin(pres_sel)]
if zaf_filtro: df_f = df_f[df_f['ZAF (*)'] == 'SI']
if ze_filtro: df_f = df_f[df_f['ZE (**)'] == 'SI']

# --- 5. CUERPO PRINCIPAL ---
st.title("Estrategia de Adjudicación SERUMS")

c1, c2, c3 = st.columns(3)
c1.metric("Establecimientos", len(df_f))
c2.metric("Vacantes Totales", int(df_f['N° PLAZAS'].sum()))
c3.metric("Mi Ranking", len(st.session_state.lista_ranking))

search = st.text_input("🔍 Buscar por establecimiento o distrito:", placeholder="Ej: Centro de Salud...")
if search:
    df_f = df_f[df_f['NOMBRE DE ESTABLECIMIENTO'].str.contains(search, case=False, na=False) | 
                df_f['DISTRITO'].str.contains(search, case=False, na=False)]

# Tabla Principal
st.info("💡 Selecciona las plazas en el cuadro de la izquierda y presiona el botón para guardarlas.")
event = st.dataframe(df_f, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")

if st.button("✨ Agregar a mi Lista", type="primary", use_container_width=True):
    indices = event['selection']['rows']
    if indices:
        seleccionados = df_f.iloc[indices].to_dict('records')
        for s in seleccionados:
            if s not in st.session_state.lista_ranking:
                st.session_state.lista_ranking.append(s)
        st.rerun()

# --- 6. RANKING PERSONALIZADO ---
if st.session_state.lista_ranking:
    st.divider()
    st.header("⭐ Mi Orden de Prioridad")
    
    col_rank, col_mapa = st.columns([1, 1.2])
    
    with col_rank:
        for i, plaza in enumerate(st.session_state.lista_ranking):
            with st.container():
                st.markdown(f"""
                    <div class="plaza-card">
                        <div class="plaza-name">#{i+1} - {plaza['NOMBRE DE ESTABLECIMIENTO']}</div>
                        <div class="plaza-detail">{plaza['DEPARTAMENTO']} | {plaza['PROVINCIA']} | {plaza['INSTITUCIÓN']}</div>
                        <div class="plaza-detail">Dificultad: {plaza['GRADO DE DIFICULTAD']} | Presupuesto: {plaza['PRESUPUESTO']}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                b1, b2, b3 = st.columns([1, 1, 2])
                if b1.button("+", key=f"up_{i}") and i > 0:
                    st.session_state.lista_ranking[i], st.session_state.lista_ranking[i-1] = st.session_state.lista_ranking[i-1], st.session_state.lista_ranking[i]
                    st.rerun()
                if b2.button("-", key=f"down_{i}") and i < len(st.session_state.lista_ranking)-1:
                    st.session_state.lista_ranking[i], st.session_state.lista_ranking[i+1] = st.session_state.lista_ranking[i+1], st.session_state.lista_ranking[i]
                    st.rerun()
                if b3.button("🗑️ Quitar", key=f"del_{i}"):
                    st.session_state.lista_ranking.pop(i)
                    st.rerun()
    
    with col_mapa:
        df_rank = pd.DataFrame(st.session_state.lista_ranking)
        if df_coords is not None:
            df_mapa = pd.merge(df_rank, df_coords[['CÓDIGO RENIPRESS', 'lat', 'lon']], on='CÓDIGO RENIPRESS', how='left')
            st.map(df_mapa.dropna(subset=['lat', 'lon']), color="#1e40af") # Azul más oscuro para los puntos
        
        st.markdown("### Acciones del Ranking")
        csv = df_rank.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Descargar Ranking Ordenado", csv, "mi_ranking_serums.csv", "text/csv", use_container_width=True)
        if st.button("❌ Vaciar Ranking", use_container_width=True):
            st.session_state.lista_ranking = []
            st.rerun()
