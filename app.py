import streamlit as st
import pandas as pd
import datetime
from supabase import create_client

# Configuración de pantalla móvil
st.set_page_config(page_title="Control Financiero", page_icon="💳", layout="centered")

# Inyección de CSS para diseño limpio
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stTabs [data-baseweb="tab"] {font-size: 11px; padding: 10px 2px;}
    div[data-testid="stForm"] {border: none; padding: 0;}
    </style>
""", unsafe_allow_html=True)

# --- SISTEMA DE CONTROL DE ACCESO (USUARIO Y CONTRASEÑA) ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.subheader("🔒 Acceso Restringido")
    user_input = st.text_input("Usuario:")
    password_input = st.text_input("Contraseña:", type="password")
    
    if st.button("Ingresar"):
        if user_input == st.secrets["APP_USER"] and password_input == st.secrets["APP_PASSWORD"]:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")
    st.stop()

# Conexión a Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

CONFIG_TARJETAS = {
    "Banamex Clasica": {"corte": 5, "pago": 27}, "Banamex Oro": {"corte": 5, "pago": 27},
    "Plata": {"corte": 15, "pago": 14}, "Invex Gold": {"corte": 26, "pago": 14},
    "Klar": {"corte": 23, "pago": 2}, "Mercado Pago": {"corte": 27, "pago": 6},
    "NU": {"corte": 24, "pago": 5}, "Uala": {"corte": 30, "pago": 14},
    "Vexi": {"corte": 3, "pago": 17}, "Didi": {"corte": 22, "pago": 7}
}
TARJETAS_MAESTRAS = sorted(list(CONFIG_TARJETAS.keys())) + ["Santander Debito", "Banamex Debito"]
CATEGORIAS_GASTO = ["Centro Comercial", "Tiangiis/Market", "Tienda/Oxxo/K", "Gasolina", "Otros"]

def limpiar_diario():
    st.session_state["gd_monto"] = 0.0
    st.session_state["gd_desc"] = ""

tab1, tab2 = st.tabs(["🛒 Gasto Rápido Test", "📊 Datos"])

with tab1:
    st.subheader("Modo Diagnóstico")
    monto_gd = st.number_input("Monto ($)", min_value=0.0, step=10.0, format="%.2f", key="gd_monto")
    descripcion_gd = st.text_input("Descripción", placeholder="Test", key="gd_desc")
    
    with st.form("form_test", clear_on_submit=True):
        submit_gd = st.form_submit_button("Forzar Guardado", on_click=limpiar_diario)
        
    if submit_gd and monto_gd > 0:
        hoy = datetime.date.today()
        data = {
            "fecha": str(hoy), "monto": monto_gd, "descripcion": descripcion_gd,
            "metodo": "Efectivo", "cuenta": None, "plazo": "Contado",
            "anio_registro": hoy.year, "mes_registro": hoy.month, "categoria": "Otros"
        }
        # Forzar impresión del error directo en la pantalla si Supabase rechaza
        res = supabase.table("gastos_diarios").insert(data).execute()
        st.write("Respuesta cruda de la Base de Datos:", res)
        st.success("¡Comando enviado con éxito!")
        st.rerun()

with tab2:
    st.subheader("Ver registros actuales en Base de Datos")
    try:
        registros = supabase.table("gastos_diarios").select("*").execute()
        st.write(registros.data)
    except Exception as e:
        st.error(f"Fallo al leer datos: {e}")
