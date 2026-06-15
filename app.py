import streamlit as st
import pandas as pd
import datetime
from supabase import create_client

# Configuración de pantalla
st.set_page_config(page_title="Control Financiero", page_icon="💳", layout="centered")

# Inyección de CSS para diseño limpio
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stTabs [data-baseweb="tab"] {font-size: 11px; padding: 10px 2px;}
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

# Configuración Maestra de tus Tarjetas
CONFIG_TARJETAS = {
    "Banamex Clasica": {"corte": 5, "pago": 27},
    "Banamex Oro": {"corte": 5, "pago": 27},
    "Plata": {"corte": 15, "pago": 14},
    "Invex Gold": {"corte": 26, "pago": 14},
    "Klar": {"corte": 23, "pago": 2},
    "Mercado Pago": {"corte": 27, "pago": 6},
    "NU": {"corte": 24, "pago": 5},
    "Uala": {"corte": 30, "pago": 14},
    "Vexi": {"corte": 3, "pago": 17},
    "Didi": {"corte": 22, "pago": 7}
}
TARJETAS_MAESTRAS = sorted(list(CONFIG_TARJETAS.keys())) + ["Santander Debito", "Banamex Debito"]

CATEGORIAS_GASTO = [
    "Centro Comercial", "Tiangiis/Mercado", "Tienda/Oxxo/K", "Gasolina",
    "Ropa y Calzado", "Servicios", "Internet", "Luz", "Gas", 
    "Suplementos", "Telefonia", "E-Comerce (Amazon/Mercado/Walmart/Suburbia)", "Otros"
]

# Creación de pestañas
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📥 Ingreso", "📤 Egreso", "🛒 Gasto", "📊 Resumen", "📆 Tarjetas"])

def convertir_a_csv(df): 
    return df.to_csv(index=False).encode('utf-8-sig')

# ==========================================
# 1. MENU DE INGRESO NÓMINA
# ==========================================
with tab1:
    st.subheader("📥 Ingreso de Nómina")
    monto_in = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f", key="in_monto")
    fecha_in = st.date_input("Fecha", datetime.date.today(), key="in_fecha")
    descripcion_in = st.text_input("Descripción", placeholder="Ej. Quincena", key="in_desc")
    tipo_in = st.selectbox("Tipo", ["Efectivo", "Transferencia"], key="in_tipo")
    
    cuenta_in = None
    if tipo_in == "Transferencia":
        cuenta_in = st.selectbox("Selecciona Cuenta de Destino", ["Santander Nomina", "Banamex Nomina"], key="in_cuenta")
        
    if st.button("Guardar Ingreso", key="btn_ingreso"):
        if monto_in > 0:
            data = {"fecha": str(fecha_in), "tipo_movimiento": "Ingreso", "monto": monto_in, "descripcion": descripcion_in, "metodo": tipo_in, "cuenta": cuenta_in}
            try:
                supabase.table("nomina").insert(data)
                st.success("¡Ingreso guardado exitosamente!")
                st.rerun()
            except Exception as e: 
                st.error(f"Error de Base de Datos: {e}")
        else:
            st.warning("El monto debe ser mayor a 0")

# ==========================================
# 2. MENU DE EGRESOS NÓMINA
# ==========================================
with tab2:
    st.subheader("📤 Egreso de Nómina")
    monto_eg = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f", key="eg_monto")
    fecha_eg = st.date_input("Fecha", datetime.date.today(), key="eg_fecha")
    descripcion_eg = st.text_input("Descripción", placeholder="Ej. Pago de tarjeta", key="eg_desc")
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
                supabase.table("nomina").insert(data)
                st.success("¡Egreso guardado exitosamente!")
                st.rerun()
            except Exception as e: 
                st.error(f"Error de Base de Datos: {e}")
        else:
            st.warning("El monto debe ser mayor a 0")

# ==========================================
# 3. MENU DE GASTOS DIARIOS
# ==========================================
with tab3:
    st.subheader("🛒 Registro de Gasto Diario")
    monto_gd = st.number_input("Monto ($)", min_value=0.0, step=10.0, format="%.2f", key="gd_monto")
    categoria_gd = st.selectbox("Categoría", CATEGORIAS_GASTO, key="gd_cat")
    descripcion_gd = st.text_input("Detalle/Notas (Opcional)", placeholder="Ej. Supermercado", key="gd_desc")
    tipo_gd = st.selectbox("Tipo", ["Efectivo", "Tarjeta"], key="gd_tipo")
    
    cuenta_gd = None
    plazo_gd = "Contado"
    if tipo_gd == "Tarjeta":
        cuenta_gd = st.selectbox("Selecciona Tarjeta", TARJETAS_MAESTRAS, key="gd_cuenta")
        if cuenta_gd not in ["Santander Debito", "Banamex Debito"]:
            plazo_gd = st.selectbox("Plazo de Pago", ["Una exhibición", "3 meses", "6 meses", "9 meses", "12 meses", "15 meses", "18 meses", "24 meses"], key="gd_plazo")
        
    if st.button("Guardar Gasto Diario", key="btn_gasto"):
        if monto_gd > 0:
            hoy = datetime.date.today()
            desc_final = descripcion_gd if descripcion_gd.strip() != "" else categoria_gd
            data = {
                "fecha": str(hoy), "monto": monto_gd, "descripcion": desc_final, "categoria": categoria_gd, "metodo": tipo_gd, "cuenta": cuenta_gd, "plazo": plazo_gd,
                "anio_registro": hoy.year, "mes_registro": hoy.month
            }
            try:
                supabase.table("gastos_diarios").insert(data)
                st.success("¡Gasto diario guardado exitosamente!")
                st.rerun()
            except Exception as e: 
                st.error(f"Error de Base de Datos: {e}")
        else:
            st.warning("El monto debe ser mayor a 0")

