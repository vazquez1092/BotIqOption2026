import streamlit as st
import time
from datetime import datetime, timedelta
import pytz
import pandas as pd
from iqoptionapi.stable_api import IQ_Option
import logging

# Desactivar logs de error de la librería en la consola para que no ensucien la pantalla
logging.disable(logging.CRITICAL)

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Scanner PRO v2 - Ultra Estable", layout="wide")
arg_tz = pytz.timezone('America/Argentina/Buenos_Aires')

# --- ESTADO DE SESIÓN ---
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
        API = IQ_Option(email, password)
        check, reason = API.connect()
        if check:
            st.session_state.api = API
            st.session_state.conectado = True
            st.success("¡Conexión Inicial Exitosa!")
            time.sleep(2)
        else:
            st.error(f"Error: {reason}")

# --- LÓGICA DE ESTABILIDAD ---
def obtener_datos_seguros(api, activo):
    """Intenta obtener velas manejando errores de conexión silenciosamente"""
    try:
        # Intentar reconectar si el socket se cerró
        if not api.check_connect():
            api.connect()
            time.sleep(5) # Pausa crucial para que el socket se estabilice
        
        velas = api.get_candles(activo, 60, 40, time.time())
        if isinstance(velas, list):
            return velas
        return None
    except:
        return None

def obtener_activo(api, par):
    try:
        profits = api.get_all_profit()
        if par in profits.get('turbo', {}):
            return par
        return f"{par}-OTC"
    except:
        return f"{par}-OTC"

# --- PANEL PRINCIPAL ---
st.title("🎯 Scanner Fibonacci + RSI (10 Pares)")

if st.session_state.conectado:
    lista_pares = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", 
                   "EURJPY", "GBPJPY", "EURGBP", "AUDJPY", "GBPCHF"]
    
    placeholder = st.empty()
    
    while True:
        try:
            ahora = datetime.now(arg_tz)
            with placeholder.container():
                st.metric("🕒 Hora Actual (Junín)", ahora.strftime("%H:%M:%S"))
                st.divider()
                
                cols = st.columns(2)
                
                for i, par_base in enumerate(lista_pares):
                    with cols[i % 2]:
                        activo = obtener_activo(st.session_state.api, par_base)
                        
                        # Llamada segura que evita los errores rojos en pantalla
                        velas = obtener_datos_seguros(st.session_state.api, activo)
                        
                        if velas:
                            df = pd.DataFrame(velas)
                            precio = float(df['close'].iloc[-1])
                            
                            # Cálculo rápido de Fibo 0.618
                            max_h = df['max'].tail(20).max()
                            min_l = df['min'].tail(20).min()
                            f618 = max_h - ((max_h - min_l) * 0.618)
                            
                            distancia = abs(precio - f618)
                            
                            if distancia < 0.00015:
                                st.success(f"🔥 **{activo}**: ¡OPORTUNIDAD!")
                            else:
                                st.write(f"🔎 {activo}: {round(precio, 5)} (Fibo: {round(f618, 5)})")
                        else:
                            st.info(f"⏳ {activo}: Sincronizando con IQ Option...")

            time.sleep(3) # No bajar de 3 segundos para no saturar la conexión
            
        except Exception as e:
            # En lugar de mostrar el error rojo gigante, mostramos un mensaje breve
            st.warning("Ajustando conexión... por favor espera.")
            time.sleep(5)
            continue
