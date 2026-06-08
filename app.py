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
    </style>
""", unsafe_allow_html=True)# Conexión a Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Creación de los 4 Menús solicitados mediante pestañas móviles
tab1, tab2, tab3, tab4 = st.tabs(["📥 Ingreso Nom.", "📤 Egreso Nom.", "🛒 Gasto Diario", "📊 Resumen"])

# ==========================================
# 1. MENU DE INGRESO NÓMINA
# ==========================================
with tab1:
    st.subheader("📥 Ingreso de Nómina")
    with st.form("form_ingreso", clear_on_submit=True):
        monto = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f", key="in_monto")
        fecha = st.date_input("Fecha", datetime.date.today(), key="in_fecha")
        descripcion = st.text_input("Descripción", placeholder="Ej. Quincena Orca, Bono", key="in_desc")
        tipo = st.selectbox("Tipo", ["Efectivo", "Transferencia"], key="in_tipo")
        
        # Menú condicional para cuentas de ingreso
        cuenta = None
        if tipo == "Transferencia":
            cuenta = st.selectbox("Selecciona Cuenta de Destino", ["Santander Nomina", "Banamex Nomina"], key="in_cuenta")
            
        submit_in = st.form_submit_button("Guardar Ingreso")
        
    if submit_in and monto > 0:
        data = {
            "fecha": str(fecha), "tipo_movimiento": "Ingreso", "monto": monto,
            "descripcion": descripcion, "metodo": tipo, "cuenta": cuenta
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
    with st.form("form_egreso", clear_on_submit=True):
        monto = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f", key="eg_monto")
        fecha = st.date_input("Fecha", datetime.date.today(), key="eg_fecha")
        descripcion = st.text_input("Descripción", placeholder="Ej. Traspaso, Pago de deuda", key="eg_desc")
        tipo = st.selectbox("Tipo", ["Efectivo", "Transferencia"], key="eg_tipo")
        
        # Menú condicional para cuentas de egreso
        cuenta = None
        if tipo == "Transferencia":
            cuenta = st.selectbox("Selecciona Cuenta de Origen", ["Santander Nomina", "Banamex Debito", "Azteca", "Uala", "Didi"], key="eg_cuenta")
            
        submit_eg = st.form_submit_button("Guardar Egreso")
        
    if submit_eg and monto > 0:
        data = {
            "fecha": str(fecha), "tipo_movimiento": "Egreso", "monto": monto,
            "descripcion": descripcion, "metodo": tipo, "cuenta": cuenta
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
    with st.form("form_diario", clear_on_submit=True):
        monto = st.number_input("Monto ($)", min_value=0.0, step=10.0, format="%.2f", key="gd_monto")
        descripcion = st.text_input("Descripción", placeholder="Ej. Comida, Oxxo, Pasajes", key="gd_desc")
        tipo = st.selectbox("Tipo", ["Efectivo", "Tarjeta"], key="gd_tipo")
        
        # Menú condicional con tu lista completa de tarjetas
        cuenta = None
        if tipo == "Tarjeta":
            cuenta = st.selectbox("Selecciona Tarjeta", [
                "Didi", "Vexi", "Invex Gold", "Banamex Oro", "Plata", "NU", 
                "Uala", "Klar", "Mercado Pago", "Banamex Clasica", "Santander Debito", "Banamex Debito"
            ], key="gd_cuenta")
            
        submit_gd = st.form_submit_button("Guardar Gasto Diario")
        
    if submit_gd and monto > 0:
        # El requerimiento pide fecha automática al guardar
        fecha_auto = str(datetime.date.today())
        data = {
            "fecha": fecha_auto, "monto": monto, "descripcion": descripcion,
            "metodo": tipo, "cuenta": cuenta
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
        # Descargar los datos de gastos diarios para el análisis
        res_gastos = supabase.table("gastos_diarios").select("*").execute()
        
        if res_gastos.data:
            df = pd.DataFrame(res_gastos.data)
            
            # --- DASHBOARD 1: Gastos por Tipo (Efectivo/Tarjeta) ---
            st.markdown("### 💳 Gastos por Tipo de Pago")
            df_tipo = df.groupby("metodo")["monto"].sum().reset_index()
            st.bar_chart(data=df_tipo, x="metodo", y="monto", color="#262730")
            
            # --- DASHBOARD 2: Gastos por Descripción ---
            st.markdown("### 📝 Gastos por Descripción")
            # Agrupamos por descripción para ver en qué conceptos específicos gastas más
            df_desc = df.groupby("descripcion")["monto"].sum().reset_index().sort_values(by="monto", ascending=False)
            st.bar_chart(data=df_desc, x="descripcion", y="monto", color="#FF4B4B")
            
            # Tabla de datos crudos para auditoría visual rápida en el celular
            with st.expander("👁️ Ver historial completo de gastos"):
                st.dataframe(df[["fecha", "descripcion", "monto", "metodo", "cuenta"]].sort_values(by="fecha", ascending=False), hide_index=True)
        else:
            st.info("Aún no hay gastos registrados para generar gráficos.")
            
    except Exception as e:
        st.error(f"Error al cargar dashboards: {e}")
