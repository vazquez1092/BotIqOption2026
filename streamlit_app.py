import streamlit as st
import time
from datetime import datetime, timedelta
from iqoptionapi.stable_api import IQ_Option

st.set_page_config(page_title="Scanner Fibo REAL", layout="wide")

# Estética y CSS
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; background-color: #2e7d32; color: white; }
    .stMetric { background-color: #1e1e1e; padding: 10px; border-radius: 10px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Scanner Fibo IQ: SEÑALES REALES")

with st.sidebar:
    st.header("Configuración")
    email = st.text_input("Email", value="vazquez.1092@gmail.com")
    password = st.text_input("Contraseña", type="password")
    conectar = st.button("Conectar Bot Real")

pares = ["EURUSD", "GBPUSD", "EURJPY", "AUDUSD"]

# Espacios en la interfaz
st.write("---")
cols = st.columns(4)
contenedores = []
for i, par in enumerate(pares):
    with cols[i]:
        st.subheader(f"📊 {par}")
        fibo_val = st.empty()
        timer_val = st.empty()
        btn_val = st.empty()
        contenedores.append({"fibo": fibo_val, "timer": timer_val, "btn": btn_val, "par": par})

def calcular_fibo(velas):
    # Lógica Real: Máximo y Mínimo de las últimas 20 velas
    highs = [v['max'] for v in velas]
    lows = [v['min'] for v in velas]
    precio_actual = velas[-1]['close']
    
    max_h, min_l = max(highs), min(lows)
    diff = max_h - min_l
    
    # Nivel 61.8%
    nivel_618 = max_h - (diff * 0.618)
    return precio_actual, nivel_618

if conectar:
    API = IQ_Option(email, password)
    check, reason = API.connect()
    
    if check:
        st.success("✅ Conectado al Mercado Real")
        while True:
            ahora = datetime.now()
            prox_vela = (ahora + timedelta(minutes=5 - ahora.minute % 5)).replace(second=0, microsecond=0)
            
            for cont in contenedores:
                # El bot intenta mercado normal, si falla va a OTC
                simbolo = cont["par"]
                velas = API.get_candles(simbolo, 60, 20, time.time())
                
                if not velas: # Intento modo OTC
                    simbolo = cont["par"] + "-OTC"
                    velas = API.get_candles(simbolo, 60, 20, time.time())

                if velas:
                    precio, f618 = calcular_fibo(velas)
                    distancia = abs(precio - f618)
                    
                    # Si el precio está muy cerca del nivel (0.618)
                    if distancia < 0.0001:
                        cont["fibo"].metric(f"{simbolo}", f"{precio:.5f}", delta="🎯 NIVEL 0.618")
                        cont["timer"].write(f"🔔 Entrada: **{prox_vela.strftime('%H:%M')}**")
                        cont["btn"].button("🎯 ENTRAR YA", key=f"run_{simbolo}")
                    else:
                        cont["fibo"].metric(f"{simbolo}", f"{precio:.5f}", delta=f"Fibo: {f618:.5f}", delta_color="off")
                        cont["timer"].write("⏳ Buscando punto...")
                        cont["btn"].button("⏳ ESCANEANDO", key=f"wait_{simbolo}")
                
            time.sleep(2) # Escaneo rápido
    else:
        st.error(f"Error: {reason}")
