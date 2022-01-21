from discord.ext import commands
from json import load
from discord.channel import DMChannel

# Default values
DEFAULT_PREFIX = "!"
DEFAULT_LB_SIZE = 15
DEFAULT_CHANNEL = ''
DEFAULT_MAX_REPLY = 3
config = load(open('config.json'))

# General
token = config['General']['Discord Token']
admin_id = config['General']['Admin id']
master_logger_id = config['General']['master logging channel id']
music_servers_id = config['General']['special slash command guilds']
# Database
host = config['mysql']['host']
Database = config['mysql']['database']
user = config['mysql']['user']
password = config['mysql']['password']
# Api keys
spotify_client_id = config['API Keys']['Spotify client id']
spotify_client_secret = config['API Keys']['Spotify client secret']
youtube_developerkey = config['API Keys']['YouTube developerKey']
genius_developer_key = config['API Keys']['Genius developer key']
google_api_key = config['API Keys']['Google API key']


async def get_prefix(client, msg):
    if isinstance(msg.channel, DMChannel):  # Prevents error upon DM chat (DM does not have a guild)
        return commands.when_mentioned_or(DEFAULT_PREFIX)(client, msg)
    else:
        return commands.when_mentioned_or(client.db.get_guild_info(msg.guild.id)[1])(client, msg)
           

async def get_configdata(client, guild_did, request):
    data = client.db.get_guild_info(guild_did)
    if data is None:  # Fail safe if guild does not have data
        client.db.update_guild_info(guild_did, DEFAULT_PREFIX,
                                    DEFAULT_CHANNEL, DEFAULT_CHANNEL,
                                    DEFAULT_CHANNEL, DEFAULT_CHANNEL,
                                    DEFAULT_CHANNEL, DEFAULT_LB_SIZE,
                                    DEFAULT_CHANNEL, DEFAULT_CHANNEL,
                                    DEFAULT_MAX_REPLY, DEFAULT_CHANNEL,
                                    DEFAULT_CHANNEL)
        data = client.db.get_guild_info(guild_did)
    switcher = {
        'command_prefix': data[1],
        "logger_ids": 2,
        "polly_channel_id": 3,
        "poll_maker_id": 4,
        "clvl_channel_id": 5,
        "word_snake__channel_id": 6,
        "lb_size": data[7],
        "ntbpl_channel_id": 8,
        "HL_channel_id": 9,
        "HL_max_reply": data[10],
        "connect4_id": 11,
        "hangman_id": 12
    }
    if request not in ['lb_size', 'command_prefix', 'HL_max_reply']:
        try:
            to_send = list(map(int, data[switcher[request]].split(',')))
        except ValueError:  # If string does not contain any ids (DEFAULT_CHANNEL = '')
            to_send = [0]
        return to_send
    else:
        return switcher[request]


class config_handler(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_join(self, guild):  #Creates guild info upon join
        self.client.db.update_guild_info(guild.id, DEFAULT_PREFIX,
                                         DEFAULT_CHANNEL, DEFAULT_CHANNEL,
                                         DEFAULT_CHANNEL, DEFAULT_CHANNEL,
                                         DEFAULT_CHANNEL, DEFAULT_LB_SIZE,
                                         DEFAULT_CHANNEL, DEFAULT_CHANNEL,
                                         DEFAULT_MAX_REPLY, DEFAULT_CHANNEL,
                                         DEFAULT_CHANNEL )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):  #Deletes guild info when leaving
        self.client.db.delete_guild_data(guild.id)


def setup(client):
    client.add_cog(config_handler(client))
