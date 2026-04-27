import streamlit as st
import time
from datetime import datetime, timedelta
import pytz # Librería para zonas horarias
from iqoptionapi.stable_api import IQ_Option

# Configuración de página
st.set_page_config(page_title="Scanner Fibo REAL - ARG", layout="wide")

# Definimos la zona horaria de Argentina
arg_tz = pytz.timezone('America/Argentina/Buenos_Aires')

st.title("🚀 Scanner Fibo IQ: Señales (Hora Argentina)")

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
            # OBTENEMOS LA HORA REAL DE ARGENTINA
            ahora = datetime.now(arg_tz)
            
            # Cálculo de próxima vela de 5 min basado en hora ARG
            minutos_restantes = 5 - (ahora.minute % 5)
            prox_v = (ahora + timedelta(minutes=minutos_restantes)).replace(second=0, microsecond=0)
            
            for ui in interfaces:
                velas = API.get_candles(ui["par"], 60, 20, time.time())
                nombre_activo = ui["par"]
                if not velas:
                    nombre_activo = ui["par"] + "-OTC"
                    velas = API.get_candles(nombre_activo, 60, 20, time.time())

                if velas:
                    max_h = max([v['max'] for v in velas])
                    min_l = min([v['min'] for v in velas])
                    precio_actual = velas[-1]['close']
                    f618 = max_h - ((max_h - min_l) * 0.618)
                    
                    ui["msg"].write(f"Modo: **{nombre_activo}**")
                    
                    if abs(precio_actual - f618) < 0.0001:
                        ui["fibo"].metric("NIVEL 0.618", f"{precio_actual:.5f}", "🎯 ¡ENTRAR YA!")
                        # Mostramos la hora exacta del aviso en horario local
                        ui["reloj"].error(f"🕒 Señal: {ahora.strftime('%H:%M:%S')}\n\n🔔 Entrada: {prox_v.strftime('%H:%M')}")
                    else:
                        ui["fibo"].metric("Buscando Fibo", f"{precio_actual:.5f}", f"F618: {f618:.5f}", delta_color="off")
                        ui["reloj"].info(f"⏳ Reloj ARG: {ahora.strftime('%H:%M:%S')}\n\nPróx. Vela: {prox_v.strftime('%H:%M')}")
            
            time.sleep(1) 
    else:
        st.error(f"Error: {reason}")
