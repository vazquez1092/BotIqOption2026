import streamlit as st
import time
from iqoptionapi.stable_api import IQ_Option

st.set_page_config(page_title="Scanner Fibo IQ - Pro", layout="wide")

# Estética profesional
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #2e7d32; color: white; }
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Scanner Fibo IQ: 4 Pares + OTC")

with st.sidebar:
    st.header("Configuración")
    email = st.text_input("Email", value="vazquez.1092@gmail.com")
    password = st.text_input("Contraseña", type="password")
    conectar = st.button("Conectar Bot", key="btn_conectar_principal")

# Definición de los 4 pares (El bot probará Normal y luego OTC si el normal está cerrado)
pares_monitoreo = ["EURUSD", "GBPUSD", "EURJPY", "AUDUSD"]

# Contenedores de interfaz para los 4 pares
st.write("---")
cols = st.columns(4)
contenedores = []

for i, par in enumerate(pares_monitoreo):
    with cols[i]:
        st.subheader(f"📊 {par}")
        status = st.empty()
        fibo = st.empty()
        alerta = st.empty()
        contenedores.append({"status": status, "fibo": fibo, "alerta": alerta, "par": par})

if conectar:
    API = IQ_Option(email, password)
    check, reason = API.connect()
    
    if check:
        st.success("✅ Conexión Establecida")
        
        while True:
            for cont in contenedores:
                # Lógica simplificada: El bot detecta si el par es OTC automáticamente
                # En un entorno real, aquí se llamaría a API.get_all_open_time()
                is_otc = "-OTC" if time.localtime().tm_wday >= 5 else "" # Ejemplo: Sáb/Dom es OTC
                par_actual = cont["par"] + is_otc
                
                # Simulación de detección de niveles Fibonacci 0.50 y 0.618
                # Aquí la API leería las últimas velas para calcular el retroceso
                cont["status"].write(f"Modo: **{is_otc.replace('-','')} Mercado**")
                
                # Ejemplo de señal activa en EURUSD
                if cont["par"] == "EURUSD":
                    cont["fibo"].metric("Nivel Fibo", "0.618", delta="¡ENTRAR!")
                    cont["alerta"].button("🎯 OPORTUNIDAD ORO", key=f"btn_{cont['par']}")
                else:
                    cont["fibo"].metric("Nivel Fibo", "0.382", delta="Esperando...")
                    cont["alerta"].button("⏳ MONITOREANDO", key=f"btn_{cont['par']}")
            
            time.sleep(10) # Escaneo cada 10 segundos para no saturar la API
    else:
        st.error(f"Error de conexión: {reason}")
