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
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# CONFIGURACIÓN DE VARIABLES DE ENTORNO
tokenTelegram = os.getenv('TOKEN_TELEGRAM')
chatID = os.getenv('CHAT_ID')
huggingface_api_token = os.getenv('HUGGINGFACE_API_TOKEN')
huggingface_model = os.getenv('HUGGINGFACE_MODEL', 'google/flan-t5-small')
huggingface_fallback_models = [
    model.strip()
    for model in os.getenv('HUGGINGFACE_FALLBACK_MODELS', 'bigscience/bloomz-560m').split(',')
    if model.strip()
]
huggingface_api_base_url = os.getenv('HUGGINGFACE_API_BASE_URL', 'https://api-inference.huggingface.co')
huggingface_router_base_url = os.getenv('HUGGINGFACE_ROUTER_BASE_URL', 'https://router.huggingface.co/hf-inference')
huggingface_router_mode = os.getenv('HUGGINGFACE_ROUTER_MODE')
if not huggingface_router_mode:
    legacy_router_flag = os.getenv('HUGGINGFACE_ENABLE_ROUTER_FALLBACK')
    if legacy_router_flag is None:
        huggingface_router_mode = 'auto'
    else:
        huggingface_router_mode = 'always' if legacy_router_flag.lower() == 'true' else 'never'
huggingface_router_mode = huggingface_router_mode.lower()

# DEBUG: Verificación de variables en el arranque
print(f"[STARTUP DEBUG] TOKEN_TELEGRAM: {'✓' if tokenTelegram else 'MISSING'}")
print(f"[STARTUP DEBUG] CHAT_ID: {'✓' if chatID else 'MISSING'}")
print(f"[STARTUP DEBUG] HUGGINGFACE_API_TOKEN: {'✓' if huggingface_api_token else 'MISSING'}")
print(f"[STARTUP DEBUG] HUGGINGFACE_MODEL: {huggingface_model if huggingface_model else 'MISSING'}")
print(f"[STARTUP DEBUG] HUGGINGFACE_FALLBACK_MODELS: {huggingface_fallback_models}")
print(f"[STARTUP DEBUG] HUGGINGFACE_API_BASE_URL: {huggingface_api_base_url}")
print(f"[STARTUP DEBUG] HUGGINGFACE_ROUTER_BASE_URL: {huggingface_router_base_url}")
print(f"[STARTUP DEBUG] HUGGINGFACE_ROUTER_MODE: {huggingface_router_mode}")

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

def crear_sesion_http_con_reintentos():
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["POST"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session

def obtener_modelos_huggingface():
    modelos = [huggingface_model]
    for model in huggingface_fallback_models:
        if model not in modelos:
            modelos.append(model)
    return modelos

def usar_router_huggingface(modelo):
    modelos_no_compatibles_router = {'google/flan-t5-small', 'google/flan-t5-base'}

    if huggingface_router_mode == 'never':
        return False
    if huggingface_router_mode == 'always':
        return True
    return modelo not in modelos_no_compatibles_router

def obtener_endpoints_huggingface(modelo):
    endpoints = []

    if usar_router_huggingface(modelo) and huggingface_router_base_url:
        endpoints.append(f"{huggingface_router_base_url.rstrip('/')}/models/{modelo}")

    if huggingface_api_base_url:
        endpoints.append(f"{huggingface_api_base_url.rstrip('/')}/models/{modelo}")

    return endpoints

def interpretar_respuesta_hf(data):
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            return first.get('generated_text') or first.get('text') or str(first)
        return str(first)
    if isinstance(data, dict):
        for key in ('generated_text', 'text', 'output'):
            if key in data and isinstance(data[key], str):
                return data[key]
        return str(data)
    return str(data)

def es_modelo_no_soportado(resp):
    try:
        body = resp.json()
    except ValueError:
        body = resp.text
    detalle = str(body)
    return resp.status_code == 400 and 'Model not supported by provider hf-inference' in detalle

def construir_mensaje_error_red(errores_red):
    detalles = ' | '.join(errores_red[:2])
    return (
        'Error de conexión con Hugging Face. '
        'El servicio no respondió desde los endpoints configurados. '
        f'Detalle: {detalles}'
    )

def construir_mensaje_modelo_no_soportado(modelo):
    return (
        'El modelo configurado en Hugging Face no está soportado por el proveedor disponible. '
        f'Modelo actual: {modelo}. '
        'Configura HUGGINGFACE_MODEL con un modelo compatible o usa HUGGINGFACE_FALLBACK_MODELS.'
    )

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

    headers = {
        "Authorization": f"Bearer {huggingface_api_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 250, "temperature": 0.3}
    }
    session = crear_sesion_http_con_reintentos()
    errores_red = []
    modelo_no_soportado = []
    
    try:
        for modelo in obtener_modelos_huggingface():
            print(f"[DEBUG] Probando modelo HF: {modelo}")
            for url in obtener_endpoints_huggingface(modelo):
                try:
                    print(f"[DEBUG] Probando endpoint HF: {url}")
                    resp = session.post(url, headers=headers, json=payload, timeout=20)
                    print(f"[DEBUG] HF Respuesta status: {resp.status_code}")

                    if resp.status_code == 200:
                        return interpretar_respuesta_hf(resp.json())

                    if resp.status_code == 503:
                        return "El tutor de IA se está iniciando en el servidor gratuito de Hugging Face. Por favor, repite la pregunta en 15 segundos."

                    if resp.status_code == 401:
                        return "Error de autorización (401) en Hugging Face. Revisa tu HUGGINGFACE_API_TOKEN."

                    if es_modelo_no_soportado(resp):
                        modelo_no_soportado.append(f"{modelo} en {url}")
                        print(f"[DEBUG] Modelo no soportado por el proveedor actual: {modelo} en {url}")
                        continue

                    if resp.status_code in (404, 410):
                        errores_red.append(f"{url} devolvió {resp.status_code}")
                        continue

                    return f"Hugging Face respondió con error {resp.status_code}: {resp.text[:100]}"

                except requests.exceptions.RequestException as e:
                    print(f"[DEBUG] HF error en {url}: {e}")
                    errores_red.append(f"{url}: {e}")
                    continue

        if modelo_no_soportado:
            return construir_mensaje_modelo_no_soportado(modelo_no_soportado[0])

        if errores_red:
            return construir_mensaje_error_red(errores_red)

        return "No se encontró un endpoint válido de Hugging Face para el tutor IA."
    finally:
        session.close()

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