import streamlit as st
import pandas as pd
import numpy as np
import joblib
import time
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================

st.set_page_config(
    page_title="MantenIA | Asset Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# ESTILO GLOBAL (TEMA INDUSTRIAL PROFESIONAL - SaaS)
# ============================================================

st.markdown("""
<style>
.stApp { background-color: #020617; color: #F8FAFC; }
[data-testid="stSidebar"] { background-color: #0B0F19; border-right: 1px solid #1E293B; }
[data-testid="stSidebar"] * { color: #94A3B8 !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] div { color: #F8FAFC !important; }
.stButton>button { background-color: #10B981; color: #FFFFFF; font-weight: 600; letter-spacing: 0.5px; border: none; border-radius: 4px; padding: 0.6rem 1.2rem; transition: all 0.3s ease; width: 100%; }
.stButton>button:hover { background-color: #059669; color: #FFFFFF; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25); transform: translateY(-1px); }
.stTextInput>div>div>input, .stTextArea>div>div>textarea { background-color: #0F172A !important; color: #10B981 !important; border: 1px solid #334155 !important; border-radius: 6px; font-family: monospace; }
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus { border-color: #3B82F6 !important; box-shadow: 0 0 0 1px #3B82F6 !important; }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); } 70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); } 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); } }
.status-dot { height: 10px; width: 10px; background-color: #10B981; border-radius: 50%; display: inline-block; margin-right: 8px; animation: pulse 2s infinite; }
.status-dot-warning { height: 10px; width: 10px; background-color: #F59E0B; border-radius: 50%; display: inline-block; margin-right: 8px; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# PANTALLA DE CARGA (BOOT SEQUENCE)
# ============================================================

if "inicio_completo" not in st.session_state:
    pantalla = st.empty()
    with pantalla.container():
        st.write("\n" * 4)
        st.markdown(
            """
            <div style="text-align:center;">
                <div style="font-size:50px; color:#10B981; margin-bottom: 10px; text-shadow: 0 0 20px rgba(16,185,129,0.5);">⚡</div>
                <div style="font-size:36px; font-weight:900; color:#FFFFFF; letter-spacing: 2px;">MANTEN<span style="color:#10B981;">IA</span></div>
                <div style="font-size:12px; color:#64748B; letter-spacing: 3px; margin-top: 5px;">INICIALIZANDO MOTOR DE DIAGNÓSTICO PREDICTIVO...</div>
                <div style="margin-top: 40px; font-family: monospace; color: #10B981; font-size: 14px;">[>] Calibrando sensores...<br>[>] Cargando arquitectura SVM, Naive Bayes y LDA...<br>[>] Estableciendo umbrales de alerta...</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write("")
        barra = st.progress(0)
        for i in range(0, 101, 15):
            time.sleep(0.08)
            barra.progress(i)
        st.markdown("<div style='text-align:center; color:#10B981; font-family:monospace; font-weight:bold;'>[ SISTEMA EN LÍNEA ]</div>", unsafe_allow_html=True)
        time.sleep(0.6)
    pantalla.empty()
    st.session_state.inicio_completo = True
    st.rerun()


# ============================================================
# CARGA DE MODELOS (RESTAURO LDA Y AGREGO SIMULADOR FALLBACK)
# ============================================================

class SimModel:
    def predict(self, X):
        return ["1" if any(k in str(x).lower() for k in ["vibracion", "vibración", "temperatura", "anómalo", "ruido"]) else "0" for x in X]

class SimVectorizer:
    def transform(self, X): return X

@st.cache_resource
def cargar_modelos():
    try:
        vectorizador = joblib.load("vectorizador_prod.pkl")
        modelo_svm = joblib.load("modelo_svm.pkl")
        modelo_nb = joblib.load("modelo_naive_bayes.pkl")
        modelo_lda = joblib.load("modelo_lda_prod.pkl") # <-- RESTAURADO
        return vectorizador, modelo_svm, modelo_nb, modelo_lda, True
    except:
        return SimVectorizer(), SimModel(), SimModel(), None, False

vectorizador, modelo_svm, modelo_nb, modelo_lda, modelos_ok = cargar_modelos()


# ============================================================
# VARIABLES DE SESIÓN (HISTORIAL)
# ============================================================

if "historial" not in st.session_state:
    st.session_state.historial = []


# ============================================================
# BARRA LATERAL (SIDEBAR NAVIGATION)
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div style="font-size:24px; font-weight:900; color:#FFFFFF; margin-bottom: 2px;"><span style="color:#10B981;">⚡</span> MANTEN<span style="color:#10B981;">IA</span></div>
        <div style="color:#64748B; font-size:11px; margin-bottom:35px; letter-spacing: 1px;">ASSET INTELLIGENCE PLATFORM</div>
        """,
        unsafe_allow_html=True
    )

    pagina = st.radio(
        "MÓDULOS DE NAVEGACIÓN",
        [
            "🖥️ Panel de Control",
            "🔍 Diagnóstico de Activos",
            "📂 Ingesta de Datos (CSV)",
            "📋 Registro de Telemetría",
            "ℹ️ Especificaciones"
        ]
    )

    st.markdown("---")
    st.markdown("<div style='font-size:11px; color:#475569; margin-bottom:10px; font-weight:700; letter-spacing:1px;'>ESTADO DE RED NEURAL</div>", unsafe_allow_html=True)

    if modelos_ok:
        st.markdown("<div style='display: flex; align-items: center;'><div class='status-dot'></div><span style='color:#F8FAFC; font-size:13px; font-weight:600;'>🟢 ONLINE - Modelos Activos</span></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='display: flex; align-items: center; background-color: rgba(245,158,11,0.1); padding: 8px; border-radius: 4px; border: 1px solid rgba(245,158,11,0.3);'><div class='status-dot-warning'></div><span style='color:#F59E0B; font-size:12px; font-weight:600;'>MODO SIMULACIÓN (NO PKL)</span></div>", unsafe_allow_html=True)


# ============================================================
# ENCABEZADO PRINCIPAL
# ============================================================

st.markdown(
    """
    <div style="font-size: 28px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.5px;">Manten<span style="color: #10B981;">IA</span></div>
    <div style="font-size: 14px; color: #94A3B8; margin-bottom: 25px;">SISTEMA INTELIGENTE DE MONITOREO Y MANTENIMIENTO PREDICTIVO</div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# MÓDULO 1: DASHBOARD (RESTAURADO CON TEXTOS ORIGINALES)
# ============================================================

if pagina == "🖥️ Panel de Control":

    st.markdown(
        """
        <div style="background-color: #0F172A; border-left: 3px solid #3B82F6; padding: 12px 16px; border-radius: 4px; margin-bottom: 24px; border-top: 1px solid #1E293B; border-right: 1px solid #1E293B; border-bottom: 1px solid #1E293B;">
            <div style="color: #60A5FA; font-size: 12px; font-weight: 700; letter-spacing: 1px; margin-bottom: 4px;">INFO DEL SISTEMA</div>
            <div style="color: #94A3B8; font-size: 13px;">El panel actualmente evalúa registros históricos y anomalías detectadas en los sensores de la planta. Utilice los modelos para predecir alertas de fallos en maquinaria crítica.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    total = len(st.session_state.historial)
    positivos = sum(1 for r in st.session_state.historial if r["clasificacion"] == "Positivo")
    negativos = total - positivos

    col1, col2, col3, col4 = st.columns(4)
    card_css = "background-color: #0F172A; padding: 20px; border-radius: 6px; border: 1px solid #1E293B; position: relative; overflow: hidden; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);"
    lbl_css = "font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px;"
    val_css = "font-size: 32px; font-weight: 800; margin-top: 8px; font-family: monospace;"

    with col1:
        st.markdown(f'<div style="{card_css}"><div style="position:absolute; top:0; left:0; width:100%; height:3px; background-color:#64748B;"></div><div style="{lbl_css}">LECTURAS PROCESADAS</div><div style="{val_css} color: #F8FAFC;">{total}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div style="{card_css}"><div style="position:absolute; top:0; left:0; width:100%; height:3px; background-color:#EF4444;"></div><div style="{lbl_css}">ALERTAS DE FALLO (POS)</div><div style="{val_css} color: #FCA5A5;">{positivos}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div style="{card_css}"><div style="position:absolute; top:0; left:0; width:100%; height:3px; background-color:#10B981;"></div><div style="{lbl_css}">OPERACIÓN NORMAL (NEG)</div><div style="{val_css} color: #6EE7B7;">{negativos}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div style="{card_css}"><div style="position:absolute; top:0; left:0; width:100%; height:3px; background-color:#3B82F6;"></div><div style="{lbl_css}">UPTIME DEL SISTEMA</div><div style="{val_css} color: #93C5FD;">99.9%</div></div>', unsafe_allow_html=True)

    st.markdown("<h3 style='color: #F8FAFC; font-size:18px; margin-top:10px;'>Arquitectura de Predicción</h3>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    pipe_box = "background-color: #0B0F19; padding: 16px; border-radius: 4px; border: 1px solid #1E293B; height: 100%;"
    
    with col1:
        st.markdown(f"<div style='{pipe_box}'><h4 style='color:#10B981; font-size:14px;'>01. 📡 Telemetría</h4><p style='color:#9CA3AF; font-size:12px;'>Ingesta de datos provenientes de sensores de vibración, temperatura y acústica.</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='{pipe_box}'><h4 style='color:#10B981; font-size:14px;'>02. ⚙️ Filtrado</h4><p style='color:#9CA3AF; font-size:12px;'>Limpieza de ruido y vectorización de espectros y logs de mantenimiento.</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div style='{pipe_box}'><h4 style='color:#10B981; font-size:14px;'>03. 🧠 Inferencia IA</h4><p style='color:#9CA3AF; font-size:12px;'>Clasificación de firmas de falla utilizando algoritmos de Machine Learning.</p></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div style='{pipe_box}'><h4 style='color:#10B981; font-size:14px;'>04. 🛠️ Acción</h4><p style='color:#9CA3AF; font-size:12px;'>Emisión de alertas para planificar mantenimiento preventivo y evitar paros.</p></div>", unsafe_allow_html=True)

    # Gráfico Futurista con Plotly agregado para mantener el aspecto SaaS
    st.write("---")
    np.random.seed(int(time.time()))
    tiempos = [datetime.now() - timedelta(minutes=i) for i in range(100, 0, -1)]
    base_vib = np.random.normal(loc=3.5, scale=0.5, size=100)
    base_vib[-15:] = base_vib[-15:] + np.linspace(0, 8, 15) + np.random.normal(0, 1, 15)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tiempos, y=base_vib, mode='lines', line=dict(color='#10B981', width=2), fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.1)', name="Vibración Motor Principal"))
    fig.add_hline(y=9.0, line_dash="dash", line_color="#EF4444", annotation_text="Umbral Crítico (9.0 mm/s)", annotation_position="top left", annotation_font_color="#EF4444")
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,23,42,0.5)', margin=dict(l=0, r=0, t=30, b=0), height=250, xaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B'), yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title="Amplitud RMS (mm/s)"))
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# MÓDULO 2: DIAGNÓSTICO DE ACTIVOS (TEXTOS ORIGINALES)
# ============================================================

elif pagina == "🔍 Diagnóstico de Activos":

    st.markdown("<h3 style='color: #F8FAFC; font-size:20px;'>Diagnóstico Manual de Activo</h3>", unsafe_allow_html=True)

    st.markdown(
        """
        <div style="background-color: #0F172A; border-left: 3px solid #10B981; padding: 12px 16px; border-radius: 4px; margin-bottom: 24px; border: 1px solid #1E293B; border-left-width: 3px;">
            <div style="color: #94A3B8; font-size: 13px;">Ingrese los datos extraídos del PLC o el log de observaciones del sensor. El motor de IA analizará la huella de los datos para predecir un fallo inminente.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    equipo = st.text_input("ID del Activo (Maquinaria)", placeholder="Ej. BC-01 (Banda Clasificadora Principal)")
    texto = st.text_area("Log de Sensores / Síntomas", placeholder="Ejemplo: Pico de vibración anómalo detectado en el rodamiento delantero (15 mm/s). La temperatura del motor principal ascendió a 85°C...", height=120)

    if st.button("⚡ EJECUTAR DIAGNÓSTICO IA"):
        if texto.strip() == "":
            st.warning("⚠️ Requiere input de telemetría o registro para procesar.")
        else:
            with st.spinner('Analizando espectro y logs del activo...'):
                inicio = time.time()
                try:
                    X = vectorizador.transform([texto])
                    pred_svm = modelo_svm.predict(X)[0]
                    pred_nb = modelo_nb.predict(X)[0]
                    time.sleep(0.4) 
                    tiempo = time.time() - inicio

                    def interpretar(valor):
                        valor = str(valor).lower()
                        if valor in ["1", "positivo", "positive", "pos"]: return "Alerta de Falla"
                        return "Operación Normal"

                    resultado_svm = interpretar(pred_svm)
                    resultado_nb = interpretar(pred_nb)
                    estado_real = "Positivo" if resultado_svm == "Alerta de Falla" else "Negativo"

                    st.session_state.historial.append({
                        "equipo": equipo if equipo else "Desconocido",
                        "texto": texto,
                        "clasificacion": estado_real,
                        "modelo": "SVM/NB",
                        "tiempo": round(tiempo, 4)
                    })

                    st.write("")
                    st.success(f"✔️ Diagnóstico completado en {tiempo:.3f} segundos.")

                    col1, col2 = st.columns(2)
                    color_svm = "#EF4444" if resultado_svm == "Alerta de Falla" else "#10B981"
                    color_nb = "#EF4444" if resultado_nb == "Alerta de Falla" else "#10B981"
                    res_box = "background-color: #0F172A; padding: 24px; border-radius: 6px; border: 1px solid #1E293B; text-align: center; margin-top: 10px;"

                    with col1:
                        st.markdown(f'<div style="{res_box}; border-bottom: 4px solid {color_svm};"><div style="font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px; margin-bottom: 12px;">SVM ENGINE (SOPORTE VECTORIAL)</div><div style="font-size: 26px; font-weight: 900; color: {color_svm};">{resultado_svm.upper()}</div></div>', unsafe_allow_html=True)
                    with col2:
                        st.markdown(f'<div style="{res_box}; border-bottom: 4px solid {color_nb};"><div style="font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px; margin-bottom: 12px;">NAIVE BAYES ENGINE</div><div style="font-size: 26px; font-weight: 900; color: {color_nb};">{resultado_nb.upper()}</div></div>', unsafe_allow_html=True)

                except Exception as error:
                    st.error("Ocurrió un error en la inferencia.")
                    st.code(str(error))


# ============================================================
# MÓDULO 3: CSV BATCH (TEXTOS ORIGINALES)
# ============================================================

elif pagina == "📂 Ingesta de Datos (CSV)":

    st.markdown("<h3 style='color: #F8FAFC; font-size:20px;'>Procesamiento en Lote (Batch)</h3>", unsafe_allow_html=True)

    st.markdown(
        """
        <div style="background-color: #0F172A; border-left: 3px solid #F59E0B; padding: 12px 16px; border-radius: 4px; margin-bottom: 24px; border: 1px solid #1E293B; border-left-width: 3px;">
            <div style="color: #94A3B8; font-size: 13px;">Cargue un archivo exportado de su sistema SCADA/IoT. El archivo CSV debe contener una columna llamada <b>texto</b> que incluya los logs históricos del comportamiento de las máquinas.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    archivo = st.file_uploader("📥 Subir archivo de telemetría (CSV)", type=["csv"])

    if archivo:
        try:
            df = pd.read_csv(archivo)
            st.markdown("<h5 style='color: #9CA3AF; font-size:14px;'>Muestra de datos estructurados:</h5>", unsafe_allow_html=True)
            st.dataframe(df.head(), use_container_width=True)

            if "texto" not in df.columns:
                st.error("Error estructural: El CSV no contiene la columna requerida 'texto'.")
            else:
                if st.button("⚡ INICIAR PROCESAMIENTO BATCH"):
                    with st.spinner('Evaluando dataset con modelos de clasificación...'):
                        inicio = time.time()
                        X = vectorizador.transform(df["texto"].fillna("").astype(str))
                        pred_svm = modelo_svm.predict(X)
                        pred_nb = modelo_nb.predict(X)

                        resultado = df.copy()
                        resultado["Diagnóstico_SVM"] = pred_svm
                        resultado["Diagnóstico_NB"] = pred_nb
                        tiempo = time.time() - inicio

                        st.success(f"✔️ {len(df)} registros procesados en {tiempo:.3f} segundos.")
                        st.dataframe(resultado, use_container_width=True)

                        csv = resultado.to_csv(index=False).encode("utf-8")
                        st.download_button("⬇️ Descargar Reporte Predictivo (CSV)", csv, "predicciones_activos_mantenia.csv", "text/csv")

        except Exception as error:
            st.error("Falla en la decodificación del archivo.")
            st.code(str(error))


# ============================================================
# MÓDULO 4: HISTORIAL
# ============================================================

elif pagina == "📋 Registro de Telemetría":

    st.markdown("<h3 style='color: #F8FAFC; font-size:20px;'>Historial de Evaluaciones</h3>", unsafe_allow_html=True)

    if len(st.session_state.historial) == 0:
        st.info("No hay registros en la sesión actual.")
    else:
        historial = pd.DataFrame(st.session_state.historial)
        st.dataframe(historial, use_container_width=True, hide_index=True)
        csv = historial.to_csv(index=False).encode("utf-8")
        st.write("")
        st.download_button("⬇️ Exportar Telemetría", csv, "log_auditoria_mantenia.csv", "text/csv")


# ============================================================
# MÓDULO 5: ACERCA / ESPECIFICACIONES (RESTAURADO CON LDA)
# ============================================================

elif pagina == "ℹ️ Especificaciones":

    st.markdown(
        """
        <div style="background-color: #0F172A; padding: 30px; border-radius: 6px; border: 1px solid #1E293B;">
            <h2 style="color: #10B981; font-size: 22px; margin-bottom: 15px;">MantenIA Asset Intelligence</h2>
            <div style="color: #94A3B8; font-size: 14px; line-height: 1.6; margin-bottom: 20px;"><b>Plataforma IoT y Machine Learning orientada a la confiabilidad industrial.</b><br><br>Esta herramienta está diseñada para ingerir datos de maquinaria rotativa, bandas transportadoras, bombas y motores para identificar anomalías antes de que ocurra una falla catastrófica (Tiempo de inactividad / Downtime).</div>
            <div style="font-size: 14px; font-weight: 700; color: #F8FAFC; margin-bottom: 10px; text-transform: uppercase;">Arquitectura de la Versión 1.0</div>
            <div style="color: #94A3B8; font-size: 13px; margin-bottom: 10px;">Actualmente, el sistema mapea lenguaje técnico, registros de inspectores y firmas vectorizadas de sensores para realizar un diagnóstico binario (Operación Normal vs. Alerta de Falla). Emplea:</div>
            <ul style="color: #CBD5E1; font-size: 13px; line-height: 1.8; margin-bottom: 30px;">
                <li><b>SVM (Máquinas de Vectores de Soporte):</b> Excelente para fronteras de decisión complejas en espacios multidimensionales.</li>
                <li><b>Naive Bayes:</b> Para análisis probabilístico rápido de anomalías históricas.</li>
                <li><b>LDA:</b> Para agrupamiento de tópicos y causas de falla raíz.</li>
            </ul>
            <div style="font-size: 14px; font-weight: 700; color: #F8FAFC; margin-bottom: 10px; text-transform: uppercase;">Roadmap Futuro</div>
            <div style="color: #94A3B8; font-size: 13px; margin-bottom: 10px;">Integración directa con APIs de PLCs (Siemens, Allen-Bradley) y sensores en tiempo real (MQTT). Evaluaciones continuas de:</div>
            <ul style="color: #CBD5E1; font-size: 13px; line-height: 1.8;">
                <li>Frecuencias de vibración (Espectro RMS)</li>
                <li>Termografía y temperatura de rodamientos</li>
                <li>Consumo de amperaje anómalo</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# FOOTER CORPORATIVO
# ============================================================

st.markdown(
    """
    <div style="text-align: center; color: #475569; margin-top: 50px; font-size: 11px; border-top: 1px solid #1E293B; padding-top: 20px; font-weight: 600; letter-spacing: 1px;">
        MANTENIA ASSET INTELLIGENCE V1.0 · PROTEGIENDO LA INDUSTRIA CON IA
    </div>
    """,
    unsafe_allow_html=True
)