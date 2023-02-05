from twitchio.ext import commands
from twitchio import *
from datetime import datetime, timedelta
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit
from io import BytesIO

import asyncio
import threading
import pytz
import random 
from gtts import gTTS

socketio = SocketIO

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")
print(socketio.async_mode)
#python -m pip install twitchio flask flask_socketio pytz gtts simple-websocket pyglet
#
# make sure to pip uninstall eventlet also

@app.route("/")
def home():
    return render_template('index.html')#redirects to index.html in templates folder

@socketio.event
def connect(): #when socket connects send data confirming connection
    socketio.emit('message_send',
                    {'data': "Connected"})

def pyg_init():
    import pyglet
    global player
    player = pyglet.media.Player()
    pyglet.app.run()
    player.play()
    print(type(player))


def text_to_audio(text: str):
    import pyglet
    mp3 = BytesIO()
    input = gTTS(text,lang='en')
    input.write_to_fp(mp3)
    mp3.seek(0)
    audio = pyglet.media.load(None, file=mp3, streaming=False)
    player.queue(audio)
    player.play()

@socketio.on("tts")
def toggletts(value):
    print("tts " + str(value['data']))
    bot.tts_enabled = value['data']

class Bot(commands.Bot):
    first = True
    currentUser = ""
    tts_enabled = False

    def __init__(self):
        #connects to twitch channel
        self.tts_enabled = False
        super().__init__(token='e6yobed5d48tky6otlahj4mlwecqe7', prefix='?', initial_channels=['dougdougw'])
    

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')
        global userPool
        userPool = {} #dict of username and time last chatted

    async def event_message(self, message):
        await bot.process_message(message)
        if(bot.first): #picks the first random user AFTER someone talks in chat to init
            bot.randomUser()
            bot.first = False


    async def process_message(self, message: Message):
        if message.author.name.lower() in userPool:
            userPool.pop(message.author.name.lower())
        userPool[message.author.name.lower()] = message.timestamp 
        # update time last chatted of the user and add to the end of the dict
        seconds = 60
        time_x = datetime.now(pytz.utc) - timedelta(seconds=seconds) # get the time 2 min ago uct
        least_most_reacent_user = list(userPool.keys())[0] # get the first user in the dict which will be the user that has chatted the longest ago
        if userPool[least_most_reacent_user].replace(tzinfo=pytz.utc) < time_x: # if the least most recent user user last chatted more then x min ago
            userPool.pop(least_most_reacent_user) # remove them from the list
            print(f"{least_most_reacent_user} was popped due to not talking for {seconds} seconds")
        #this all works because whenever someone gets added to the list someone else will get removed but only if they havn't talked in the last 2 min

        if not bot.first:
            if message.author.name == bot.currentUser:
                socketio.emit('message_send',
                {'data': f"{bot.currentUser}: {message.content}"})
                if bot.tts_enabled:
                    text_to_audio(message.content)
                print(bot.currentUser + ": " + message.content)
    #picks a random user from the queue
    def randomUser(this):
        try:
            bot.currentUser = random.choice(list(userPool.keys()))
        except Exception:
            return
        socketio.emit('message_send',{'data': f"{bot.currentUser} was picked!"})
        print("Random User is: " + bot.currentUser)

@socketio.on("pickrandom")
def pickrandom():
    bot.randomUser()

@socketio.on("choose")
def toggletts(value):
    print("Choose User Is: " + str(value['data']))
    bot.currentUser = (value['data']).lower()
    bot.first = False
    socketio.emit('message_send',{
        'data' : f'Choose User: {bot.currentUser}'
    })


def startBot():
    global bot
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot = Bot()
    bot.run()


if __name__=='__main__':
    global bot_thread; global audio_thread
    bot_thread = threading.Thread(target=startBot)
    bot_thread.start()
    audio_thread = threading.Thread(target=pyg_init)
    audio_thread.start()
    socketio.run(app)