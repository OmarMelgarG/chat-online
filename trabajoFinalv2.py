from flask import Flask
from flask_socketio import SocketIO, send
from telegram import Update
from telegram.error import Conflict
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

import threading
import requests
import asyncio
import os
import time
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError, InferenceTimeoutError

def normalizar_modelo_huggingface(valor):
    if not valor:
        return None

    modelo = valor.strip().strip('"').strip("'")
    modelo = modelo.rstrip('.,;:')

    if modelo.lower() in {'value', 'none', 'null', 'n/a', 'na', 'false'}:
        return None

    return modelo

# CONFIGURACIÓN DE VARIABLES DE ENTORNO
tokenTelegram = os.getenv('TOKEN_TELEGRAM')
chatID = os.getenv('CHAT_ID')
huggingface_api_token = os.getenv('HUGGINGFACE_API_TOKEN')
huggingface_model = normalizar_modelo_huggingface(os.getenv('HUGGINGFACE_MODEL')) or 'Qwen/Qwen2.5-7B-Instruct-1M'
huggingface_fallback_models = []
for raw_model in os.getenv('HUGGINGFACE_FALLBACK_MODELS', '').split(','):
    model = normalizar_modelo_huggingface(raw_model)
    if model:
        huggingface_fallback_models.append(model)
huggingface_provider = os.getenv('HUGGINGFACE_PROVIDER', 'auto').lower()

# DEBUG: Verificación de variables en el arranque
print(f"[STARTUP DEBUG] TOKEN_TELEGRAM: {'✓' if tokenTelegram else 'MISSING'}")
print(f"[STARTUP DEBUG] CHAT_ID: {'✓' if chatID else 'MISSING'}")
print(f"[STARTUP DEBUG] HUGGINGFACE_API_TOKEN: {'✓' if huggingface_api_token else 'MISSING'}")
print(f"[STARTUP DEBUG] HUGGINGFACE_MODEL: {huggingface_model if huggingface_model else 'MISSING'}")
print(f"[STARTUP DEBUG] HUGGINGFACE_FALLBACK_MODELS: {huggingface_fallback_models}")
print(f"[STARTUP DEBUG] HUGGINGFACE_PROVIDER: {huggingface_provider}")

# PALABRAS CLAVE DE ACTIVACIÓN
palabrasClave = {
    "ayuda": "/ayuda",
    "emergencia": "/ayuda",
    "urgente": "/ayuda",
    "comprar": "/comprar",
    "productos": "/producto",
    "reserva": "/reserva"
}

# APLICACIÓN WEB Y WEBSOCKET
app = Flask(__name__)
socket = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

def crear_bot_telegram():
    bot = ApplicationBuilder().token(tokenTelegram).build()
    bot.add_handler(CommandHandler('tutor', tutorTelegram))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibirTelegram))
    return bot

