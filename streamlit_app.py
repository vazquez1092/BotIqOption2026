import streamlit as st
import time
from datetime import datetime, timedelta
from iqoptionapi.stable_api import IQ_Option

st.set_page_config(page_title="Scanner Fibo IQ - Pro Timers", layout="wide")

# Estética y colores de trading
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #2e7d32; color: white; }
    .stMetric { background-color: #1e1e1e; padding: 10px; border-radius: 10px; border: 1px solid #333; }
    .time-text { color: #00ff00; font-weight: bold; font-size: 1.1em; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Scanner Fibo IQ: 4 Pares + Timers")

with st.sidebar:
    st.header("Configuración")
    email = st.text_input("Email", value="vazquez.1092@gmail.com")
    password = st.text_input("Contraseña", type="password")
    conectar = st.button("Conectar Bot", key="btn_conectar_v3")

pares_monitoreo = ["EURUSD", "GBPUSD", "EURJPY", "AUDUSD"]

st.write("---")
cols = st.columns(4)
contenedores = []

for i, par in enumerate(pares_monitoreo):
    with cols[i]:
        st.subheader(f"📊 {par}")
        status = st.empty()
        fibo = st.empty()
        # NUEVOS ESPACIOS PARA HORARIOS
        tiempos = st.empty()
        alerta = st.empty()
        contenedores.append({"status": status, "fibo": fibo, "tiempos": tiempos, "alerta": alerta, "par": par})

if conectar:
    API = IQ_Option(email, password)
    check, reason = API.connect()
    
    if check:
        st.success("✅ Conexión Establecida")
        
        while True:
            # Obtener hora actual (horario Junín de los Andes)
            ahora = datetime.now()
            
            # Cálculo de la próxima vela de 5 min (ejemplo)
            prox_vela = (ahora + timedelta(minutes=5 - ahora.minute % 5)).replace(second=0, microsecond=0)
            
            for cont in contenedores:
                is_otc = "-OTC" if ahora.weekday() >= 5 else ""
                
                cont["status"].write(f"Modo: **{is_otc.replace('-','')} Mercado**")
                
                # Lógica visual de las señales
                if cont["par"] == "EURUSD": # Ejemplo de señal activa
                    cont["fibo"].metric("Nivel Fibo", "0.618", delta="¡ENTRAR!")
                    
                    # MOSTRAMOS LOS HORARIOS QUE PEDISTE
                    cont["tiempos"].markdown(f"""
                        🕒 Detectada: **{ahora.strftime('%H:%M:%S')}** 🔔 Entrada: **{prox_vela.strftime('%H:%M')} (Próx. Vela)**
                    """)
                    
                    cont["alerta"].button("🎯 OPORTUNIDAD ORO", key=f"btn_{cont['par']}_v3")
                else:
                    cont["fibo"].metric("Nivel Fibo", "0.412", delta="Buscando...")
                    cont["tiempos"].write("⏳ Esperando punto de entrada...")
                    cont["alerta"].button("⏳ MONITOREANDO", key=f"btn_{cont['par']}_v3")
            
            time.sleep(1) # Actualización rápida del reloj
    else:
        st.error(f"Error: {reason}")
