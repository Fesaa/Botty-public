import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from regex import search
from cogs.config_handler import spotify_client_id, spotify_client_secret


class Spotify_api:

    def __init__(self):
        self.auth_manager = SpotifyClientCredentials(client_id=spotify_client_id,
                                                     client_secret=spotify_client_secret)

        self.sp = spotipy.Spotify(auth_manager=self.auth_manager)

    def get_track_info(self, url: str):
        re_search = search(r'https:\/\/(open)?\.spotify\.com\/track\/(.{22})(\?si=.{16})?', url)
        info = self.sp.track(re_search.group(2))
        return {'artist': info['album']['artists'][0]['name'], 'title': info['name'], 'url': url}
    
    def get_playlist_list(self, url: str):
        re_search = search(r'https:\/\/(open)?\.spotify\.com\/playlist\/(.{22})(\?si=.{16})?', url)
        info = self.sp.playlist(re_search.group(2))
        return [self.get_track_info(item['track']['external_urls']['spotify']) for item in info['tracks']['items']]
    
    def get_album_list(self, url: str):
        re_search = search(r'https:\/\/(open)?\.spotify\.com\/album\/(.{22})(\?si=.{34})?', url)
        info = self.sp.album(re_search.group(2))
        return [self.get_track_info(item['external_urls']['spotify']) for item in info['tracks']['items']]
