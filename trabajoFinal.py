from flask import Flask
from flask_socketio import SocketIO, send
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes
)

# CREAR APP


app = Flask(__name__)


# CONFIGURAR SOCKETIO


socket = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet"
)


# CREAR BOT TELEGRAM


botTelegram = ApplicationBuilder().token(
    tokenTelegram
).build()


# PAGINA PRINCIPAL


@app.route("/")
def index():

    return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Tiempo Real</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        :root { --primary: #2563eb; --bg: #f3f4f6; }
        body { background: var(--bg); font-family: 'Segoe UI', Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .chat-card { width: 90%; max-width: 450px; height: 80vh; background: white; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); display: flex; flex-direction: column; overflow: hidden; }
        .header { background: var(--primary); color: white; padding: 15px; text-align: center; font-weight: bold; font-size: 1.2rem; }
        #messages { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 8px; background: #fafafa; }
        .msg { padding: 8px 12px; border-radius: 8px; max-width: 80%; font-size: 0.95rem; line-height: 1.4; position: relative; }
        .other { background: #e5e7eb; align-self: flex-start; color: #1f2937; }
        .own { background: #dbeafe; align-self: flex-end; color: #1e40af; }
        .sender-name { font-size: 0.7rem; font-weight: bold; display: block; margin-bottom: 2px; opacity: 0.8; }
        .controls { display: flex; padding: 15px; gap: 10px; border-top: 1px solid #eee; }
        input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 6px; outline: none; }
        button { background: var(--primary); color: white; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; }
        .screen { display: none; flex-direction: column; height: 100%; }
        .active { display: flex; }
    </style>
</head>
<body>
    <div class="chat-card">
        <!-- Pantalla de Login -->
        <div id="login" class="screen active" style="justify-content: center; padding: 40px; text-align: center;">
            <h2 style="color: var(--primary)">Bienvenido al Chat</h2>
            <input type="text" id="username" placeholder="Escribe tu nombre..." style="margin-bottom: 20px;">
            <button onclick="conectar()">Entrar al Chat</button>
        </div>

        <!-- Pantalla de Chat -->
        <div id="chat-ui" class="screen">
            <div class="header">Chat Tiempo Real</div>
            <div id="messages"></div>
            <div class="controls">
                <input type="text" id="msgInput" placeholder="Escribe un mensaje..." onkeypress="if(event.key==='Enter') enviar()">
                <button onclick="enviar()">Enviar</button>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let nombre = "";

        function conectar() {
            const nom = document.getElementById('username').value.trim();
            if(!nom) return alert('Ingrese su nombre');
            nombre = nom;
            document.getElementById('login').classList.remove('active');
            document.getElementById('chat-ui').classList.add('active');
            // Mostrar localmente sin enviar al servidor (evita spam a Telegram)
            agregarLocal('Sistema', nombre + ' se unió al chat');
        }

        function enviar() {
            const input = document.getElementById('msgInput');
            if(!nombre) return alert('Debe ingresar su nombre');
            if(input.value.trim()) {
                socket.send(nombre + ': ' + input.value);
                input.value = '';
            }
        }

        socket.on('message', function(msg) {
            const container = document.getElementById('messages');
            const div = document.createElement('div');
            const esMio = msg.startsWith(nombre + ":");
            div.className = 'msg ' + (esMio ? 'own' : 'other');

            if(!esMio && msg.includes(':')) {
                const [user, ...texto] = msg.split(':');
                div.innerHTML = `<span class="sender-name">${user}</span> ${texto.join(':')}`;
            } else {
                div.textContent = msg.replace(nombre + ": ", "");
            }

            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        });

        // Mensajes que vienen desde Telegram (el servidor emite 'telegram_message')
        socket.on('telegram_message', function(msg){
            const container = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = 'msg other';
            div.innerHTML = `<span class="sender-name">Telegram</span> ${msg.replace(/^Telegram:\\s*/, '')}`;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        });

        function agregarLocal(usuario, texto){
            const container = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = 'msg other';
            div.innerHTML = `<span class="sender-name">${usuario}</span> ${texto}`;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }
    </script>
</body>
</html>
"""

    if(msg.includes(":")){

        let partes = msg.split(":");

        div.innerHTML =
            "<strong>" +
            partes[0] +
            ":</strong> " +
            partes.slice(1).join(":");

    }else{

        div.innerText = msg;
    }
=======
    return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Tiempo Real</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        :root { --primary: #2563eb; --bg: #f3f4f6; }
        body { background: var(--bg); font-family: 'Segoe UI', Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .chat-card { width: 90%; max-width: 450px; height: 80vh; background: white; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); display: flex; flex-direction: column; overflow: hidden; }
        .header { background: var(--primary); color: white; padding: 15px; text-align: center; font-weight: bold; font-size: 1.2rem; }
        #messages { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 8px; background: #fafafa; }
        .msg { padding: 8px 12px; border-radius: 8px; max-width: 80%; font-size: 0.95rem; line-height: 1.4; position: relative; }
        .other { background: #e5e7eb; align-self: flex-start; color: #1f2937; }
        .own { background: #dbeafe; align-self: flex-end; color: #1e40af; }
        .sender-name { font-size: 0.7rem; font-weight: bold; display: block; margin-bottom: 2px; opacity: 0.8; }
        .controls { display: flex; padding: 15px; gap: 10px; border-top: 1px solid #eee; }
        input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 6px; outline: none; }
        button { background: var(--primary); color: white; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; }
        .screen { display: none; flex-direction: column; height: 100%; }
        .active { display: flex; }
    </style>
</head>
<body>
    <div class="chat-card">
        <!-- Pantalla de Login -->
        <div id="login" class="screen active" style="justify-content: center; padding: 40px; text-align: center;">
            <h2 style="color: var(--primary)">Bienvenido al Chat</h2>
            <input type="text" id="username" placeholder="Escribe tu nombre..." style="margin-bottom: 20px;">
            <button onclick="conectar()">Entrar al Chat</button>
        </div>

        <!-- Pantalla de Chat -->
        <div id="chat-ui" class="screen">
            <div class="header">Chat Tiempo Real</div>
            <div id="messages"></div>
            <div class="controls">
                <input type="text" id="msgInput" placeholder="Escribe un mensaje..." onkeypress="if(event.key==='Enter') enviar()">
                <button onclick="enviar()">Enviar</button>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let nombre = "";

        function conectar() {
            const nom = document.getElementById('username').value.trim();
            if(!nom) return alert('Ingrese su nombre');
            nombre = nom;
            document.getElementById('login').classList.remove('active');
            document.getElementById('chat-ui').classList.add('active');
            // Mostrar localmente sin enviar al servidor (evita spam a Telegram)
            agregarLocal('Sistema', nombre + ' se unió al chat');
        }

        function enviar() {
            const input = document.getElementById('msgInput');
            if(!nombre) return alert('Debe ingresar su nombre');
            if(input.value.trim()) {
                socket.send(nombre + ': ' + input.value);
                input.value = '';
            }
        }

        socket.on('message', function(msg) {
            const container = document.getElementById('messages');
            const div = document.createElement('div');
            const esMio = msg.startsWith(nombre + ":");
            div.className = 'msg ' + (esMio ? 'own' : 'other');

            if(!esMio && msg.includes(':')) {
                const [user, ...texto] = msg.split(':');
                div.innerHTML = `<span class="sender-name">${user}</span> ${texto.join(':')}`;
            } else {
                div.textContent = msg.replace(nombre + ": ", "");
            }

            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        });

        // Mensajes que vienen desde Telegram (el servidor emite 'telegram_message')
        socket.on('telegram_message', function(msg){
            const container = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = 'msg other';
            div.innerHTML = `<span class="sender-name">Telegram</span> ${msg.replace(/^Telegram:\\s*/, '')}`;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        });

        function agregarLocal(usuario, texto){
            const container = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = 'msg other';
            div.innerHTML = `<span class="sender-name">${usuario}</span> ${texto}`;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }
    </script>
</body>
</html>
"""
>>>>>>> 54eb5fe (Apply chatOnline styles to trabajoFinal.py)

    chat.appendChild(div);

    chat.scrollTop = chat.scrollHeight;
}

// =====================================
// MENSAJE LOCAL
// =====================================

function agregarMensaje(usuario, texto){

    let chat = document.getElementById("chat");

    let div = document.createElement("div");

    div.className = "mensaje";

    div.innerHTML =
        "<strong>" +
        usuario +
        ":</strong> " +
        texto;

    chat.appendChild(div);
}

</script>

</body>
</html>
"""

# MENSAJES DESDE WEB


@socket.on("message")
def recibirMensaje(mensaje):

    print("Mensaje WEB:", mensaje)

    # Mostrar a todos los clientes WEB
    send(mensaje, broadcast=True)

    # Enviar a Telegram
    threading.Thread(
        target=enviarTelegram,
        args=(mensaje,)
    ).start()


# ENVIAR A TELEGRAM


def enviarTelegram(mensaje):

    url = (
        f"https://api.telegram.org/bot"
        f"{tokenTelegram}/sendMessage"
    )

    data = {
        "chat_id": chatID,
        "text": f"{mensaje}"
    }

    try:

        requests.post(url, data=data)

    except Exception as e:

        print("Error Telegram:", e)


# RECIBIR DESDE TELEGRAM


async def recibirTelegram(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    usuario = update.message.from_user.first_name

    mensaje = update.message.text

    texto = f"{usuario}: {mensaje}"

    print("Telegram:", texto)

    # SOLO enviar a WEB
    socket.emit(
        "telegram_message",
        texto
    )


# INICIAR BOT


def iniciarBot():

    botTelegram.add_handler(

        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            recibirTelegram
        )
    )

    print("BOT TELEGRAM ACTIVO")

    botTelegram.run_polling()


# MAIN


if __name__ == "__main__":

    hiloBot = threading.Thread(
        target=iniciarBot
    )

    hiloBot.start()

    print("Servidor iniciado")

    socket.run(
        app,
        host="0.0.0.0",
        port=5000
    )