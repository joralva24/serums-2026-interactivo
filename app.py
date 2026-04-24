import streamlit as st
import pandas as pd

# 1. ESTILO PROFESIONAL (UI/UX)
st.set_page_config(page_title="SERUMS 2026 | Estrategia", layout="wide", page_icon="🏥")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .main { background-color: #fcfcfd; }
    
    /* Métricas Minimalistas */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #edf2f7;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
    }
    
    /* Tarjetas de Ranking */
    .plaza-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .plaza-info { flex-grow: 1; }
    .plaza-name { color: #1a202c; font-weight: 700; font-size: 1.1rem; }
    .plaza-detail { color: #718096; font-size: 0.9rem; }
    
    /* Botones */
    .stButton>button {
        border-radius: 8px;
        transition: all 0.2s;
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

# Sesión de favoritos
if 'lista_ranking' not in st.session_state:
    st.session_state.lista_ranking = []

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.title("🏥 SERUMS 2026")
    prof_sel = st.multiselect("Profesión", sorted(df_master['PROFESIÓN'].unique()))
    dept_sel = st.multiselect("Departamento", sorted(df_master['DEPARTAMENTO'].unique()))
    inst_sel = st.multiselect("Institución", sorted(df_master['INSTITUCIÓN'].unique()))
    gd_sel = st.multiselect("Dificultad (GD)", sorted(df_master['GRADO DE DIFICULTAD'].unique()))

# --- 4. FILTRADO ---
df_f = df_master.copy()
if prof_sel: df_f = df_f[df_f['PROFESIÓN'].isin(prof_sel)]
if dept_sel: df_f = df_f[df_f['DEPARTAMENTO'].isin(dept_sel)]
if inst_sel: df_f = df_f[df_f['INSTITUCIÓN'].isin(inst_sel)]
if gd_sel: df_f = df_f[df_f['GRADO DE DIFICULTAD'].isin(gd_sel)]

# --- 5. CUERPO PRINCIPAL ---
st.title("Estrategia de Adjudicación")

col1, col2, col3 = st.columns(3)
col1.metric("Establecimientos", len(df_f))
col2.metric("Vacantes", int(df_f['N° PLAZAS'].sum()))
col3.metric("En tu Ranking", len(st.session_state.lista_ranking))

# Tabla de búsqueda
search = st.text_input("🔍 Buscar establecimiento...", placeholder="Nombre del puesto o centro de salud")
if search:
    df_f = df_f[df_f['NOMBRE DE ESTABLECIMIENTO'].str.contains(search, case=False, na=False)]

event = st.dataframe(df_f, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")

if st.button("✨ Guardar selección en mi ranking", type="primary"):
    indices = event['selection']['rows']
    if indices:
        seleccionados = df_f.iloc[indices].to_dict('records')
        for s in seleccionados:
            if s not in st.session_state.lista_ranking:
                st.session_state.lista_ranking.append(s)
        st.rerun()

# --- 6. RANKING PERSONALIZADO (EL "TUNEO") ---
if st.session_state.lista_ranking:
    st.divider()
    st.header("⭐ Mi Prioridad de Postulación")
    
    col_rank, col_mapa = st.columns([1, 1.2])
    
    with col_rank:
        # Dibujamos las tarjetas de ranking
        for i, plaza in enumerate(st.session_state.lista_ranking):
            with st.container():
                # HTML para la tarjeta visual
                st.markdown(f"""
                    <div class="plaza-card">
                        <div class="plaza-info">
                            <div class="plaza-detail">OPCIÓN {i+1}</div>
                            <div class="plaza-name">{plaza['NOMBRE DE ESTABLECIMIENTO']}</div>
                            <div class="plaza-detail">{plaza['DEPARTAMENTO']} • {plaza['PROVINCIA']} • {plaza['GRADO DE DIFICULTAD']}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Botones de control bajo la tarjeta
                b1, b2, b3 = st.columns([1,1,2])
                if b1.button("🔼", key=f"up_{i}") and i > 0:
                    st.session_state.lista_ranking[i], st.session_state.lista_ranking[i-1] = st.session_state.lista_ranking[i-1], st.session_state.lista_ranking[i]
                    st.rerun()
                if b2.button("🔽", key=f"down_{i}") and i < len(st.session_state.lista_ranking)-1:
                    st.session_state.lista_ranking[i], st.session_state.lista_ranking[i+1] = st.session_state.lista_ranking[i+1], st.session_state.lista_ranking[i]
                    st.rerun()
                if b3.button("❌ Quitar", key=f"del_{i}"):
                    st.session_state.lista_ranking.pop(i)
                    st.rerun()
    
    with col_mapa:
        df_rank = pd.DataFrame(st.session_state.lista_ranking)
        if df_coords is not None:
            df_mapa = pd.merge(df_rank, df_coords[['CÓDIGO RENIPRESS', 'lat', 'lon']], on='CÓDIGO RENIPRESS', how='left')
            st.map(df_mapa.dropna(subset=['lat', 'lon']), color="#3b82f6")
        
        st.markdown("### Acciones finales")
        csv = df_rank.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Descargar Ranking Oficial", csv, "mi_serums_2026.csv", "text/csv")
        if st.button("🗑️ Vaciar lista"):
            st.session_state.lista_ranking = []
            st.rerun()
