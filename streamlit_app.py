import streamlit as st
import time
from datetime import datetime, timedelta
import pytz
from iqoptionapi.stable_api import IQ_Option

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Scanner Fibo REAL - ARG", layout="wide")

arg_tz = pytz.timezone('America/Argentina/Buenos_Aires')

st.title("🚀 Scanner Fibo IQ: Señales (Hora Argentina)")

# ---------------- SESSION STATE ----------------
if "api" not in st.session_state:
    st.session_state.api = None
if "conectado" not in st.session_state:
    st.session_state.conectado = False

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("Configuración")
    email = st.text_input("Email", value="")
    password = st.text_input("Contraseña", type="password")

    if st.button("Conectar Mercado Real"):
        API = IQ_Option(email, password)
        check, reason = API.connect()

        if check:
            st.session_state.api = API
            st.session_state.conectado = True
            st.success("✅ Conectado")
        else:
            st.error(f"Error: {reason}")

# ---------------- UI PRINCIPAL ----------------
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

# ---------------- LÓGICA PRINCIPAL ----------------
if st.session_state.conectado and st.session_state.api:

    API = st.session_state.api

    ahora = datetime.now(arg_tz)

    minutos_restantes = 5 - (ahora.minute % 5)
    prox_v = (ahora + timedelta(minutes=minutos_restantes)).replace(second=0, microsecond=0)

    for ui in interfaces:
        try:
    velas = API.get_candles(ui["par"], 60, 50, time.time())
    nombre_activo = ui["par"]

    if not velas:
        nombre_activo = ui["par"] + "-OTC"
        velas = API.get_candles(nombre_activo, 60, 50, time.time())

    if velas:
        closes = [v['close'] for v in velas]
        highs = [v['max'] for v in velas]
        lows = [v['min'] for v in velas]

        precio_actual = closes[-1]

        # EMA 20
        ema20 = sum(closes[-20:]) / 20

        # FIBO
        max_h = max(highs[-20:])
        min_l = min(lows[-20:])
        f618 = max_h - ((max_h - min_l) * 0.618)

        # VELA ACTUAL
        vela_actual = velas[-1]
        vela_alcista = vela_actual['close'] > vela_actual['open']
        vela_bajista = vela_actual['close'] < vela_actual['open']

        # VOLATILIDAD
        rango = max_h - min_l
        volatilidad_ok = rango > 0.0005

        ui["msg"].write(f"Modo: **{nombre_activo}**")

        señal = None

        if abs(precio_actual - f618) < 0.0001 and volatilidad_ok:

            if precio_actual > ema20 and vela_alcista:
                señal = "CALL 🚀"

            elif precio_actual < ema20 and vela_bajista:
                señal = "PUT 🔻"

        if señal:
            ui["fibo"].metric(
                "SNIPER SIGNAL",
                f"{precio_actual:.5f}",
                señal
            )

            ui["reloj"].error(
                f"🎯 {señal}\n🕒 {ahora.strftime('%H:%M:%S')}\n🔔 Entrada: {prox_v.strftime('%H:%M')}"
            )
        else:
            ui["fibo"].metric(
                "Sin señal",
                f"{precio_actual:.5f}",
                f"F618: {f618:.5f}",
                delta_color="off"
            )

            ui["reloj"].info(
                f"⏳ {ahora.strftime('%H:%M:%S')}\nPróx: {prox_v.strftime('%H:%M')}"
            )

except Exception as e:
    ui["msg"].error(f"Error: {str(e)}")

    # 🔁 REFRESH CONTROLADO (NO while True)
    time.sleep(2)
    st.rerun()
