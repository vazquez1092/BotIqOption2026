import streamlit as st
import time
from datetime import datetime, timedelta
import pytz
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Scanner PRO v2 - 10 Pares", layout="wide")
arg_tz = pytz.timezone('America/Argentina/Buenos_Aires')

# Estilos CSS para la interfaz
st.markdown("""
    <style>
    .stMetric { background-color: #1e1e1e; padding: 10px; border-radius: 10px; }
    .stSuccess { background-color: #052e16; color: #4ade80; }
    .stError { background-color: #450a0a; color: #f87171; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DE SESIÓN (Persistencia de conexión) ---
if "api" not in st.session_state:
    st.session_state.api = None
if "conectado" not in st.session_state:
    st.session_state.conectado = False

# --- SIDEBAR (LOGIN) ---
with st.sidebar:
    st.header("🔑 Acceso IQ Option")
    email = st.text_input("Email", value="vazquez.1092@gmail.com")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("🚀 Iniciar Scanner", use_container_width=True):
        with st.spinner("Conectando con el servidor..."):
            API = IQ_Option(email, password)
            check, reason = API.connect()
            if check:
                st.session_state.api = API
                st.session_state.conectado = True
                st.success("¡Conexión Exitosa!")
            else:
                st.error(f"Error de conexión: {reason}")

# --- LÓGICA TÉCNICA ---
def obtener_activo_disponible(api, par):
    """Detecta si el mercado real está abierto o usa OTC"""
    try:
        profits = api.get_all_profit()
        # Si el par no tiene profit en mercado real, es que está cerrado
        if par in profits.get('turbo', {}):
            return par
        return f"{par}-OTC"
    except:
        return f"{par}-OTC"

def calcular_indicadores(velas):
    """Cálculo de Fibonacci 0.618, RSI y tendencia"""
    df = pd.DataFrame(velas)
    df['close'] = df['close'].astype(float)
    
    # Fibonacci 0.618 de las últimas 20 velas
    max_h = df['max'].tail(20).max()
    min_l = df['min'].tail(20).min()
    fibo_618 = max_h - ((max_h - min_l) * 0.618)
    
    # RSI (14 periodos)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs.iloc[-1]))
    
    return df['close'].iloc[-1], fibo_618, rsi

# --- PANEL CENTRAL ---
st.title("📊 Dashboard de Señales Fibonacci + RSI (10 Pares)")

if st.session_state.conectado:
    lista_pares = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", 
                   "EURJPY", "GBPJPY", "EURGBP", "AUDJPY", "GBPCHF"]
    
    # Contenedor dinámico para evitar que el reloj se congele
    placeholder = st.empty()
    
    while True:
        try:
            # 1. Sistema de reconexión automática (Evita el error de WebSocket)
            if not st.session_state.api.check_connect():
                st.session_state.api.connect()
                time.sleep(1)

            ahora = datetime.now(arg_tz)
            prox_v = (ahora + timedelta(minutes=1)).replace(second=0, microsecond=0)

            with placeholder.container():
                c1, c2 = st.columns(2)
                c1.metric("🕒 Hora (Junín)", ahora.strftime("%H:%M:%S"))
                c2.info(f"⌛ Próxima Vela: {prox_v.strftime('%H:%M:%S')}")
                
                st.divider()
                
                # Crear grid de 2 columnas para los 10 pares
                grid = st.columns(2)
                
                for i, par_base in enumerate(lista_pares):
                    with grid[i % 2]:
                        activo = obtener_activo_disponible(st.session_state.api, par_base)
                        
                        # Pedir velas de 1 minuto
                        velas = st.session_state.api.get_candles(activo, 60, 40, time.time())
                        
                        if velas:
                            precio, f618, rsi = calcular_indicadores(velas)
                            
                            # Lógica de señal
                            distancia = abs(precio - f618)
                            
                            if distancia < 0.0002: # Proximidad al nivel Fibo
                                if rsi < 35:
                                    st.success(f"🔥 **{activo}**: COMPRA (CALL) | RSI: {round(rsi,1)}")
                                elif rsi > 65:
                                    st.error(f"🔻 **{activo}**: VENTA (PUT) | RSI: {round(rsi,1)}")
                                else:
                                    st.warning(f"⚖️ **{activo}**: Nivel Fibo tocado, esperando RSI...")
                            else:
                                st.write(f"🔎 {activo}: Buscando entrada... (Precio: {round(precio,5)})")
                        else:
                            st.write(f"⚠️ {activo}: Conectando datos...")

            time.sleep(2) # Pausa para refrescar datos sin saturar
            
        except Exception as e:
            st.error(f"Error de conexión: {e}")
            time.sleep(5)
else:
    st.info("👈 Por favor, ingresá tus credenciales en el panel izquierdo para comenzar el monitoreo.")
