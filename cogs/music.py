import youtube_dl
from math import floor
from json import loads
from regex import match
from requests import get
from random import shuffle
from discord import Reaction
from discord.ext import commands
from discord.embeds import Embed
from asyncio import sleep as asyncio_sleep
from discord.voice_client import VoiceClient
from discord.player import FFmpegOpusAudio
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_slash import SlashContext, cog_ext
from imports.sleep_class import Sleeper
from imports.spotifyapi import Spotify_api
from imports.youtubeapi import playlist_to_urllist, search
from cogs.config_handler import music_servers_id, genius_developer_key, google_api_key
from lyricsgenius import Genius


def db_dict(url: str, title: str, author: str, link_type: str, req: str):
    return {"url": url, "title": title, "author": author, "type": link_type, 'req': req}


async def slash_error(ctx: SlashContext, txt: str):
    await ctx.defer(hidden=True)
    await ctx.send(txt, hidden=True)


async def play_song(self, ctx: SlashContext, vc: VoiceClient, url):
    ffmpeg_option = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    ydl_option = {'format': 'bestaudio'}
    with youtube_dl.YoutubeDL(ydl_option) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['formats'][0]['url']
        source = await FFmpegOpusAudio.from_probe(url2, **ffmpeg_option)
        vc.play(source=source)
        await self.sleep_handler.sleep(int(info['duration']))
        if (data := self.client.db.get_music(ctx.guild.id)) is not None:
            q = data[3].split(';')
            if q != ['']:
                if data[5] + 1 == len(q) and data[4] != 1:
                    self.client.db.del_music(ctx.guild.id)
                    await asyncio_sleep(120)
                    if self.client.db.get_music(ctx.guild.id) is None:
                        await ctx.voice_client.disconnect()
                        self.current_q = 0
                        await self.client.get_channel(ctx.channel_id).send("I haven't played music for 2 min,"
                                                                           " disconnected myself :)")
                else:
                    next_q_place = data[5] + 1 if data[5] + 1 < len(q) else 0
                    song_info = eval(q[next_q_place])
                    if song_info['type'] == 'spotify_link':
                        new_url = search(song_info['author'] + " " + song_info['title'])['url']
                    else:
                        new_url = song_info['url']
                    self.client.db.update_music(data[0], data[1], data[2], ';'.join(q), data[4], next_q_place)
                    await play_song(self, ctx, vc, new_url)


