import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from django.conf import settings

client_credentials_manager = SpotifyClientCredentials(
    client_id=settings.SPOTIPY_CLIENT_ID,
    client_secret=settings.SPOTIPY_CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


def search(query, limit=10, offset=0):
  return sp.search(query, limit, offset)
