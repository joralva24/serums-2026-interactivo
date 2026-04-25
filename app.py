import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN Y FIX PARA DARK MODE (FORZAR CONTRASTE)
st.set_page_config(page_title="SERUMS 2026 | Estrategia", layout="wide", page_icon="🏥")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* FIX DARK MODE: Forzamos colores para que no se rompa la visibilidad */
    .stApp { background-color: #f1f5f9 !important; }
    
    /* Forzamos que los textos de las métricas y tarjetas sean siempre oscuros */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"], .plaza-name, .plaza-detail {
        color: #0f172a !important; 
    }

    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 2px solid #cbd5e0 !important;
        padding: 20px;
        border-radius: 12px;
    }
    
    .plaza-card {
        background-color: #ffffff !important;
        border: 2px solid #94a3b8 !important;
        padding: 1.2rem;
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }

    /* Ajuste de la barra lateral para que no se vea 'sucia' en dark mode */
    section[data-testid="stSidebar"] {
        background-color: #e2e8f0 !important;
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

# --- 3. BARRA LATERAL (FILTROS COMPLETOS) ---
with st.sidebar:
    st.title("🏥 SERUMS 2026")
    st.subheader("Filtros Maestros")
    
    prof_sel = st.multiselect("1. Profesión", sorted(df_master['PROFESIÓN'].unique()))
    
    dept_sel = st.multiselect("2. Departamento", sorted(df_master['DEPARTAMENTO'].unique()))
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

    # --- SECCIÓN DE DONACIONES (SUTIL) ---
    st.markdown("---")
    st.markdown("### ❤️ Apoya el proyecto")
    st.markdown("Si esta herramienta te sirvió, puedes invitarme un café vía **Yape**.")
    st.code("941760539", language=None) # AQUÍ PON TU NÚMERO REAL
    st.caption("¡Éxitos en tu adjudicación!")

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

search = st.text_input("🔍 Buscar por establecimiento:", placeholder="Ej: Puesto de Salud...")
if search:
    df_f = df_f[df_f['NOMBRE DE ESTABLECIMIENTO'].str.contains(search, case=False, na=False)]

event = st.dataframe(df_f, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")

if st.button("✨ Guardar selección en mi ranking", type="primary", use_container_width=True):
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
                        <div class="plaza-detail">{plaza['DEPARTAMENTO']} | {plaza['PROVINCIA']} | GD: {plaza['GRADO DE DIFICULTAD']}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                b1, b2, b3 = st.columns([1, 1, 2])
                if b1.button("🔼", key=f"up_{i}"):
                    if i > 0:
                        st.session_state.lista_ranking[i], st.session_state.lista_ranking[i-1] = st.session_state.lista_ranking[i-1], st.session_state.lista_ranking[i]
                        st.rerun()
                if b2.button("🔽", key=f"down_{i}"):
                    if i < len(st.session_state.lista_ranking)-1:
                        st.session_state.lista_ranking[i], st.session_state.lista_ranking[i+1] = st.session_state.lista_ranking[i+1], st.session_state.lista_ranking[i]
                        st.rerun()
                if b3.button("🗑️ Quitar", key=f"del_{i}"):
                    st.session_state.lista_ranking.pop(i)
                    st.rerun()
    
    with col_mapa:
        df_rank = pd.DataFrame(st.session_state.lista_ranking)
        if df_coords is not None:
            df_mapa = pd.merge(df_rank, df_coords[['CÓDIGO RENIPRESS', 'lat', 'lon']], on='CÓDIGO RENIPRESS', how='left')
            st.map(df_mapa.dropna(subset=['lat', 'lon']), color="#1e40af")
        
        st.markdown("### Acciones")
        csv = df_rank.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Descargar mi Ranking", csv, "mi_ranking_serums.csv", "text/csv", use_container_width=True)
