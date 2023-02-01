from twitchio.ext import commands
from twitchio import *
from datetime import datetime, timedelta
from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit
from threading import Lock
import asyncio
import threading
import pytz
import random

socketio = SocketIO

app = Flask(__name__)
socketio = SocketIO(app, async_mode=None)
thread = None
thread_lock = Lock()

@app.route("/")
def home():
    return render_template('index.html')

@socketio.event
def connect():
    global thread
    print(1)
    with thread_lock:
        print(2)
        if thread is None:
            print(3)
            thread = threading.Thread(target=startBot)
            thread.start()
            print(thread.getName)
    socketio.emit('connectt',
                    {'data': "connected"})

class Bot(commands.Bot):
    first = True
    currentUser = ""

    def __init__(self):
        #connects to your twitch channel
        super().__init__(token='e6yobed5d48tky6otlahj4mlwecqe7', prefix='?', initial_channels=['dougdougw'])

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')
        global userPool
        userPool = {} #dict of username and time last chatted

    async def event_message(self, message):
        await bot.process_message(message)
        if(bot.first): #picks the first random user AFTER someone talks in chat to init
            await bot.randomUser()
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
                print(bot.currentUser + ": " + message.content)
    
    #picks a random user from the queue
    async def randomUser(this):
        bot.currentUser = random.choice(list(userPool.keys()))
        print("Random User is: " + bot.currentUser)


def startBot():
    global bot
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot = Bot()
    bot.run()


if __name__=='__main__':
    socketio.run(app)