# ==========================================
# 4. MENU DE RESUMEN DE GASTOS
# ==========================================
with tab4:
    st.subheader("📊 Resumen General")
    try:
        res_nomina = supabase.table("nomina").select("*").eq("tipo_movimiento", "Ingreso").execute()
        if res_nomina.data:
            df_in = pd.DataFrame(res_nomina.data)
            st.metric("Total Ingresos Nómina", f"${df_in['monto'].sum():,.2f}")
            df_in_f = df_in[["fecha", "descripcion", "monto", "metodo", "cuenta"]].sort_values(by="fecha", ascending=False)
            with st.expander("👁️ Ver Ingresos"):
                st.dataframe(df_in_f, hide_index=True)
    except Exception as e: 
        st.error(f"Error al cargar Resumen: {e}")
        
    st.markdown("---")
    try:
        res_gastos = supabase.table("gastos_diarios").select("*").execute()
        if res_gastos.data:
            df = pd.DataFrame(res_gastos.data)
            df_cat_graf = df.groupby("categoria")["monto"].sum().reset_index().sort_values(by="monto", ascending=False)
            st.markdown("### 🛒 Gastos por Categoría")
            st.bar_chart(data=df_cat_graf, x="categoria", y="monto", color="#FF4B4B")
            
            df_g_f = df[["fecha", "categoria", "descripcion", "monto", "metodo", "cuenta", "plazo"]].sort_values(by="fecha", ascending=False)
            with st.expander("👁️ Ver Todos los Gastos"):
                st.dataframe(df_g_f, hide_index=True)
    except Exception as e: 
        pass

# ==========================================
# 5. MENU: AGENDA DE TARJETAS
# ==========================================
with tab5:
    st.subheader("📆 Saldos y Pagos del Mes")
    hoy = datetime.date.today()
    mes_sel = st.selectbox("Ver Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=hoy.month-1)
    anio_sel = st.number_input("Ver Año", min_value=2026, max_value=2035, value=hoy.year, step=1)
    mes_num = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"].index(mes_sel) + 1

    try:
        res_all_g = supabase.table("gastos_diarios").select("*").eq("metodo", "Tarjeta").execute()
        if res_all_g.data:
            df_all = pd.DataFrame(res_all_g.data)
            resumen_tarjetas = []
            
            for t_nombre, fechas in CONFIG_TARJETAS.items():
                pago_contado = 0.0
                pago_msi = 0.0
                detalles_msi = []
                df_t = df_all[df_all["cuenta"] == t_nombre]
                
                for _, gasto in df_t.iterrows():
                    g_monto = float(gasto["monto"])
                    g_plazo = gasto["plazo"]
                    g_anio = int(gasto["anio_registro"])
                    g_mes = int(gasto["mes_registro"])
                    
                    if g_plazo in ["Contado", "Una exhibición"]:
                        if g_anio == anio_sel and g_mes == mes_num:
                            pago_contado += g_monto
                    else:
                        meses_totales = int(g_plazo.split()[0])
                        sensualidad = g_monto / meses_totales
                        meses_transcurridos = (anio_sel - g_anio) * 12 + (mes_num - g_mes)
                        if 0 <= meses_transcurridos < meses_totales:
                            pago_msi += sensualidad
                            meses_restantes = meses_totales - (meses_transcurridos + 1)
                            detalles_msi.append(f"• {gasto['descripcion']}: msl. {meses_transcurridos+1}/{meses_totales} (${sensualidad:,.2f})")
                
                total_a_pagar = pago_contado + pago_msi
                if total_a_pagar > 0:
                    resumen_tarjetas.append({"Tarjeta": t_nombre, "Total": total_a_pagar, "Corte": fechas['corte'], "Pago": fechas['pago'], "Contado": pago_contado, "MSI": pago_msi, "Detalles": detalles_msi})
            
            if resumen_tarjetas:
                gran_total_mes = sum([item["Total"] for item in resumen_tarjetas])
                st.subheader(f"Total del Mes: ${gran_total_mes:,.2f} MXN")
                for r in resumen_tarjetas:
                    with st.expander(f"💳 {r['Tarjeta']} — ${r['Total']:,.2f}"):
                        st.write(f"Corte: Día {r['Corte']} | Pago: Día {r['Pago']}")
                        st.write(f"Contado: ${r['Contado']:,.2f} | MSI: ${r['MSI']:,.2f}")
                        for d in r["Detalles"]: st.text(d)
            else:
                st.success("Sin pagos este mes.")
        else:
            st.info("Sin registros de tarjeta.")
    except Exception as e: 
        pass
