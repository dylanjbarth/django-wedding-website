from django.shortcuts import render

# Create your views here.

def song_requests(request):
    return render(request, 'song_requests.html', context={})