class music(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client
        self.current_q = 0
        self.sleep_handler = Sleeper()
        self.genius = Genius(genius_developer_key)

    @cog_ext.cog_slash(name="join",
                       description="Summon me to your current voice channel.",
                       guild_ids=music_servers_id
                       )
    async def _join(self, ctx: SlashContext):
        if (data := self.client.db.get_music(ctx.guild.id)) is not None:
            await ctx.send(f'Music is already playing in <#{data[1]}>, commands are bound to <#{data[2]}>.')
        else:
            if (v_channel := ctx.author.voice.channel) is not None:
                self.client.db.update_music(ctx.guild.id, v_channel.id, ctx.channel.id, "")
                await v_channel.connect()
                await ctx.send(f"Connected to <#{v_channel.id}>, and bound commands to <#{ctx.channel.id}>.")
            else:
                await ctx.send(f"You have to be in a voice channel to use this command.")

    @cog_ext.cog_slash(name="leave",
                       description="Remove me from your voice channel.",
                       guild_ids=music_servers_id
                       )
    async def _leave(self, ctx: SlashContext):
        if (data := self.client.db.get_music(ctx.guild.id)) is not None:
            if ctx.channel.id == data[2] and (vc := self.client.voice_clients) is not None and ctx.author.voice is not None:
                if data[1] == ctx.author.voice.channel.id:
                    for i in vc:
                        if i.channel.id == data[1]:
                            await i.disconnect()
                    self.current_q = 0
                    await ctx.send(f"Disconnected myself.")
                    self.client.db.del_music(ctx.guild.id)
                    await self.sleep_handler.cancel_all()
                else:
                    await slash_error(ctx, f'You have to be in the same voice channel to disconnect. <#{data[1]}>')
            else:
                await slash_error(ctx, f"You are required to be in the right channel <#{data[2]}>")
        else:
            await slash_error(ctx, "Cannot disconnect when not connected in the first place.")

    @cog_ext.cog_slash(name="Nowplaying",
                       description="Display current song",
                       guild_ids=music_servers_id
                       )
    async def _nowplaying(self, ctx: SlashContext):
        if (data := self.client.db.get_music(ctx.guild_id)) is not None:
            if ctx.channel_id == data[2]:
                song_info = eval(data[3].split(";")[data[5]])
                description = f"[{song_info['title']} - {song_info['author']}]({song_info['url']}) -" \
                              f" `requested by: {self.client.get_user(song_info['req']).name} ` "
                await ctx.send(embed=Embed(title="**__Now playing:__**", description=description, color=0xad3998))
            else:
                await slash_error(ctx, f"You are required to be in the right channel <#{data[2]}>")
        else:
            await slash_error(ctx, "No music is playing at the moment, play music with /play")

    @cog_ext.cog_slash(name="Shuffle",
                       description="Shuffles the queue",
                       guild_ids=music_servers_id
                       )
    async def _shuffle(self, ctx: SlashContext):
        if (data := self.client.db.get_music(ctx.guild_id)) is not None:
            if ctx.channel_id == data[2] and data[1] == ctx.author.voice.channel.id:
                q = data[3].split(";")
                shuffle(q)
                self.client.db.update_music(data[0], data[1], data[2], ";".join(q))
                await ctx.send("Shuffled the queue! 🔀")
            else:
                await slash_error(ctx, f"You are required to be in the right channel <#{data[2]}>"
                                       f" and be in the voice channel to use this command")
        else:
            await slash_error(ctx, "No music is playing at the moment, play music with /play")

    @cog_ext.cog_slash(name="removesong",
                       description="Remove a particular song from the queue",
                       guild_ids=music_servers_id,
                       options=[
                           create_option(name="index",
                                         description="Index of the song in /queue",
                                         option_type=4,
                                         required=True)
                       ])
    async def _removesong(self, ctx: SlashContext, index):
        if (data := self.client.db.get_music(ctx.guild_id)) is not None:
            if ctx.channel_id == data[2] and data[1] == ctx.author.voice.channel.id:
                q = data[3].split(";")
                if index <= len(q):
                    song_info = eval(q[index])
                    del q[index]
                    self.client.db.update_music(data[0], data[1], data[2], ";".join(q))
                    description = f"[{song_info['title']} - {song_info['author']}]({song_info['url']}) -" \
                                  f" `requested by: {self.client.get_user(song_info['req']).name} ` "
                    await ctx.send(embed=Embed(title="**__Removed:__**", description=description, color=0xad3998))
                else:
                    await slash_error(ctx, "Index out of range")
            else:
                await slash_error(ctx, f"You are required to be in the right channel <#{data[2]}> and be in the voice channel to use this command")
        else:
            await slash_error(ctx, "No music is playing at the moment => no queue to remove song from, play music with /play")

    @cog_ext.cog_slash(name="loop",
                       description="Configure loop preferences",
                       guild_ids=music_servers_id,
                       options=[
                           create_option(name="loop_type",
                                         description="Loop song or entire queue",
                                         option_type=3,
                                         required=True,
                                         choices=[
                                             create_choice(
                                                 value="song",
                                                 name="song"
                                             ),
                                             create_choice(
                                                 value="queue",
                                                 name="queue"
                                             )
                                         ]
                                         )
                       ]
                       )
    async def _loop(self, ctx: SlashContext, loop_type):
        if (data := self.client.db.get_music(ctx.guild_id)) is not None and ctx.author.voice is not None:
            if ctx.channel_id == data[2] and data[1] == ctx.author.voice.channel.id:
                if loop_type == "song":
                    song = data[3].split(";")[0]
                    self.client.db.update_music(data[0], data[1], data[2], data[3] + ";" + song)
                    await ctx.send("Added current song to the end of the queue")
                else:
                    loop_switcher = {1: 0,  0: 1}
                    self.client.db.update_music(data[0], data[1], data[2], data[3], loop_switcher[data[4]])
                    if loop_switcher[data[4]] == 1:
                        await ctx.send("Looped queue turned on.")
                    else:
                        await ctx.send("Lopped queue turned off.")
            else:
                await slash_error(ctx, f"You are required to be in the right channel <#{data[2]}> and be in the voice channel to use this command")
        else:
            await slash_error(ctx, "The bot must be playing music and you have to be in the same voice channel.")

    @cog_ext.cog_slash(name="skip",
                       description="Skip the current song",
                       guild_ids=music_servers_id,
                       options=[
                           create_option(name="to",
                                         description="Skip to a certain track, use index in /queue for reference",
                                         option_type=4,
                                         required=False)
                       ]
                       )
    async def _skip(self, ctx: SlashContext, to=None):
        if (data := self.client.db.get_music(ctx.guild_id)) is not None and ctx.author.voice is not None:
            if ctx.channel_id == data[2] and data[1] == ctx.author.voice.channel.id:

                if to is not None:
                    self.client.db.update_music(data[0], data[1], data[2], data[3], data[4], to - 1)
                    data = self.client.db.get_music(ctx.guild_id)

                vc = ctx.voice_client
                vc.stop()
                await self.sleep_handler.cancel_all()

                current_song_info = eval(data[3].split(";")[data[5] + 1])
                description = f"[{current_song_info['title']} - {current_song_info['author']}]({current_song_info['url']}) -" \
                              f" `requested by: {self.client.get_user(current_song_info['req']).name} ` "

                await ctx.send(embed=Embed(title="**__Skipped to:__**", description=description, color=0xad3998))
            else:
                await slash_error(ctx, f"You are required to be in the right channel <#{data[2]}> and be in the voice channel to use this command")
        else:
            await slash_error(ctx, "The bot must be playing music and you have to be in the same voice channel.")

    @cog_ext.cog_slash(name="play",
                       description="Play your favourite song/playlist from YouTube or Spotify",
                       guild_ids=music_servers_id,
                       options=[
                           create_option(
                               name="url",
                               description="url to video, track, playlist or Album",
                               required=True,
                               option_type=3
                                )]
                       )
    async def play(self, ctx: SlashContext, url: str):
        s = Spotify_api()

        if match(r'^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/(watch\?v=)?.{11}$', url):
            valid = [True, 'link', url]
        elif match(r'https:\/\/(w){0,3}\.?youtube\.com\/playlist\?list=.{34}', url):
            valid = [True, 'playlist', url]
        elif match(r'https:\/\/(open)?\.spotify\.com\/track\/.{22}(\?si=.{16})?', url):
            valid = [True, 'spotify_link', url]
        elif match(r'https:\/\/(open)?\.spotify\.com\/playlist\/.{22}(\?si=.{16})?', url):
            valid = [True, 'spotify_playlist', url]
        elif match(r'https:\/\/(open)?\.spotify\.com\/album\/(.{22})(\?si=.{34})?', url):
            valid = [True, 'spotify_album', url]
        else:
            valid = [True, 'guess', url]

        if valid[0]:
            if ctx.author.voice is not None:
                data = self.client.db.get_music(ctx.guild.id)

                # Get voice channel
                if data is not None:
                    if data[1] == ctx.author.voice.channel.id:
                        v_channel = ctx.author.voice.channel
                        vc = ctx.voice_client
                        connected, play = True, True
                    else:
                        await slash_error(ctx, "You have to be in the same voice channel as me! :)")
                        connected, play = True, False

                else:
                    v_channel = ctx.author.voice.channel
                    connected, play = False, True

                if play:
                    # Update db
                    if not connected:
                        self.client.db.update_music(ctx.guild.id, v_channel.id, ctx.channel.id, "")
                        data = self.client.db.get_music(ctx.guild_id)
                        await ctx.send(f"Going to connect to <#{v_channel.id}>,"
                                       f" and bound commands to <#{ctx.channel.id}>.")
                    else:
                        await ctx.send("Got your request, going over it now!")

                    # Making queue
                    if valid[1] == 'playlist':
                        url_list = playlist_to_urllist(valid[2])
                        q = data[3] + ";" + ";".join(
                            [str(db_dict(i, loads((get(
                                f'https://www.googleapis.com/youtube/v3/videos?id={i[-34:]}'
                                f'&key={google_api_key}&fields=items(snippet(title))'
                                f'&part=snippet'))
                                                  .text)['items'][0]['snippet']['title'],
                                         "",
                                         'link',
                                         ctx.author.id
                                         ))
                             for i in url_list])

                    elif valid[1] == 'link':
                        q = data[3] + ";" + str(db_dict(url, loads((get(
                            f'https://www.googleapis.com/youtube/v3/videos?id={url[-11:]}'
                            f'&key={google_api_key}&fields=items(snippet(title))'
                            f'&part=snippet')).text)['items'][0]['snippet']['title'],
                                                        "",
                                                        'link',
                                                        ctx.author.id
                                                        ))

                    elif valid[1] == 'spotify_link':
                        key_words = s.get_track_info(valid[2])
                        q = data[3] + ";" + str(db_dict(search(key_words['artist'] + " " + key_words['title'])['url'],
                                                        key_words["title"],
                                                        key_words["artist"],
                                                        "spotify_link",
                                                        ctx.author.id
                                                        ))

                    elif valid[1] == 'spotify_playlist':
                        url_list = s.get_playlist_list(valid[2])
                        q = data[3] + ";" + ";".join(
                            [
                                str(db_dict(i['url'],
                                            i["title"],
                                            i["artist"],
                                            'spotify_link',
                                            ctx.author.id
                                            ))
                                for i in url_list
                            ]
                        )

                    elif valid[1] == 'spotify_album':
                        url_list = s.get_album_list(valid[2])
                        q = data[3] + ";" + ";".join([
                            str(db_dict(i['url'],
                                        i['title'],
                                        i["artist"],
                                        'spotify_link',
                                        ctx.author.id))
                            for i in url_list
                        ])

                    elif valid[1] == 'guess':
                        s = search(url)
                        q = data[3] + ";" + str(db_dict(s['url'], s['title'], s['author'], 'guess', ctx.author.id))

                    if q[0] == ';':
                        q = q[1:]

                    if ctx.voice_client:
                        vc = ctx.voice_client
                    else:
                        await v_channel.connect()
                        for i in self.client.voice_clients:
                            if i.channel.id == v_channel.id:
                                vc = i
                                break

                    if vc.is_playing():
                        await ctx.send('Already playing a song, added to queue.')
                    else:
                        await ctx.send('Request accepted, stay tuned.')

                    if vc.is_playing():
                        self.client.db.update_music(data[0], data[1], data[2], q)
                    else:

                        for i in self.client.voice_clients:
                            i: VoiceClient
                            if i.channel.id == v_channel.id:
                                vc = i
                                break

                        song_info = eval(q.split(';')[0])
                        if song_info['type'] == 'spotify_link':
                            url = search(song_info['author'] + " " + song_info['title'])['url']
                        else:
                            url = song_info['url']
                        self.client.db.update_music(data[0], data[1], data[2], q, data[4], 0)
                        await play_song(self, ctx, vc, url)

            else:
                await slash_error(ctx, "You have to be in a voice channel to use this command.")
        else:
            await ctx.send("You provided an invalid url, please try again.")

    @cog_ext.cog_slash(
        name="queue",
        description="Current queue of music",
        guild_ids=music_servers_id,
        options=[
        ]
    )
    async def _queue(self, ctx: SlashContext):
        if (data := self.client.db.get_music(ctx.guild.id)) is not None:
            q = data[3].split(';')
            q_length = len(q)
            title = f"Queue for {ctx.guild.name} - {self.client.voice_clients[0].channel.name}"

            if q == ['']:
                description = "No current queue. You can add song, playlists or albums with the /play slash-command!"
            else:
                description = f"**__Now playing:__** \n\n [{eval(q[data[5]])['title']} -" \
                              f" {eval(q[data[5]])['author']}]" \
                              f"({eval(q[data[5]])['url']}) - `requested by:" \
                              f" {(self.client.get_user(eval(q[data[5]])['req'])).name}`  \n\n **__Queue:__** \n\n"
                count = data[5]

                for track in q[data[5] + 1:]:
                    track_info = eval(track)
                    count += 1
                    if count <= data[5] + 20:
                        description += f"**{count}** [{track_info['title']} - {track_info['author']}]" \
                                       f"({track_info['url']}) - `requested by:" \
                                       f" {(self.client.get_user(track_info['req'])).name}`  \n\n"
                    else:
                        break

            embed = Embed(title=title, description=description, color=0xad3998)
            if q_length > 20:
                embed.set_footer(text=f'1 / {floor((q_length - data[5])/ 20) + 1}')

            q_msg = await ctx.send(embed=embed)

            self.current_q = q_msg.id

            if q_length > 20:
                await q_msg.add_reaction('▶')
        else:
            if data[3] == "":
                msg = "No queue"
            else:
                msg = data(3)
            await ctx.send(msg)

    @cog_ext.cog_slash(
        name="lyrics",
        description="Get the lyrics of the current song",
        guild_ids=music_servers_id
    )
    async def _lyrics(self, ctx: SlashContext):
        if (data := self.client.db.get_music(ctx.guild.id)) is not None:
            song = eval(data[3].split(';')[data[5]])
            title = song['title']
            author = song['author']

            if s := (self.genius.search_song(title, author)):
                lyrics = s.lyrics

                if 'English Translation:' in lyrics:
                    lyrics = lyrics.split('English Translation:')[1]

                embed = Embed(title=f"Lyrics - {title} by {author}", color=0xad3998)

                if len(lyrics) > 3900:
                    embed.description = lyrics[:3900] + "\nLyrics is too long to be displayed. Only first part is shown."
                else:
                    embed.description = lyrics[:-27]

                await ctx.send(embed=embed)

            else:
                await slash_error(ctx, "Can't find lyrics. Sorry!")
        else:
            await slash_error(ctx, "No song playing, can't display lyrics")


    @commands.Cog.listener()
    async def on_reaction_add(self, rec: Reaction, user):
        if rec.message.id == self.current_q and user != self.client.user:
            if str(rec) == '▶' or str(rec) == '◀':
                q_page = [int(i) for i in rec.message.embeds[0].to_dict()['footer']['text'].split(' / ')]

                data = self.client.db.get_music(rec.message.guild.id)

                q = data[3].split(';')
                q_length = len(q)
                title = f"Queue for {rec.message.guild.name} - {self.client.voice_clients[0].channel.name}"

                description = f"**__Now playing:__** \n\n [{eval(q[data[5]])['title']}" \
                              f" - {eval(q[data[5]])['author']}]" \
                              f"({eval(q[data[5]])['url']}) - `requested by:" \
                              f" {(self.client.get_user(eval(q[data[5]])['req'])).name}`  \n\n **__Queue:__** \n\n"

                def get_index(emoji: str):
                    index_switcher = {
                        '▶': 1,
                        '◀': -1
                    }
                    return index_switcher[emoji]
                start_index = data[5] + ((q_page[0] + get_index(str(rec)) - 1) * 20) + 1

                count = start_index
                for track in q[start_index:]:
                    track_info = eval(track)
                    count += 1
                    if count <= start_index + 20:
                        description += f"**{count - 1}** [{track_info['title']} - {track_info['author']}]" \
                                       f"({track_info['url']}) - `requested by: " \
                                       f"{(self.client.get_user(track_info['req'])).name}`  \n\n"
                    else:
                        break

                embed = Embed(title=title, description=description, color=0xad3998)
                embed.set_footer(text=f'{q_page[0] + get_index(str(rec))}  / {floor((q_length - data[5])/ 20) + 1}')
                await rec.message.edit(embed=embed)

                if str(rec) == '▶':
                    if str((reaction := rec.message.reactions[0])) == '▶':
                        await reaction.clear()
                        await rec.message.add_reaction('◀')
                        if q_page[0] + 1 != q_page[1]:
                            await rec.message.add_reaction('▶')
                    else:

                        if q_page[0] + 1 == q_page[1]:
                            await rec.clear()
                        else:
                            await rec.remove(user)

                elif str(rec) == '◀':
                    if (q_page[0] - 1) == 1:
                        await rec.clear()
                        await rec.message.add_reaction('▶')
                    else:
                        await rec.remove(user)

            else:
                await rec.remove(user)


def setup(client: commands.Bot):
    client.add_cog(music(client))
