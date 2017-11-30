# -*- coding: utf-8 -*-

from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, send
import paho.mqtt.client as mqtt
import sys


app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisupposedtobesecret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

Bootstrap(app)
db = SQLAlchemy(app) # obj de acesso ao banco
socketio = SocketIO(app)

reload(sys)  
sys.setdefaultencoding('utf8')

MQTT_ADDRESS = 'iot.eclipse.org'
MQTT_PORT = 1883
MQTT_TIMEOUT = 60

class History(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	message = db.Column('message', db.String(500))

class Mensagem(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	topico =db.Column(db.String(200))
	conteudo= db.Column(db.String(200))
db.create_all()

class RegisterMensagem(FlaskForm):
	topico = StringField('topico', validators=[InputRequired(), Length(min=4, max =200)])
	conteudo = StringField('conteudo', validators=[InputRequired(), Length(min=4, max =200)])



if sys.version_info[0] == 3:
	input_func = input
else:
	input_func = raw_input

def on_connect(client, userdata, flags, rc):
 #   print('Conectado. Resultado: %s' % str(rc))
	result, mid = client.subscribe('/buteco/topico')
 #   print('Inscrevendo-se no tópico "/buteco/topico" (%d)' % mid)


#def on_subscribe(client, userdata, mid, granted_qos):
#    print('Inscrito no tópico: %d' % mid)
def on_subscribe(client, userdata, mid, granted_qos):
    index()

def on_message(client, userdata, msg):
	if msg.topic == '/buteco/topico':
		new_mensagem = Mensagem(conteudo= msg.payload, topico=msg.topic)
		#db.session.add(new_Comentario)
		#db.session.commit()
	#else:
	  #  print('Tópico desconhecido.')

def send_message(msg):
	client = mqtt.Client()
	# descomente esta linha caso seu servidor possua autenticação.
	# client.username_pw_set(MQTT_AUTH.user, MQTT_AUTH.pwd)
	client.connect(MQTT_ADDRESS, MQTT_PORT, MQTT_TIMEOUT)
	result, mid = client.publish('/buteco/topico', msg)

def loop():
	client = mqtt.Client()
	client.on_connect = on_connect
	client.on_subscribe = on_subscribe
	client.on_message = on_message
	# descomente esta linha caso seu servidor possua autenticação.
	# client.username_pw_set(MQTT_AUTH.user, MQTT_AUTH.pwd)
	client.connect(MQTT_ADDRESS, MQTT_PORT, MQTT_TIMEOUT)
	#client.loop_forever()

@socketio.on('message' )
def handleMessage(msg):
	print('Message: ' + msg)

	message = History(message=msg)
	db.session.add(message)
	db.session.commit()

	send(msg, broadcast=True)# manda para todos

@app.route('/', methods=['GET','POST'])
def index():
	messages = History.query.all()
	return render_template('index.html', messages=messages)
	loop()
	mensagem = Mensagem.query.all()
	form = RegisterMensagem()

	if form.validate_on_submit():
	    send_message(form.conteudo.data)
		#new_Comentario = Comentario( idpost=id, comentario=form.comentario.data )
		#new_user = User(username=form.username.data, email=form.username.data, password=form.password.data)
		#db.session.add(new_Comentario)
		#db.session.commit()

	return render_template('index.html', form=form, mensagem=mensagem)    


if __name__ == '__main__':
	socketio.run(app)

