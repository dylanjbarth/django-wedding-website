import json

from django.shortcuts import render
from django.http import JsonResponse

from .spotify import search

def song_requests(request):
    return render(request, 'song_requests.html', context={})

def search_song(request):
    query = request.GET.get('q', '')
    pageSize = request.GET.get('pageSize', 10)
    pageOffset = request.GET.get('pageOffset', 0)
    if not query:
        return JsonResponse({'message': 'Query is required.'}, status=400)
    results = search(query, pageSize, pageOffset)
    return JsonResponse(results)