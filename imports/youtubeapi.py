import googleapiclient.discovery
import youtube_dl
from urllib.parse import parse_qs, urlparse
from cogs.config_handler import youtube_developerkey


def playlist_to_urllist(url: str) -> list:
    query = parse_qs(urlparse(url).query, keep_blank_values=True)
    playlist_id = query["list"][0]

    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=youtube_developerkey)

    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlist_id,
        maxResults=50
    )

    playlist_items = []
    while request is not None:
        response = request.execute()
        playlist_items += response["items"]
        request = youtube.playlistItems().list_next(request, response)
    return [f'https://www.youtube.com/watch?v={t["snippet"]["resourceId"]["videoId"]}' for t in playlist_items]


def search(arg):
    ydl_option = {'format': 'bestaudio', 'noplaylist': 'True'}
    with youtube_dl.YoutubeDL(ydl_option) as ydl:
        video = ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]
    return {"url": video['webpage_url'], "title": video['title'], "author": video['uploader']}

        