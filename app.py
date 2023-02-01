from twitchio.ext import commands
from twitchio import *
from datetime import datetime, timedelta
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit
from threading import Lock
from io import BytesIO
import asyncio
import threading
import pytz
import random 
from gtts import gTTS

socketio = SocketIO

app = Flask(__name__)
socketio = SocketIO(app, async_mode=None)
thread = None
thread_lock = Lock()

#idk why but this script speiciflly only works if you DON'T have eventlet installed so make sure to pip uninstall eventlet

@app.route("/")
def home():
    return render_template('index.html')#redirects to index.html in templates folder

@socketio.event
def connect(): #when socket connects send data confirming connection
    socketio.emit('connectt',
                    {'data': "connected"})

class Bot(commands.Bot):
    first = True
    currentUser = ""

    def __init__(self):
        #connects to twitch channel
        super().__init__(token='e6yobed5d48tky6otlahj4mlwecqe7', prefix='?', initial_channels=['bananababoo'])

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
        if message.author.name in userPool:
            userPool.pop(message.author.name)
        userPool[message.author.name] = message.timestamp 
        # update time last chatted of the user and add to the end of the dict
        two_min_ago = datetime.now(pytz.utc) - timedelta(minutes=2) # get the time 2 min ago uct
        least_most_reacent_user = list(userPool.keys())[0] # get the first user in the dict which will be the user that has chatted the longest ago
        if userPool[least_most_reacent_user].replace(tzinfo=pytz.utc) < two_min_ago: # if the least mos _reacent user user last chatted 2 min ago
            userPool.pop(least_most_reacent_user) # remove them from the list
            print(f"{least_most_reacent_user} was popped due to not talking in 2 minuets")
        #this all works because whenever someone gets added to the list someone else will get removed but only if they havn't talked in the last 2 min

        if not bot.first:
            if message.author.name == bot.currentUser:
                socketio.emit('my_response',
                    {'data': f"{bot.currentUser}: {message.content}"})
                try:
                    if tts_enabled:
                        text_to_audio(message.content)
                    print(bot.currentUser + ": " + message.content)
                except NameError:
                    pass
    
    #picks a random user from the queue
    def randomUser(this):
        bot.currentUser = random.choice(list(userPool.keys()))
        socketio.emit('randompicked',{'data': f"{bot.currentUser} was picked!"})
        print("Random User is: " + bot.currentUser)

@socketio.on("pickrandom")
def pickrandom():
    bot.randomUser()

@socketio.on("tts")
def toggletts(value):
    print("tts enabled " + str(value['data']))
    global tts_enabled
    tts_enabled = value['data']

def text_to_audio(text: str):
    import pyglet
    mp3 = BytesIO()
    input = gTTS(text,lang='en')
    input.write_to_fp(mp3)
    mp3.seek(0)
    audio = pyglet.media.load(None, file=mp3, streaming=False)
    player.queue(audio)
    player.play()

def startBot():
    global bot
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot = Bot()
    bot.run()

def pyg_init():
    import pyglet
    global player
    player = pyglet.media.Player()
    pyglet.app.run()
    player.play()
    print(type(player))


if __name__=='__main__':
    thread = threading.Thread(target=startBot)
    thread.start()
    thread = threading.Thread(target=pyg_init)
    thread.start()
    socketio.run(app)