# INTERFAZ HTML
@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Chat de Estudio Inteligente</title>
<style>
:root {
    color-scheme: dark;
    --bg: #f4f7fb;
    --panel: #ffffff;
    --surface: #e5eaf4;
    --surface-dark: #d1d9e6;
    --text: #1b2330;
    --muted: #596277;
    --primary: #0f3d7c;
    --accent: #0066cc;
    --success: #0a6b4a;
    --danger: #c4303b;
    --border: rgba(27, 35, 48, 0.12);
}
* { box-sizing: border-box; }
body {
    margin: 0;
    font-family: Inter, Arial, sans-serif;
    background: linear-gradient(180deg, #eef2f8 0%, #f7fbff 100%);
    color: var(--text);
}
.page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
}
.panel {
    width: min(1080px, 100%);
    background: var(--panel);
    border-radius: 24px;
    box-shadow: 0 36px 80px rgba(15, 61, 124, 0.08);
    overflow: hidden;
    border: 1px solid rgba(15, 61, 124, 0.08);
}
.header {
    background: #0f3d7c;
    color: white;
    padding: 30px 34px;
}
.header-title { margin: 0; font-size: 1.85rem; letter-spacing: -0.02em; }
.header-subtitle {
    margin: 10px 0 0;
    color: rgba(255, 255, 255, 0.82);
    font-size: 1rem;
    max-width: 620px;
    line-height: 1.6;
}
.body-grid { display: grid; grid-template-columns: 1fr; }
.chat-panel { padding: 28px; }
.status-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 22px; }
.status-card {
    width: 100%;
    border-radius: 16px;
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 18px 22px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.status-card strong { color: var(--primary); }
.chat-window {
    border-radius: 24px;
    background: var(--surface);
    min-height: 460px;
    max-height: 620px;
    overflow: hidden;
    border: 1px solid var(--border);
    display: flex;
    flex-direction: column;
}
.chat-history { padding: 24px; overflow-y: auto; gap: 14px; display: flex; flex-direction: column; flex: 1; }
.message {
    display: inline-flex;
    max-width: 80%;
    white-space: pre-wrap;
    word-break: break-word;
    line-height: 1.6;
    padding: 16px 18px;
    border-radius: 18px;
    border: 1px solid transparent;
}
.message.user { background: #ffffff; color: var(--text); align-self: flex-end; border-color: rgba(15, 61, 124, 0.08); }
.message.telegram { background: #eef2ff; color: var(--text); border-color: rgba(0, 102, 204, 0.16); align-self: flex-start; }
.message.tutor { background: #0f3d7c; color: white; border-color: rgba(255, 255, 255, 0.18); align-self: flex-start; }
.message.system { background: #f5f7fb; color: var(--muted); border-radius: 14px; align-self: center; font-size: 0.95rem; }
.message .badge { display: inline-flex; gap: 8px; align-items: center; margin-bottom: 10px; font-size: 0.82rem; opacity: 0.88; }
.input-area { padding: 20px 24px 24px; background: #f6f8fb; border-top: 1px solid var(--border); }
.input-row { display: grid; grid-template-columns: 1fr auto; gap: 12px; }
.input-row input {
    width: 100%;
    border: 1px solid rgba(15, 61, 124, 0.16);
    border-radius: 16px;
    padding: 16px 18px;
    font-size: 1rem;
    background: white;
    color: var(--text);
}
.input-row button {
    border: none;
    border-radius: 16px;
    background: var(--accent);
    color: white;
    padding: 0 26px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s ease, background 0.2s ease;
}
.input-row button:hover { background: #004ea1; transform: translateY(-1px); }
.note { margin-top: 16px; color: var(--muted); font-size: 0.92rem; }
@media (max-width: 720px) {
    .panel { border-radius: 18px; }
    .chat-window { min-height: 520px; }
}
</style>
</head>
<body>
<div class="page">
    <section class="panel">
        <header class="header">
            <h1 class="header-title">Chat de Estudio Inteligente</h1>
            <p class="header-subtitle">Asistente de estudio profesional para la web y Telegram. Usa <strong>/tutor</strong> para pedir explicaciones académicas.</p>
        </header>
        <div class="body-grid">
            <div class="chat-panel">
                <div class="status-bar">
                    <div class="status-card">
                        <div><strong>Modo Tutor:</strong> disponible para consultas académicas.</div>
                        <div id="statusText">Escribe /tutor seguido de tu pregunta.</div>
                    </div>
                </div>
                <div class="chat-window">
                    <div id="chat" class="chat-history"></div>
                </div>
                <div class="input-area">
                    <div class="input-row">
                        <input type="text" id="nombre" placeholder="Tu nombre" autocomplete="off" />
                        <button id="btn-entrar" onclick="guardarNombre()">Entrar</button>
                    </div>
                    <div class="input-row" style="margin-top: 12px;">
                        <input type="text" id="mensaje" placeholder="Escribe un mensaje o /tutor explica ..." autocomplete="off" />
                        <button onclick="enviar()">Enviar</button>
                    </div>
                    <p class="note">El tutor de IA responde aquí y también envía la misma explicación al chat de Telegram.</p>
                </div>
            </div>
        </div>
    </section>
</div>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<script>
var socket = io();
var nombre = "";

function guardarNombre() {
    let input = document.getElementById("nombre");
    if (input.value.trim() == "") { alert("Ingrese nombre"); return; }
    nombre = input.value.trim();
    input.disabled = true;
    document.getElementById("btn-entrar").disabled = true;
    agregarSistema(nombre + " se unió al chat");
}

function enviar() {
    let input = document.getElementById("mensaje");
    let mensaje = input.value.trim();
    if (nombre == "") { alert("Ingrese nombre"); return; }
    if (mensaje == "") return;

    if (mensaje.toLowerCase().startsWith('/tutor')) {
        socket.emit('tutor_query', mensaje);
        showTutorStatus('El tutor de IA está analizando tu consulta...');
        agregarChat('Tu consulta se está enviando al tutor de IA...', 'system');
    } else {
        socket.send(nombre + ': ' + mensaje);
    }
    input.value = "";
}

socket.on('message', function(msg) { agregarChat(msg, 'user'); });
socket.on('telegram_message', function(msg) { agregarChat('📲 ' + msg, 'telegram'); });
socket.on('emergencia', function(msg) { agregarChat('🚨 ' + msg, 'telegram'); });
socket.on('tutor_status', function(msg) { showTutorStatus(msg); });
socket.on('tutor_response', function(msg) { hideTutorStatus(); agregarChat('🤖 Tutor IA: ' + msg, 'tutor'); });

function agregarChat(msg, tipo) {
    var chat = document.getElementById('chat');
    var div = document.createElement('div');
    div.className = 'message ' + (tipo || 'user');
    if (tipo === 'tutor') {
        div.innerHTML = '<div class="badge">🤖 <strong>Tutor IA</strong></div>' + msg;
    } else if (tipo === 'telegram') {
        div.innerHTML = '<div class="badge">📲 <strong>Telegram</strong></div>' + msg;
    } else if (tipo === 'system') {
        div.className = 'message system';
        div.innerHTML = msg;
    } else {
        div.innerHTML = msg;
    }
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}
function agregarSistema(msg) { agregarChat('<strong>Sistema:</strong> ' + msg, 'system'); }
function showTutorStatus(text) { document.getElementById('statusText').textContent = text; }
function hideTutorStatus() { showTutorStatus('El tutor está listo para tu próxima consulta.'); }
</script>
</body>
</html>
"""

@socket.on("message")
def recibirMensaje(mensaje):
    print("WEB:", mensaje)
    send(mensaje, broadcast=True)
    comandosDeteccion(mensaje)

@socket.on('tutor_query')
def recibirTutorQuery(texto):
    print('TUTOR QUERY:', texto)
    pregunta = texto[len('/tutor'):].strip()

    if not pregunta:
        socket.emit('tutor_status', 'Escribe /tutor seguido de tu consulta.')
        return

    socket.emit('tutor_status', 'El tutor de IA está procesando tu consulta...')
    respuesta = consultar_tutor_ia(pregunta)
    socket.emit('tutor_response', respuesta)
    socket.emit('tutor_status', 'El tutor está listo para tu próxima consulta.')

    enviarTelegram(f"📘 Tutor IA\nPregunta: {pregunta}\nRespuesta: {respuesta}")

def comandosDeteccion(mensaje):
    texto = mensaje.lower()
    for palabra, comando in palabrasClave.items():
        if palabra in texto:
            notificacion = f"\n            REPORTE MENSAJE CHAT WEB\n\n            Comando:\n            {comando}\n\n            Palabra Detectada:\n            {mensaje}\n\n            Estado:\n            En revision...\n        "
            socket.emit("ayuda", notificacion)
            threading.Thread(target=enviarTelegram, args=(notificacion,), daemon=True).start()
            print("Notificacion Enviada...")
            break

# ENVÍO DE MENSAJES A TELEGRAM
def enviarTelegram(texto):
    url = f"https://api.telegram.org/bot{tokenTelegram}/sendMessage"
    data = {"chat_id": chatID, "text": texto}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

def obtener_modelos_compatibles_huggingface():
    return ['HuggingFaceBio/Carbon-3B']

def obtener_modelos_huggingface():
    modelos = [huggingface_model]
    for model in huggingface_fallback_models:
        if model not in modelos:
            modelos.append(model)
    for model in obtener_modelos_compatibles_huggingface():
        if model not in modelos:
            modelos.append(model)
    return modelos

def crear_cliente_huggingface():
    if huggingface_provider == 'auto':
        return InferenceClient(api_key=huggingface_api_token, timeout=30)
    return InferenceClient(provider=huggingface_provider, api_key=huggingface_api_token, timeout=30)

def describir_modelo_huggingface(modelo):
    return modelo or 'modelo recomendado automatico de Hugging Face'

def extraer_texto_chat_completion(respuesta):
    try:
        mensaje = respuesta.choices[0].message
    except Exception:
        return str(respuesta)

    contenido = getattr(mensaje, 'content', None)

    if isinstance(contenido, str) and contenido.strip():
        return contenido.strip()

    if isinstance(contenido, list):
        partes = []
        for parte in contenido:
            if isinstance(parte, dict):
                texto = parte.get('text') or parte.get('content')
            else:
                texto = getattr(parte, 'text', None) or getattr(parte, 'content', None)

            if isinstance(texto, str) and texto.strip():
                partes.append(texto.strip())

        if partes:
            return '\n'.join(partes)

    razonamiento = getattr(mensaje, 'reasoning', None)
    if isinstance(razonamiento, str) and razonamiento.strip():
        print('[DEBUG] HF devolvio razonamiento interno sin respuesta final visible.')
        return (
            'El modelo generó razonamiento interno, pero no devolvió una respuesta final visible. '
            'Intenta de nuevo o usa un modelo sin razonamiento.'
        )

    return 'No fue posible extraer una respuesta legible del tutor de IA.'

def obtener_status_code_hf(error):
    response = getattr(error, 'response', None)
    return getattr(response, 'status_code', None)

def extraer_detalle_error_hf(error):
    response = getattr(error, 'response', None)
    if response is None:
        return str(error)

    try:
        data = response.json()
        if isinstance(data, dict):
            if isinstance(data.get('error'), str):
                return data['error']
            return str(data)
        return str(data)
    except Exception:
        text = getattr(response, 'text', '')
        return text or str(error)

def construir_mensaje_error_hf(error, modelo):
    status_code = obtener_status_code_hf(error)
    detalle = extraer_detalle_error_hf(error)

    if status_code == 401:
        return 'Error de autorización (401) en Hugging Face. Revisa tu HUGGINGFACE_API_TOKEN.'

    if status_code == 402:
        return (
            'Hugging Face rechazó la consulta por créditos o facturación. '
            'En tu cuenta de Hugging Face, revisa Inference Providers y habilita billing si no tienes créditos disponibles.'
        )

    if status_code == 403:
        return (
            'Tu token de Hugging Face no tiene permisos suficientes para Inference Providers. '
            'Crea un token nuevo con permiso de inferencia serverless y actualízalo en Render.'
        )

    if status_code == 429:
        return 'Hugging Face alcanzó el límite de uso. Intenta de nuevo en unos segundos.'

    if status_code == 503:
        return 'El tutor de IA se está iniciando en Hugging Face. Repite la consulta en 15 segundos.'

    if status_code in (400, 404):
        return (
            'No encontré un modelo conversacional compatible en Hugging Face con la configuración actual. '
            f'Último intento: {describir_modelo_huggingface(modelo)}. '
            f'Detalle: {detalle[:160]}'
        )

    return f'Error de Hugging Face ({status_code if status_code else "sin código"}): {detalle[:180]}'

# CONSULTA EXCLUSIVA A HUGGING FACE
def consultar_tutor_ia(pregunta):
    print(f"[DEBUG] consultar_tutor_ia llamado con: {pregunta[:50]}...")
    print(f"[DEBUG] hf_token disponible: {bool(huggingface_api_token)}")
    print(f"[DEBUG] hf_model: {huggingface_model}")
    
    prompt = (
        "Eres un Tutor Académico Formal y Profesional. "
        "Responde en español con claridad, precisión y un tono ejecutivo. "
        "Explica conceptos de manera estructurada y mantén la respuesta breve. "
        f"Consulta: {pregunta}"
    )

    if not huggingface_api_token:
        return "El tutor de IA no está disponible. Falta configurar la variable HUGGINGFACE_API_TOKEN en Render."

    client = crear_cliente_huggingface()
    mensajes = [
        {
            'role': 'system',
            'content': (
                'Eres un Tutor Académico Formal y Profesional. '
                'Responde siempre en español con claridad, precisión y tono ejecutivo. '
                'Explica conceptos de forma estructurada y mantén la respuesta breve. '
                'No muestres razonamiento interno ni pasos de análisis; entrega solo la respuesta final.'
            )
        },
        {
            'role': 'user',
            'content': prompt
        }
    ]
    errores_modelo = []

    for modelo in obtener_modelos_huggingface():
        try:
            print(f"[DEBUG] Probando modelo HF por provider {huggingface_provider}: {describir_modelo_huggingface(modelo)}")
            respuesta = client.chat_completion(
                model=modelo,
                messages=mensajes,
                max_tokens=400,
                temperature=0.3,
                reasoning_effort='none',
            )
            return extraer_texto_chat_completion(respuesta)

        except InferenceTimeoutError as e:
            print(f"[DEBUG] HF timeout con {describir_modelo_huggingface(modelo)}: {e}")
            return 'El tutor de IA se está iniciando en Hugging Face. Repite la consulta en 15 segundos.'

        except HfHubHTTPError as e:
            status_code = obtener_status_code_hf(e)
            detalle = extraer_detalle_error_hf(e)
            print(f"[DEBUG] HF HTTP error con {describir_modelo_huggingface(modelo)}: {status_code} - {detalle}")

            if status_code in (400, 404):
                errores_modelo.append(f"{describir_modelo_huggingface(modelo)}: {status_code} - {detalle[:120]}")
                continue

            return construir_mensaje_error_hf(e, modelo)

        except Exception as e:
            print(f"[DEBUG] HF error inesperado con {describir_modelo_huggingface(modelo)}: {e}")
            errores_modelo.append(f"{describir_modelo_huggingface(modelo)}: {e}")
            continue

    if errores_modelo:
        detalles = ' | '.join(errores_modelo[:2])
        return (
            'No encontré un modelo conversacional compatible en Hugging Face con la configuración actual. '
            'Revisa HUGGINGFACE_MODEL y HUGGINGFACE_FALLBACK_MODELS en Render. '
            f'Detalle: {detalles}'
        )

    return 'No fue posible obtener respuesta del tutor de IA en Hugging Face.'

# RECEPCIÓN DESDE TELEGRAM → WEB
async def recibirTelegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = update.message.from_user.first_name
    mensaje = update.message.text
    texto = f"{usuario}: {mensaje}"
    print("TELEGRAM:", texto)
    socket.emit("telegram_message", texto)

async def tutorTelegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = ' '.join(context.args).strip()
    if not pregunta:
        await update.message.reply_text("Usa /tutor seguido de tu consulta, por ejemplo: /tutor explica la fotosíntesis")
        return

    await update.message.reply_text("El tutor de IA está analizando tu consulta...")
    respuesta = consultar_tutor_ia(pregunta)
    await update.message.reply_text(respuesta)
    socket.emit("tutor_response", respuesta)
    enviarTelegram(f"📘 Tutor IA\nPregunta: {pregunta}\nRespuesta: {respuesta}")

# FUNCIÓN DEL HILO DEL BOT
def iniciarBot():
    asyncio.set_event_loop(asyncio.new_event_loop())
    if not tokenTelegram:
        print("BOT TELEGRAM INACTIVO: falta TOKEN_TELEGRAM")
        return

    while True:
        botTelegram = crear_bot_telegram()
        try:
            print("BOT TELEGRAM ACTIVO")
            botTelegram.run_polling(stop_signals=None, drop_pending_updates=True)
            return
        except Conflict as e:
            print(f"BOT TELEGRAM EN CONFLICTO: {e}. Reintentando en 10 segundos...")
            time.sleep(10)
        except Exception as e:
            print(f"BOT TELEGRAM ERROR: {e}. Reintentando en 15 segundos...")
            time.sleep(15)

# EJECUCIÓN PRINCIPAL
if __name__ == "__main__":
    hiloBot = threading.Thread(target=iniciarBot, daemon=True)
    hiloBot.start()
    print("Servidor iniciado")

    puerto = int(os.getenv('PORT', 5000))
    socket.run(
        app,
        host="0.0.0.0",
        port=puerto,
        debug=False,
        allow_unsafe_werkzeug=True
    )