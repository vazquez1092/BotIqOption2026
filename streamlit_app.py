import streamlit as st
import time
from iqoptionapi.stable_api import IQ_Option

st.set_page_config(page_title="Scanner Fibo IQ", layout="wide")

st.title("🚀 Scanner Fibo IQ: Modo Nube")

# Barra lateral fija
with st.sidebar:
    st.header("Configuración")
    email = st.text_input("Email", value="vazquez.1092@gmail.com")
    password = st.text_input("Contraseña", type="password")
    conectar = st.button("Conectar Bot")

# CONTENEDORES FIJOS (Para evitar el error de duplicados)
st.write("---")
col1, col2 = st.columns(2)
with col1:
    st.info("📊 **EURJPY**")
    fibo_eur = st.empty() # Espacio reservado
    boton_eur = st.empty()

with col2:
    st.warning("📊 **GBPUSD**")
    fibo_gbp = st.empty() # Espacio reservado
    boton_gbp = st.empty()

if conectar:
    API = IQ_Option(email, password)
    check, reason = API.connect()
    
    if check:
        st.success("✅ Conectado")
        # CREAMOS LOS BOTONES UNA SOLA VEZ FUERA DEL BUCLE
        boton_eur.button("🎯 OPORTUNIDAD ORO", key="btn_fijo_eur")
        boton_gbp.button("⏳ MONITOREANDO", key="btn_fijo_gbp")
        
        while True:
            # SOLO ACTUALIZAMOS EL TEXTO, NO EL BOTÓN
            fibo_eur.write("Nivel Fibo: **0.618** | Estado: **ACTIVO**")
            fibo_gbp.write("Nivel Fibo: **0.50** | Estado: **ESPERANDO**")
            time.sleep(2)
    else:
        st.error(f"Error: {reason}")
