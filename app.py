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
            st.error("Usuario o contraseña incorrectos. Acceso denegado.")
    st.stop()

# Conexión a Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuración Maestra de tus Tarjetas (Fechas de Corte y Pago)
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

# Lista de tus Categorías para Gasto Diario
CATEGORIAS_GASTO = [
    "Centro Comercial", "Tiangiis/Mercado", "Tienda/Oxxo/K", "Gasolina",
    "Ropa y Calzado", "Servicios", "Internet", "Luz", "Gas", 
    "Suplementos", "Telefonia", "E-Comerce (Amazon/Mercado/Walmart/Suburbia)", "Otros"
]

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
    st.session_state["gd_cat"] = "Centro Comercial"
    if "gd_plazo" in st.session_state:
        st.session_state["gd_plazo"] = "Una exhibición"

# Creación de 5 pestañas móviles
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📥 Ingreso", "📤 Egreso", "🛒 Gasto", "📊 Resumen", "📆 Tarjetas"])

def convertir_a_csv(df): return df.to_csv(index=False).encode('utf-8-sig')

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
        submit_in = st.form_submit_button("Guardar Ingreso", on_click=limpiar_ingreso)
        
    if submit_in and monto_in > 0:
        data = {"fecha": str(fecha_in), "tipo_movimiento": "Ingreso", "monto": monto_in, "descripcion": descripcion_in, "metodo": tipo_in, "cuenta": cuenta_in}
        try:
            # CORRECCIÓN: Se remueve el .execute() para la nueva versión de la librería
            supabase.table("nomina").insert(data)
            st.success("¡Ingreso guardado!")
            st.rerun()
        except Exception as e: st.error(f"Error: {e}")

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
        data = {"fecha": str(fecha_eg), "tipo_movimiento": "Egreso", "monto": monto_eg, "descripcion": descripcion_eg, "metodo": tipo_eg, "cuenta": cuenta_eg, "cuenta_destino": cuenta_dest_eg}
        try:
            # CORRECCIÓN: Se remueve el .execute() para la nueva versión de la librería
            supabase.table("nomina").insert(data)
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
    descripcion_gd = st.text_input("Detalle/Notas (Opcional)", placeholder="Ej. Mandado, Tenis nuevos", key="gd_desc")
    tipo_gd = st.selectbox("Tipo", ["Efectivo", "Tarjeta"], key="gd_tipo")
    
    cuenta_gd = None
    plazo_gd = "Contado"
    if tipo_gd == "Tarjeta":
        cuenta_gd = st.selectbox("Selecciona Tarjeta", TARJETAS_MAESTRAS, key="gd_cuenta")
        if cuenta_gd not in ["Santander Debito", "Banamex Debito"]:
            plazo_gd = st.selectbox("Plazo de Pago", ["Una exhibición", "3 meses", "6 meses", "9 meses", "12 meses", "15 meses", "18 meses", "24 meses"], key="gd_plazo")
        
    with st.form("form_diario_submit", clear_on_submit=True):
        submit_gd = st.form_submit_button("Guardar Gasto Diario", on_click=limpiar_diario)
        
    if submit_gd and monto_gd > 0:
        hoy = datetime.date.today()
        desc_final = descripcion_gd if descripcion_gd.strip() != "" else categoria_gd
        data = {
            "fecha": str(hoy), "monto": monto_gd, "descripcion": desc_final, "categoria": categoria_gd, "metodo": tipo_gd, "cuenta": cuenta_gd, "plazo": plazo_gd,
            "anio_registro": hoy.year, "mes_registro": hoy.month
        }
        try:
            # CORRECCIÓN: Se remueve el .execute() para la nueva versión de la librería
            supabase.table("gastos_diarios").insert(data)
            st.success("¡Gasto guardado!")
            st.rerun()
        except Exception as e: st.error(f"Error: {e}")

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
                st.download_button("📥 Descargar CSV de Ingresos", convertir_a_csv(df_in_f), f"ingresos_{datetime.date.today()}.csv", "text/csv", key="dl_in_tab4")
    except Exception as e: st.error(f"Error: {e}")
        
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
                st.download_button("🛒 Descargar CSV de Gastos", convertir_a_csv(df_g_f), f"gastos_{datetime.date.today()}.csv", "text/csv", key="dl_gd_tab4")
    except Exception as e: st.error(f"Error: {e}")

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
            df_all["fecha"] = pd.to_datetime(df_all["fecha"])
            
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
                        mensualidad = g_monto / meses_totales
                        meses_transcurridos = (anio_sel - g_anio) * 12 + (mes_num - g_mes)
                        
                        if 0 <= meses_transcurridos < meses_totales:
                            pago_msi += mensualidad
                            meses_restantes = meses_totales - (meses_transcurridos + 1)
                            detalles_msi.append(f"• {gasto['descripcion']}: msl. {meses_transcurridos+1}/{meses_totales} (${mensualidad:,.2f}) — Quedan: {meses_restantes} meses pend.")
                
                total_a_pagar = pago_contado + pago_msi
                
                if total_a_pagar > 0:
                    resumen_tarjetas.append({
                        "Tarjeta": t_nombre, "Corte": f"Día {fechas['corte']}", "Pago": f"Día {fechas['pago']}",
                        "Contado": pago_contado, "MSI": pago_msi, "Total": total_a_pagar, "Detalles": detalles_msi
                    })
            
            if resumen_tarjetas:
                st.markdown(f"### 💳 Total a pagar en {mes_sel}:")
                gran_total_mes = sum([item["Total"] for item in resumen_tarjetas])
                st.subheader(f"**${gran_total_mes:,.2f} MXN**")
                
                export_data = []
                for r in resumen_tarjetas:
                    export_data.append({
                        "Tarjeta": r["Tarjeta"], "Día de Corte": r["Corte"], "Día de Pago": r["Pago"],
                        "Monto Contado ($)": round(r["Contado"], 2), "Monto MSI ($)": round(r["MSI"], 2), "Total a Pagar ($)": round(r["Total"], 2)
                    })
                    
                    with st.expander(f"💳 {r['Tarjeta']} — Total: ${r['Total']:,.2f}"):
                        st.markdown(f"**Fecha de Corte:** {r['Corte']} de cada mes")
                        st.markdown(f"**Fecha Límite de Pago:** {r['Pago']} del mes siguiente")
                        st.markdown(f"**Compras del mes (Contado):** ${r['Contado']:,.2f}")
                        st.markdown(f"**Cargos por MSI:** ${r['MSI']:,.2f}")
                        if r["Detalles"]:
                            st.markdown("**Desglose e Inteligencia de MSI:**")
                            for d in r["Detalles"]: st.text(d)
                
                st.markdown("---")
                df_export = pd.DataFrame(export_data)
                csv_tarjetas = convertir_a_csv(df_export)
                st.download_button(label="📋 Descargar Plan de Pagos (CSV)", data=csv_tarjetas, file_name=f"plan_pagos_{mes_sel}_{anio_sel}.csv", mime="text/csv", key="dl_tarjetas_tab5")
            else:
                st.success(f"🎉 ¡Felicidades! No tienes pagos pendientes para {mes_sel} {anio_sel}.")
        else:
            st.info("Registra compras con tarjeta en la pestaña 'Gasto' para calcular tus fechas de pago.")
            
    except Exception as e: st.error(f"Error al calcular agenda de tarjetas: {e}")
