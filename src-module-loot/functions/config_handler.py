from json import load
from datetime import datetime

config = load(open('config.json'))

TOKEN = config['Token']
BOT_ID = config['Bot-id']

GUILD_IDS = config['Guild ids']
Q_CHANNEL_ID = config['Queue channel id']
S_CHANNEL_ID = config['Sub channel id']

host = config['mysql']['host']
database = config['mysql']['database']
user = config['mysql']['user']
password = config['mysql']['password']


def time():
    return str(datetime.now().strftime("%d/%m/%y -- %H:%M:%S"))