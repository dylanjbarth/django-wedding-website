from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^song-requests/$', views.song_requests, name='song_requests'),
]
