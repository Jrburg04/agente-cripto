import os
import time
import json
import urllib.request
import threading
from datetime import datetime
from flask import Flask

# --- CONFIGURACIÓN ---
# Reemplaza con la URL de tu Webhook de Discord para Cripto
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/TU_WEBHOOK_CRIPTO_AQUI"

# Pares de criptomonedas a monitorear
PARES = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]

# Estado de posición y saldo simulado por cada moneda
POSICIONES = {par: False for par in PARES}
HISTORIAL_PRECIOS = {par: [] for par in PARES}

app = Flask(__name__)

@app.route('/')
def home():
    return "Agente Cripto Multimoneda Operando OK - 24/7", 200

def enviar_discord(mensaje):
    if "TU_WEBHOOK_CRIPTO_AQUI" in DISCORD_WEBHOOK_URL:
        print("⚠️ Pendiente configurar la URL del Webhook de Discord.")
        return
    try:
        data = json.dumps({"content": mensaje}).encode('utf-8')
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL,
            data=data,
            headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            print(f"📩 Alerta Cripto enviada a Discord ({response.getcode()}).")
    except Exception as e:
        print(f"❌ Error al enviar a Discord: {e}")

def obtener_precio_binance(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        return float(data['price'])

def calcular_media_movil(par, periodo):
    precios = HISTORIAL_PRECIOS[par]
    if len(precios) < periodo:
        return 0.0
    return sum(precios[-periodo:]) / periodo

def analizar_par(par):
    global POSICIONES, HISTORIAL_PRECIOS
    try:
        precio_actual = obtener_precio_binance(par)
        HISTORIAL_PRECIOS[par].append(precio_actual)
        
        # Mantener un historial de máximo 30 lecturas para el cálculo de medias
        if len(HISTORIAL_PRECIOS[par]) > 30:
            HISTORIAL_PRECIOS[par].pop(0)

        ma5 = calcular_media_movil(par, 5)
        ma20 = calcular_media_movil(par, 20)

        hora_str = datetime.now().strftime("%H:%M:%S")
        print(f"[{hora_str}] 🪙 {par}: ${precio_actual:,.2f} | MA5: ${ma5:,.2f} | MA20: ${ma20:,.2f}")

        # Evaluar cruce de medias si ya tenemos suficientes datos acumulados
        if ma5 > 0 and ma20 > 0:
            # Señal de Compra (Cruce Alcista)
            if ma5 > ma20 and not POSICIONES[par]:
                POSICIONES[par] = True
                msg = f"🚀 **[CRIPTO MULTIMONEDA - SEÑAL DE COMPRA]**\n**Par:** {par}\n**Precio:** ${precio_actual:,.2f} USDT\n**Indicador:** MA5 (${ma5:,.2f}) superó a MA20 (${ma20:,.2f})"
                enviar_discord(msg)

            # Señal de Venta (Cruce Bajista)
            elif ma5 < ma20 and POSICIONES[par]:
                POSICIONES[par] = False
                msg = f"⚠️ **[CRIPTO MULTIMONEDA - SEÑAL DE VENTA]**\n**Par:** {par}\n**Precio:** ${precio_actual:,.2f} USDT\n**Indicador:** MA5 cayó por debajo de MA20"
                enviar_discord(msg)

    except Exception as e:
        print(f"❌ Error procesando {par}: {e}")

def bucle_agente():
    time.sleep(5)
    enviar_discord("🪙 **Agente Cripto Multimoneda Activo (BTC, ETH, SOL, BNB).**")
    while True:
        for par in PARES:
            analizar_par(par)
            time.sleep(2)  # Pausa entre cada consulta de moneda
        
        time.sleep(30)  # Pausa de 30 segundos entre ciclos completos de revisión

t = threading.Thread(target=bucle_agente)
t.daemon = True
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
