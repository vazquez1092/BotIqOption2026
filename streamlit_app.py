import streamlit as st
import time
from datetime import datetime, timedelta
import pytz
from iqoptionapi.stable_api import IQ_Option

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Scanner Fibo REAL - ARG", layout="wide")

arg_tz = pytz.timezone('America/Argentina/Buenos_Aires')

st.title("🚀 Scanner Fibo IQ: Modo SNIPER (Hora Argentina)")

# ---------------- SESSION ----------------
if "api" not in st.session_state:
    st.session_state.api = None

if "conectado" not in st.session_state:
    st.session_state.conectado = False

if "signals" not in st.session_state:
    st.session_state.signals = {}

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("Configuración")
    email = st.text_input("Email")
    password = st.text_input("Contraseña", type="password")

    if st.button("Conectar Mercado Real"):
        API = IQ_Option(email, password)
        check, reason = API.connect()

        if check:
            st.session_state.api = API
            st.session_state.conectado = True
            st.success("✅ Conectado")
        else:
            st.error(f"❌ Error: {reason}")

# ---------------- INTERFAZ ----------------
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

# ---------------- FUNCION INTELIGENTE OTC ----------------
def obtener_velas(API, par):
    velas = API.get_candles(par, 60, 50, time.time())

    if velas:
        return velas, par

    # fallback OTC
    par_otc = par + "-OTC"
    velas = API.get_candles(par_otc, 60, 50, time.time())

    if velas:
        return velas, par_otc

    return None, par

# ---------------- LÓGICA ----------------
if st.session_state.conectado and st.session_state.api:

    API = st.session_state.api

    ahora = datetime.now(arg_tz)

    minutos_restantes = 5 - (ahora.minute % 5)
    prox_v = (ahora + timedelta(minutes=minutos_restantes)).replace(second=0, microsecond=0)

    for ui in interfaces:

        try:
            velas, nombre_activo = obtener_velas(API, ui["par"])

            if velas:

                closes = [v['close'] for v in velas]
                highs = [v['max'] for v in velas]
                lows = [v['min'] for v in velas]

                precio_actual = closes[-1]

                # EMA
                ema20 = sum(closes[-20:]) / 20

                # FIBO
                max_h = max(highs[-20:])
                min_l = min(lows[-20:])
                f618 = max_h - ((max_h - min_l) * 0.618)

                # VELA
                vela = velas[-1]
                alcista = vela['close'] > vela['open']
                bajista = vela['close'] < vela['open']

                # VOLATILIDAD
                rango = max_h - min_l
                volatilidad_ok = rango > 0.0005

                señal = None

                if abs(precio_actual - f618) < 0.0001 and volatilidad_ok:
                    if precio_actual > ema20 and alcista:
                        señal = "CALL 🚀"
                    elif precio_actual < ema20 and bajista:
                        señal = "PUT 🔻"

                # ---------------- CACHE VISUAL (ANTI PARPADEO) ----------------
                if señal:
                    st.session_state.signals[ui["par"]] = {
                        "señal": señal,
                        "precio": precio_actual,
                        "hora": ahora.strftime('%H:%M:%S'),
                        "entrada": prox_v.strftime('%H:%M'),
                        "activo": nombre_activo
                    }

                data = st.session_state.signals.get(ui["par"], None)

                # ---------------- MOSTRAR ----------------
                if data:
                    ui["msg"].write(f"Modo: **{data['activo']}**")

                    ui["fibo"].metric(
                        "SNIPER SIGNAL",
                        f"{data['precio']:.5f}",
                        data["señal"]
                    )

                    ui["reloj"].error(
                        f"🎯 {data['señal']}\n🕒 {data['hora']}\n🔔 Entrada: {data['entrada']}"
                    )
                else:
                    ui["msg"].write(f"Modo: **{nombre_activo}**")

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

    # 🔁 REFRESH SUAVE (SIN PARPADEO BRUSCO)
    time.sleep(3)
    st.rerun()
