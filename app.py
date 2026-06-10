import streamlit as st
import pandas as pd
import datetime
from supabase import create_client

# Configuración de pantalla móvil
st.set_page_config(page_title="Control Financiero", page_icon="💳", layout="centered")

# Inyección de CSS para ocultar menús y optimizar espacio en iPhone
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

# Creación de pestañas móviles
tab1, tab2, tab3, tab4 = st.tabs(["📥 Ingreso Nom.", "📤 Egreso Nom.", "🛒 Gasto Diario", "📊 Resumen"])

# ==========================================
# 1. MENU DE INGRESO NÓMINA (Reactivo)
# ==========================================
with tab1:
    st.subheader("📥 Ingreso de Nómina")
    
    monto_in = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f", key="in_monto")
    fecha_in = st.date_input("Fecha", datetime.date.today(), key="in_fecha")
    descripcion_in = st.text_input("Descripción", placeholder="Ej. Quincena, Bono", key="in_desc")
    tipo_in = st.selectbox("Tipo", ["Efectivo", "Transferencia"], key="in_tipo")
    
    # El menú aparece al instante fuera del formulario
    cuenta_in = None
    if tipo_in == "Transferencia":
        cuenta_in = st.selectbox("Selecciona Cuenta de Destino", ["Santander Nomina", "Banamex Nomina"], key="in_cuenta")
        
    with st.form("form_ingreso_submit", clear_on_submit=True):
        submit_in = st.form_submit_button("Guardar Ingreso")
        
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
# 2. MENU DE EGRESOS NÓMINA (Reactivo)
# ==========================================
with tab2:
    st.subheader("📤 Egreso de Nómina")
    
    monto_eg = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f", key="eg_monto")
    fecha_eg = st.date_input("Fecha", datetime.date.today(), key="eg_fecha")
    descripcion_eg = st.text_input("Descripción", placeholder="Ej. Traspaso, Pago de deuda", key="eg_desc")
    tipo_eg = st.selectbox("Tipo", ["Efectivo", "Transferencia"], key="eg_tipo")
    
    cuenta_eg = None
    if tipo_eg == "Transferencia":
        cuenta_eg = st.selectbox("Selecciona Cuenta de Origen", ["Santander Nomina", "Banamex Debito", "Azteca", "Uala", "Didi"], key="eg_cuenta")
        
    with st.form("form_egreso_submit", clear_on_submit=True):
        submit_eg = st.form_submit_button("Guardar Egreso")
        
    if submit_eg and monto_eg > 0:
        data = {
            "fecha": str(fecha_eg), "tipo_movimiento": "Egreso", "monto": monto_eg,
            "descripcion": descripcion_eg, "metodo": tipo_eg, "cuenta": cuenta_eg
        }
        try:
            supabase.table("nomina").insert(data).execute()
            st.success("Egreso registrado correctamente.")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# ==========================================
# 3. MENU DE GASTOS DIARIOS (Reactivo)
# ==========================================
with tab3:
    st.subheader("🛒 Registro de Gasto Diario")
    
    monto_gd = st.number_input("Monto ($)", min_value=0.0, step=10.0, format="%.2f", key="gd_monto")
    descripcion_gd = st.text_input("Descripción", placeholder="Ej. Comida, Oxxo, Pasajes", key="gd_desc")
    tipo_gd = st.selectbox("Tipo", ["Efectivo", "Tarjeta"], key="gd_tipo")
    
    cuenta_gd = None
    if tipo_gd == "Tarjeta":
        cuenta_gd = st.selectbox("Selecciona Tarjeta", [
            "Didi", "Vexi", "Invex Gold", "Banamex Oro", "Plata", "NU", 
            "Uala", "Klar", "Mercado Pago", "Banamex Clasica", "Santander Debito", "Banamex Debito"
        ], key="gd_cuenta")
        
    with st.form("form_diario_submit", clear_on_submit=True):
        submit_gd = st.form_submit_button("Guardar Gasto Diario")
        
    if submit_gd and monto_gd > 0:
        fecha_auto = str(datetime.date.today())
        data = {
            "fecha": fecha_auto, "monto": monto_gd, "descripcion": descripcion_gd,
            "metodo": tipo_gd, "cuenta": cuenta_gd
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
    
    try:
        res_gastos = supabase.table("gastos_diarios").select("*").execute()
        
        if res_gastos.data:
            df = pd.DataFrame(res_gastos.data)
            
            st.markdown("### 💳 Gastos por Tipo de Pago")
            df_tipo = df.groupby("metodo")["monto"].sum().reset_index()
            st.bar_chart(data=df_tipo, x="metodo", y="monto", color="#262730")
            
            st.markdown("### 📝 Gastos por Descripción")
            df_desc = df.groupby("descripcion")["monto"].sum().reset_index().sort_values(by="monto", ascending=False)
            st.bar_chart(data=df_desc, x="descripcion", y="monto", color="#FF4B4B")
            
            with st.expander("👁️ Ver historial completo de gastos"):
                st.dataframe(df[["fecha", "descripcion", "monto", "metodo", "cuenta"]].sort_values(by="fecha", ascending=False), hide_index=True)
        else:
            st.info("Aún no hay gastos registrados para generar gráficos.")
            
    except Exception as e:
        st.error(f"Error al cargar dashboards: {e}")
