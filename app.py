import streamlit as st
import pandas as pd
from datetime import datetime
import zoneinfo
from supabase import create_client

# Configuración de pantalla móvil
st.set_page_config(page_title="Control Financiero", page_icon="💳", layout="centered")

# Inyección de CSS para diseño limpio en iPhone
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stTabs [data-baseweb="tab"] {font-size: 11px; padding: 10px 2px;}
    </style>
""", unsafe_allow_html=True)

# Función para obtener la fecha y hora exacta de México
def obtener_fecha_mexico():
    zona_mx = zoneinfo.ZoneInfo("America/Mexico_City")
    return datetime.now(zona_mx)

# --- SISTEMA DE CONTROL DE ACCESO ---
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
CATEGORIAS_GASTO = ["Centro Comercial", "Tiangiis/Mercado", "Tienda/Oxxo/K", "Gasolina", "Otros"]

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📥 Ingreso", "📤 Egreso", "🛒 Gasto", "📊 Resumen", "📆 Tarjetas"])

# ==========================================
# 1. MENU DE INGRESO NÓMINA
# ==========================================
with tab1:
    st.subheader("📥 Ingreso de Nómina")
    monto_in = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f", key="in_monto")
    fecha_in = st.date_input("Fecha", obtener_fecha_mexico().date(), key="in_fecha")
    descripcion_in = st.text_input("Descripción", placeholder="Ej. Quincena", key="in_desc")
    tipo_in = st.selectbox("Tipo", ["Efectivo", "Transferencia"], key="in_tipo")
    
    cuenta_in = None
    if tipo_in == "Transferencia":
        cuenta_in = st.selectbox("Selecciona Cuenta de Destino", ["Santander Nomina", "Banamex Nomina"], key="in_cuenta")
        
    if st.button("Guardar Ingreso", key="btn_ingreso"):
        if monto_in > 0:
            data = {"fecha": str(fecha_in), "tipo_movimiento": "Ingreso", "monto": monto_in, "descripcion": descripcion_in, "metodo": tipo_in, "cuenta": cuenta_in}
            try:
                supabase.table("nomina").insert(data).execute()
                st.success("¡Ingreso guardado!")
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")

# ==========================================
# 2. MENU DE EGRESOS NÓMINA
# ==========================================
with tab2:
    st.subheader("📤 Egreso de Nómina")
    monto_eg = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f", key="eg_monto")
    fecha_eg = st.date_input("Fecha", obtener_fecha_mexico().date(), key="eg_fecha")
    descripcion_eg = st.text_input("Descripción", placeholder="Ej. Pago", key="eg_desc")
    tipo_eg = st.selectbox("Tipo", ["Efectivo", "Transferencia"], key="eg_tipo")
    
    cuenta_eg = None
    cuenta_dest_eg = None
    if tipo_eg == "Transferencia":
        cuenta_eg = st.selectbox("Selecciona Cuenta de Origen", ["Santander Nomina", "Banamex Debito"], key="eg_cuenta")
        cuenta_dest_eg = st.selectbox("Selecciona Cuenta de Destino", TARJETAS_MAESTRAS + ["Azteca"], key="eg_cuenta_dest")
        
    if st.button("Guardar Egreso", key="btn_egreso"):
        if monto_eg > 0:
            data = {"fecha": str(fecha_eg), "tipo_movimiento": "Egreso", "monto": monto_eg, "descripcion": descripcion_eg, "metodo": tipo_eg, "cuenta": cuenta_eg, "cuenta_destino": cuenta_dest_eg}
            try:
                supabase.table("nomina").insert(data).execute()
                st.success("¡Egreso guardado!")
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")

# ==========================================
# 3. MENU DE GASTOS DIARIOS
# ==========================================
with tab3:
    st.subheader("🛒 Registro de Gasto Diario")
    monto_gd = st.number_input("Monto ($)", min_value=0.0, step=10.0, format="%.2f", key="gd_monto")
    categoria_gd = st.selectbox("Categoría", CATEGORIAS_GASTO, key="gd_cat")
    descripcion_gd = st.text_input("Detalle/Notas", placeholder="Ej. Mandado", key="gd_desc")
    tipo_gd = st.selectbox("Tipo", ["Efectivo", "Tarjeta"], key="gd_tipo")
    
    cuenta_gd = None
    plazo_gd = "Contado"
    if tipo_gd == "Tarjeta":
        cuenta_gd = st.selectbox("Selecciona Tarjeta", TARJETAS_MAESTRAS, key="gd_cuenta")
        if cuenta_gd not in ["Santander Debito", "Banamex Debito"]:
            plazo_gd = st.selectbox("Plazo de Pago", ["Una exhibición", "3 meses", "6 meses", "12 meses"], key="gd_plazo")
        
    if st.button("Guardar Gasto Diario", key="btn_gasto"):
        if monto_gd > 0:
            tiempo_mx = obtener_fecha_mexico()
            desc_final = descripcion_gd if descripcion_gd.strip() != "" else categoria_gd
            data = {
                "fecha": str(tiempo_mx.date()), "monto": monto_gd, "descripcion": desc_final, "categoria": categoria_gd, "metodo": tipo_gd, "cuenta": cuenta_gd, "plazo": plazo_gd,
                "anio_registro": int(tiempo_mx.year), "mes_registro": int(tiempo_mx.month)
            }
            try:
                supabase.table("gastos_diarios").insert(data).execute()
                st.success("¡Gasto guardado!")
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")

# ==========================================
# 4. MENU DE RESUMEN (DIAGNÓSTICO FORZADO)
# ==========================================
with tab4:
    st.subheader("📊 Vista Cruda de la Base de Datos")
    
    st.markdown("### Tabla: `nomina`")
    res_nom = supabase.table("nomina").select("*").execute()
    if res_nom.data:
        st.dataframe(pd.DataFrame(res_nom.data))
    else:
        st.info("La tabla 'nomina' reporta cero renglones en Supabase.")
        
    st.markdown("---")
    st.markdown("### Tabla: `gastos_diarios`")
    res_gas = supabase.table("gastos_diarios").select("*").execute()
    if res_gas.data:
        st.dataframe(pd.DataFrame(res_gas.data))
    else:
        st.info("La tabla 'gastos_diarios' reporta cero renglones en Supabase.")

# ==========================================
# 5. MENU: AGENDA DE TARJETAS
# ==========================================
with tab5:
    st.subheader("📆 Saldos y Pagos")
    res_tar = supabase.table("gastos_diarios").select("*").eq("metodo", "Tarjeta").execute()
    if res_tar.data:
        st.dataframe(pd.DataFrame(res_tar.data))
    else:
        st.info("No hay consumos con tarjeta detectados.")
