from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^song-requests/$', views.song_requests, name='song_requests'),
    url(r'^song-requests/search/$', views.search_song, name='search_song'),
]
