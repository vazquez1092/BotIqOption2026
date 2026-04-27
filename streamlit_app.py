import streamlit as st
import time
from datetime import datetime, timedelta
from iqoptionapi.stable_api import IQ_Option

# Configuración de página
st.set_page_config(page_title="Scanner Fibo REAL", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    .css-1kyx60w { font-size: 1.5rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Scanner Fibo IQ: Señales en Tiempo Real")

# Sidebar
with st.sidebar:
    st.header("Configuración")
    email = st.text_input("Email", value="vazquez.1092@gmail.com")
    password = st.text_input("Contraseña", type="password")
    conectar = st.button("Conectar Mercado Real")

# Estructura de 4 columnas
pares = ["EURUSD", "GBPUSD", "EURJPY", "AUDUSD"]
st.write("---")
cols = st.columns(4)
interfaces = []

for i, par in enumerate(pares):
    with cols[i]:
        st.subheader(f"📊 {par}")
        interfaces.append({
            "par": par,
            "msg": st.empty(),
            "fibo": st.empty(),
            "reloj": st.empty()
        })

if conectar:
    API = IQ_Option(email, password)
    check, reason = API.connect()
    
    if check:
        st.success("✅ Conectado a IQ Option")
        while True:
            ahora = datetime.now()
            # Próxima vela (ejemplo a 5 min)
            prox_v = (ahora + timedelta(minutes=5 - ahora.minute % 5)).replace(second=0, microsecond=0)
            
            for ui in interfaces:
                # Intento Mercado Real, si no, OTC
                velas = API.get_candles(ui["par"], 60, 20, time.time())
                nombre_activo = ui["par"]
                if not velas:
                    nombre_activo = ui["par"] + "-OTC"
                    velas = API.get_candles(nombre_activo, 60, 20, time.time())

                if velas:
                    precios = [v['close'] for v in velas]
                    max_h, min_l = max([v['max'] for v in velas]), min([v['min'] for v in velas])
                    precio_actual = precios[-1]
                    f618 = max_h - ((max_h - min_l) * 0.618)
                    
                    ui["msg"].write(f"Modo: **{nombre_activo}**")
                    
                    # Lógica de señal real
                    if abs(precio_actual - f618) < 0.0001:
                        ui["fibo"].metric("NIVEL 0.618", f"{precio_actual:.5f}", "🎯 ¡ENTRAR YA!", delta_color="normal")
                        ui["reloj"].error(f"🕒 Señal: {ahora.strftime('%H:%M:%S')}\n\n🔔 Entrada: {prox_v.strftime('%H:%M')}")
                    else:
                        ui["fibo"].metric("Buscando Fibo", f"{precio_actual:.5f}", f"F618: {f618:.5f}", delta_color="off")
                        ui["reloj"].info(f"⏳ Próxima Vela: {prox_v.strftime('%H:%M:%S')}")
                else:
                    ui["msg"].warning("Activo Cerrado")
            
            time.sleep(2) # Respiro para el servidor
    else:
        st.error(f"Error: {reason}")
