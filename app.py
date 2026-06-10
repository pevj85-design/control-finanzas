import streamlit as st
import pandas as pd
import datetime
from supabase import create_client

# Configuración de pantalla móvil
st.set_page_config(page_title="Control Financiero", page_icon="💳", layout="centered")

# Inyección de CSS para diseño limpio en iPhone
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stTabs [data-baseweb="tab"] {font-size: 14px; padding: 10px 4px;}
    div[data-testid="stForm"] {border: none; padding: 0;}
    </style>
""", unsafe_allow_html=True)

# Conexión a Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Funciones Callback para limpiar los campos de forma segura
def limpiar_ingreso():
    st.session_state["in_monto"] = 0.0
    st.session_state["in_desc"] = ""
    st.session_state["in_tipo"] = "Efectivo"

def limpiar_egreso():
    st.session_state["eg_monto"] = 0.0
    st.session_state["eg_desc"] = ""
    st.session_state["eg_tipo"] = "Efectivo"

def limpiar_diario():
    st.session_state["gd_monto"] = 0.0
    st.session_state["gd_desc"] = ""
    st.session_state["gd_tipo"] = "Efectivo"
    if "gd_plazo" in st.session_state:
        st.session_state["gd_plazo"] = "Una exhibición"

# Creación de pestañas móviles
tab1, tab2, tab3, tab4 = st.tabs(["📥 Ingreso Nom.", "📤 Egreso Nom.", "🛒 Gasto Diario", "📊 Resumen"])

# Lista maestra de tarjetas
TARJETAS_MAESTRAS = [
    "Didi", "Vexi", "Invex Gold", "Banamex Oro", "Plata", "NU", 
    "Uala", "Klar", "Mercado Pago", "Banamex Clasica", "Santander Debito", "Banamex Debito"
]

# ==========================================
# 1. MENU DE INGRESO NÓMINA
# ==========================================
with tab1:
    st.subheader("📥 Ingreso de Nómina")
    
    monto_in = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f", key="in_monto")
    fecha_in = st.date_input("Fecha", datetime.date.today(), key="in_fecha")
    descripcion_in = st.text_input("Descripción", placeholder="Ej. Quincena, Bono", key="in_desc")
    tipo_in = st.selectbox("Tipo", ["Efectivo", "Transferencia"], key="in_tipo")
    
    cuenta_in = None
    if tipo_in == "Transferencia":
        cuenta_in = st.selectbox("Selecciona Cuenta de Destino", ["Santander Nomina", "Banamex Nomina"], key="in_cuenta")
        
    with st.form("form_ingreso_submit", clear_on_submit=True):
        # Usamos on_click para limpiar el estado de forma segura
        submit_in = st.form_submit_button("Guardar Ingreso", on_click=limpiar_ingreso)
        
    if submit_in and monto_in > 0:
        data = {
            "fecha": str(fecha_in), "tipo_movimiento": "Ingreso", "monto": monto_in,
            "descripcion": descripcion_in, "metodo": tipo_in, "cuenta": cuenta_in
        }
        try:
            supabase.table("nomina").insert(data).execute()
            st.success("Ingreso registrado correctamente.")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# ==========================================
# 2. MENU DE EGRESOS NÓMINA
# ==========================================
with tab2:
    st.subheader("📤 Egreso de Nómina")
    
    monto_eg = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f", key="eg_monto")
    fecha_eg = st.date_input("Fecha", datetime.date.today(), key="eg_fecha")
    descripcion_eg = st.text_input("Descripción", placeholder="Ej. Traspaso, Pago", key="eg_desc")
    tipo_eg = st.selectbox("Tipo", ["Efectivo", "Transferencia"], key="eg_tipo")
    
    cuenta_eg = None
    cuenta_dest_eg = None
    if tipo_eg == "Transferencia":
        cuenta_eg = st.selectbox("Selecciona Cuenta de Origen", ["Santander Nomina", "Banamex Debito"], key="eg_cuenta")
        cuenta_dest_eg = st.selectbox("Selecciona Cuenta de Destino", TARJETAS_MAESTRAS + ["Azteca"], key="eg_cuenta_dest")
        
    with st.form("form_egreso_submit", clear_on_submit=True):
        submit_eg = st.form_submit_button("Guardar Egreso", on_click=limpiar_egreso)
        
    if submit_eg and monto_eg > 0:
        data = {
            "fecha": str(fecha_eg), "tipo_movimiento": "Egreso", "monto": monto_eg,
            "descripcion": descripcion_eg, "metodo": tipo_eg, "cuenta": cuenta_eg,
            "cuenta_destino": cuenta_dest_eg
        }
        try:
            supabase.table("nomina").insert(data).execute()
            st.success("Egreso registrado correctamente.")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# ==========================================
# 3. MENU DE GASTOS DIARIOS
# ==========================================
with tab3:
    st.subheader("🛒 Registro de Gasto Diario")
    
    monto_gd = st.number_input("Monto ($)", min_value=0.0, step=10.0, format="%.2f", key="gd_monto")
    descripcion_gd = st.text_input("Descripción", placeholder="Ej. Comida, Compra Amazon", key="gd_desc")
    tipo_gd = st.selectbox("Tipo", ["Efectivo", "Tarjeta"], key="gd_tipo")
    
    cuenta_gd = None
    plazo_gd = "Contado"
    
    if tipo_gd == "Tarjeta":
        cuenta_gd = st.selectbox("Selecciona Tarjeta", TARJETAS_MAESTRAS, key="gd_cuenta")
        plazo_gd = st.selectbox("Plazo de Pago", [
            "Una exhibición", "3 meses", "6 meses", "9 meses", "12 meses", "15 meses", "18 meses", "24 meses"
        ], key="gd_plazo")
        
    with st.form("form_diario_submit", clear_on_submit=True):
        submit_gd = st.form_submit_button("Guardar Gasto Diario", on_click=limpiar_diario)
        
    if submit_gd and monto_gd > 0:
        fecha_auto = str(datetime.date.today())
        data = {
            "fecha": fecha_auto, "monto": monto_gd, "descripcion": descripcion_gd,
            "metodo": tipo_gd, "cuenta": cuenta_gd, "plazo": plazo_gd
        }
        try:
            supabase.table("gastos_diarios").insert(data).execute()
            st.success("Gasto diario guardado.")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# ==========================================
# 4. MENU DE RESUMEN DE GASTOS
# ==========================================
with tab4:
    st.subheader("📊 Resumen y Dashboards")
    
    # --- SECCIÓN DE INGRESOS ---
    st.markdown("### 📥 Resumen de Ingresos Nómina")
    try:
        res_nomina = supabase.table("nomina").select("*").eq("tipo_movimiento", "Ingreso").execute()
        if res_nomina.data:
            df_in = pd.DataFrame(res_nomina.data)
            total_ingresos = df_in["monto"].sum()
            st.metric("Total Ingresos Registrados", f"${total_ingresos:,.2f}")
            
            with st.expander("👁️ Ver Historial de Ingresos"):
                st.dataframe(df_in[["fecha", "descripcion", "monto", "metodo", "cuenta"]].sort_values(by="fecha", ascending=False), hide_index=True)
        else:
            st.info("No hay ingresos de nómina registrados.")
    except Exception as e:
        st.error(f"Error en ingresos: {e}")
        
    st.markdown("---")
    
    # --- SECCIÓN DE GASTOS ---
    st.markdown("### 💳 Análisis de Gastos")
    try:
        res_gastos = supabase.table("gastos_diarios").select("*").execute()
        
        if res_gastos.data:
            df = pd.DataFrame(res_gastos.data)
            
            df_tipo = df.groupby("metodo")["monto"].sum().reset_index()
            st.bar_chart(data=df_tipo, x="metodo", y="monto", color="#262730")
            
            df_desc = df.groupby("descripcion")["monto"].sum().reset_index().sort_values(by="monto", ascending=False)
            st.bar_chart(data=df_desc, x="descripcion", y="monto", color="#FF4B4B")
            
            with st.expander("👁️ Ver Historial Completo de Gastos"):
                st.dataframe(df[["fecha", "descripcion", "monto", "metodo", "cuenta", "plazo"]].sort_values(by="fecha", ascending=False), hide_index=True)
        else:
            st.info("Aún no hay gastos registrados para generar gráficos.")
            
    except Exception as e:
        st.error(f"Error en gastos: {e}")
