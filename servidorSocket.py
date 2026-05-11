import socket
import threading

host="0.0.0.0"
puerto=5000

clientes=[]
nombres=[]

def enviarMensajeTodos(mensaje,clienteActual):
    for cliente in clientes:
        if cliente !=clienteActual:
            try:
                cliente.send(mensaje)
            except:
                clientes.remove(cliente)

def manejarCliente(cliente):
    while True:
        try:
            mensaje=cliente.recv(1024)
            if mensaje:
                enviarMensajeTodos(mensaje,cliente)
        except:
            clientes.remove(cliente)
            cliente.close()
            break

def iniciarServidor():
    servidor=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    servidor.bind((host,puerto))
    servidor.listen()
    print("Servidor Activo escuchando solicitudes...")
    while True:
        cliente,direccion=servidor.accept()
        #Solicitar autentificacion
        cliente.send("Nombre".encode("utf-8"))
        nombre=cliente.recv(1024).decode("utf-8")
        nombres.append(nombre)
        print(f"{nombre} se unio al chat...")

        print("Servidor conectado con las ips",direccion)
        clientes.append(cliente)
        hilo=threading.Thread(target=manejarCliente,args=(cliente,))
        hilo.start()

iniciarServidor()

