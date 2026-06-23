from flask import Flask
from flask_socketio import SocketIO, send
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes
)

import threading
import requests
import asyncio
import os



# TELEGRAM


tokenTelegram = os.getenv('TOKEN_TELEGRAM')
chatID = os.getenv('CHAT_ID')

#PALABRAS CLAVE DE ACTIVACION
palabrasClave={
    "ayuda":"/ayuda",
    "emergencia":"/ayuda",
    "urgente":"/ayuda",
    "comprar":"/comprar",
    "productos":"/producto",
    "reserva":"/reserva"
}




# APP


app = Flask(__name__)

socket = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)



# BOT TELEGRAM


botTelegram = ApplicationBuilder().token(
    tokenTelegram
).build()







# INTERFAZ HTML


@app.route("/")
def index():

    return """
<!DOCTYPE html>
<html lang="es">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Chat Tiempo Real</title>

<style>

body{
    font-family:Arial;
    background:#f2f2f2;
    display:flex;
    justify-content:center;
    align-items:center;
    height:100vh;
    margin:0;
}

.chat-container{
    width:95%;
    max-width:450px;
    background:white;
    border-radius:10px;
    overflow:hidden;
    box-shadow:0 0 10px rgba(0,0,0,0.2);
}

.chat-header{
    background:#007bff;
    color:white;
    padding:15px;
    text-align:center;
    font-size:20px;
    font-weight:bold;
}

#chat{
    height:400px;
    overflow-y:auto;
    padding:10px;
    background:#fafafa;
}

.mensaje{
    background:#e4e6eb;
    padding:10px;
    border-radius:10px;
    margin-bottom:10px;
    word-wrap:break-word;
}

.emergencia{
    background:#ff4d4d;
    color:white;
    font-weight:bold;
}

.controls{
    padding:10px;
    border-top:1px solid #ddd;
}

.input-group{
    display:flex;
    gap:10px;
    margin-bottom:10px;
}

input{
    flex:1;
    padding:10px;
    border:1px solid #ccc;
    border-radius:5px;
}

button{
    padding:10px 15px;
    border:none;
    background:#007bff;
    color:white;
    border-radius:5px;
    cursor:pointer;
}

button:hover{
    background:#0056b3;
}

#btn-entrar{
    background:#28a745;
}

#btn-entrar:hover{
    background:#1e7e34;
}

</style>

</head>

<body>

<div class="chat-container">

<div class="chat-header">
Chat Tiempo Real
</div>

<div id="chat"></div>

<div class="controls">

<div class="input-group">

<input
type="text"
id="nombre"
placeholder="Tu nombre">

<button
id="btn-entrar"
onclick="guardarNombre()">
Entrar
</button>

</div>

<div class="input-group">

<input
type="text"
id="mensaje"
placeholder="Escribe un mensaje">

<button onclick="enviar()">
Enviar
</button>

</div>

</div>

</div>

<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>

<script>

var socket = io();
var nombre = "";

function guardarNombre(){

    let input =
    document.getElementById("nombre");

    if(input.value.trim()==""){

        alert("Ingrese nombre");
        return;
    }

    nombre = input.value;

    input.disabled = true;

    document.getElementById(
        "btn-entrar"
    ).disabled = true;

    agregarSistema(
        nombre + " se unió al chat"
    );
}

function enviar(){

    let input =
    document.getElementById(
        "mensaje"
    );

    let mensaje =
    input.value;

    if(nombre==""){

        alert(
            "Ingrese nombre"
        );
        return;
    }

    if(mensaje.trim()==""){
        return;
    }

    socket.send(
        nombre + ": " + mensaje
    );

    input.value="";
}

socket.on(
    "message",
    function(msg){

        agregarChat(msg);
    }
);

socket.on(
    "telegram_message",
    function(msg){

        agregarChat(
            "📲 " + msg
        );
    }
);

socket.on(
    "emergencia",
    function(msg){

        agregarEmergencia(msg);
    }
);

function agregarChat(msg){

    let chat =
    document.getElementById("chat");

    let div =
    document.createElement("div");

    div.className="mensaje";

    div.innerHTML=msg;

    chat.appendChild(div);

    chat.scrollTop =
    chat.scrollHeight;
}

function agregarSistema(msg){

    agregarChat(
        "<strong>Sistema:</strong> "
        + msg
    );
}

function agregarEmergencia(msg){

    let chat =
    document.getElementById("chat");

    let div =
    document.createElement("div");

    div.className=
    "mensaje emergencia";

    div.innerHTML=
    "🚨 " + msg;

    chat.appendChild(div);

    chat.scrollTop =
    chat.scrollHeight;
}

</script>

</body>
</html>
"""



# WEB CHAT


@socket.on("message")
def recibirMensaje(mensaje):

    print("WEB:", mensaje)

    # Solo chat web
    send(
        mensaje,
        broadcast=True
    )
    comandosDeteccion(mensaje)

#Paso Extra. COnectar los comandos de activacion
def comandosDeteccion(mensaje):
    texto=mensaje.lower()

    for palabra, comando in palabrasClave.items():
        if palabra in texto:
            notificacion=f"""
            REPORTE MENSAJE CHAT WEB

            Comando:
            {comando}

            Palabra Detectada:
            {mensaje}

            Estado:
            En revision...
        """
            socket.emit(
                "ayuda",
                notificacion
            )
            threading.Thread(
                target=enviarTelegram,
                args=(notificacion,),
                daemon=True
            ).start()
            print("Notificacion Enviada...")
            break




# TELEGRAM SEND


def enviarTelegram(texto):

    url = (
        f"https://api.telegram.org/bot"
        f"{tokenTelegram}/sendMessage"
    )

    data = {

        "chat_id": chatID,
        "text": texto
    }

    try:

        requests.post(
            url,
            data=data,
            timeout=10
        )

    except Exception as e:

        print(
            "Telegram error:",
            e
        )



# TELEGRAM → WEB


async def recibirTelegram(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    usuario = (
        update.message
        .from_user
        .first_name
    )

    mensaje = update.message.text

    texto = (
        f"{usuario}: {mensaje}"
    )

    print(
        "TELEGRAM:",
        texto
    )

    socket.emit(
        "telegram_message",
        texto
    )



# BOT


def iniciarBot():

    asyncio.set_event_loop(
        asyncio.new_event_loop()
    )

    botTelegram.add_handler(

        MessageHandler(

            filters.TEXT
            &
            ~filters.COMMAND,

            recibirTelegram
        )
    )

    print(
        "BOT TELEGRAM ACTIVO"
    )

    botTelegram.run_polling()



# MAIN

if __name__ == "__main__":

    hiloBot = threading.Thread(
        target=iniciarBot,
        daemon=True
    )

    hiloBot.start()

    print(
        "Servidor iniciado"
    )

    puerto = int(os.getenv('PORT', 5000))
    socket.run(
        app,
        host="0.0.0.0",
        port=puerto,
        debug=False,
        allow_unsafe_werkzeug=True
    )