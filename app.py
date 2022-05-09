import json
from flask import  Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import nltk #lenguaje natural
from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()
import numpy 
import tensorflow
import tflearn
import random
import pandas as pd
import numpy as np
import markdown
import time
import pickle
from pandas.io.json import json_normalize
from twilio.rest import Client
from waitress import serve
import subprocess
from pydub import audio_segment

#from Item import *
nltk.download('punkt')

app = Flask(__name__)


@app.route('/')
def hello():
	print("siiii")
	return ("Services chatbot up")

def getData(msg, num):
	df = pd.DataFrame({'Mensaje': [msg], 'Numero': [num]})
	df.to_csv('mensajes.csv', mode='a', index=False, header=False)
	return "ok"

@app.route("/sms", methods=['POST'])

def sms_reply():
	#responde a las llamadas entrantes con un simple mensaje de texto
	# capta el mensaje
	men = []
	global msg
	msg = request.form.get('Body')
	num = request.form.get('From')
	audio = request.form.get('MediaUrl0')
	print(audio, "siiiiiiiiiiiiiiiiiiiiiiii")
	print(num)
	print(msg)

	resp = MessagingResponse()
	msgs = resp.message()
	print(msg)

	responded = False

	getData(msg, num)
	men.append(msg)


	if audio == None:
		msg = msg

	else:
		urls = audio
		print(urls, "hhhhhhhhhhhhhhh")

		myfile = requests.get(urls)

		y = myfile.content
		
		open('C:/Users/angieolarte/Downloads/codigo/Angie/audio.opus', 'wb').write(myfile.content)

		command = "ffmpeg -i C:/Users/angieolarte/Downloads/codigo/Angie/audio.opus -ab 160k -ac 2 -ar 44100 -vn C:/Users/angieolarte/Downloads/codigo/Angie/audio.wav"
		subprocess.call(command, shell=True)

		r = sr.Recognizer()

		with sr.AudioFile("C:/Users/angieolarte/Downloads/codigo/Angie/audio.wav") as source:
			audio = r.listen(source)

			text = r.recognize_google(audio, language="es-Es")

		print(text, "tttttttttttttttttttttt")

		msg = text

	

	with open("contenidoRed.json", 'r') as archivo:
		datos = json.load(archivo)
	try:
		with open("variables.pickle", "rb") as archivoPickle:
			palabras, tags, entrenamiento, salida = pickle.load(archivoPickle)
	except:
		palabras=[]
		tags=[]
		auxX=[] #auxiliares 
		auxY=[]
		for contenido in datos["contenido"]:
			for patrones in contenido["patrones"]: #acceder a cualquier elemento
				auxPalabra = nltk.word_tokenize(patrones) #separar palabras Reconocer puntos especiales
				palabras.extend(auxPalabra)
				auxX.append(auxPalabra)
				auxY.append(contenido["tag"])
				if contenido["tag"] not in tags:	
					tags.append(contenido["tag"])
	#Entranamiento aprendizaje automatico
		palabras = [stemmer.stem(w.lower())for w in palabras if w!="?"]#pasar todas las palabras en minuscular
		palabras = sorted(list(set(palabras)))
		tags = sorted(tags)
		entrenamiento = []
		salida=[]
		salidaVacia = [0 for _ in range(len(tags))]
		for x, documento in enumerate(auxX):
			cubeta=[]
			auxPalabra=[stemmer.stem(w.lower()) for w in documento]
			for w in palabras:
				if w in auxPalabra:
					cubeta.append(1)	
				else:
					cubeta.append(0)
			filaSalida = salidaVacia[:]	
			filaSalida[tags.index(auxY[x])]=1
			entrenamiento.append(cubeta)
			salida.append(filaSalida)
	#Definición redes neuronales a utilizar
		entrenamiento = numpy.array(entrenamiento)
		salida = numpy.array(salida)

		with open ("variables.Pickle", "wb") as archivoPickle:
			pickle.dump((palabras, tags, entrenamiento, salida), archivoPickle)

	tensorflow.reset_default_graph()
	red = tflearn.input_data(shape=[None,len(entrenamiento[0])])
	red = tflearn.fully_connected(red,100)
	red = tflearn.fully_connected(red,len(salida[0]),activation="softmax")
	red = tflearn.regression(red) #probabilidades
	modelo = tflearn.DNN(red)
	modelo.fit(entrenamiento,salida,n_epoch=1000,batch_size=100,show_metric=True) 
	modelo.save("modelo.tflearn")

	entrada = str(msg)
	cubeta = [0 for _ in range(len(palabras))]
	entradaProcesada = nltk.word_tokenize(entrada)
	entradaProcesada = [stemmer.stem(palabra.lower()) for palabra in entradaProcesada]
	for palabraIndividual in entradaProcesada:
		for i,palabra in enumerate(palabras):
			if palabra == palabraIndividual:
				cubeta[i]=1
	resultados =modelo.predict([numpy.array(cubeta)])
	resultadosIndices = numpy.argmax(resultados)
	global tag
	tag = tags[resultadosIndices]
	print(tag, "---------------------------------------")
	men.append(tag)
	#Primera intencion del bot saludo

	mens = len(men)
	print(mens,"---------------------")
	j = men[mens-1]
	print(j,"///////////////////////////////////")
	

	if "Saludo" == j:
		print ("holaaaaaa")
		
		respuesta =("Hola Bienvenido a Mi restaurante soy BOTTENDER y es un gusto poder ayudarte, a continuación tienes una serie de opciones"
					"que puedes elegir según lo que quieras consultar:\n\n*1.* Sobre el restaurante \n*2.* Ver el menú"
					"\n*3.* Solicitud de la cuenta\n\n Recuerda visitar nuestra pagina web https://www.mirestaurante.co/")
		msgs.body(respuesta)
		responded = True

	elif "Adios" == j:
		account_sid = 'AC8da8a9cea41f4beea9da71f5df398852'
		auth_token = '0248b3cb7f1a78ae0169cd03e8744369'
		client = Client(account_sid, auth_token)
		from_whatsapp_number = 'whatsapp:+14155238886'
		to_whatsapp_number = num  
		message = client.messages.create(body='Gracias por contactar a Mi restaurante, Siguenos en nuestras Redes Sociales y ¡vuelve pronto! \nhttps://www.mirestaurante.co/',
									media_url=['https://user-images.githubusercontent.com/24567596/167457622-41b3581e-7265-4c37-94b2-bac8f8e593e4.png'],
									from_=from_whatsapp_number,
									to=to_whatsapp_number)
		msgs.body(respuesta)
		responded = True
		
		
	
	elif "1" == j:
		respuesta = ("Mi restaurante es un gastrobar que te ayudara a agilizar tu pedido\n"
		"\n*-* Las carnes mas deliciosas \n*-* Exquisitas bebidas \n*-* Atención rapida"
		"\n*-* Precios inigualables \n*-* La mejor atención")
		msgs.body(respuesta)
		responded = True

	elif "2" == j:
		account_sid = 'AC8da8a9cea41f4beea9da71f5df398852'
		auth_token = '0248b3cb7f1a78ae0169cd03e8744369'
		client = Client(account_sid, auth_token)
		from_whatsapp_number = 'whatsapp:+14155238886'
		to_whatsapp_number = num  
		message = client.messages.create(body='',
									media_url=['https://user-images.githubusercontent.com/24567596/167451003-bce31169-7e52-46ab-a168-dc07d97e2ee9.png'],
									from_=from_whatsapp_number,
									to=to_whatsapp_number)

		time.sleep(2)
		respuesta = ("Puedes pedir lo que necesites de nuestro menú")
		msgs.body(respuesta)
		responded = True

	elif "3" == j:
		respuesta = ("En 5 minutos nuestro personal irá a tu mesa con las diferentes opciones de pago"
			"\n https://pagos.mirestaurante.com/")
		msgs.body(respuesta)
		responded = True

	
	return str(resp)
if __name__ == "__main__":
	app.run(debug=True)

