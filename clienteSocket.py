#Importar las librerias
import socket
import threading

host="192.168.172.254"
puerto=5000

def recibirMensajes(cliente):
    while True:
        try:
            mensaje=cliente.recv(1024).decode("utf-8")
            print(mensaje)
        except:
            print("Error al recibir el mensaje")
            cliente.close()
            break

def enviarMensajes(cliente):
    while True:
        mensajes=input("Ingrese su mensaje: ")
        mensajeFinal=f"{nombre}: {mensajes}"
        
        cliente.send(mensajeFinal.encode("utf-8"))

nombre=input("Ingrese su nombre: ")

def inicioCliente():
    cliente=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    cliente.connect((host,puerto))
    print("Conectado al chat...")

    hiloRecibir=threading.Thread(target=recibirMensajes,args=(cliente,))
    hiloRecibir.start()

    enviarMensajes(cliente)

inicioCliente()
