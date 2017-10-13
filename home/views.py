from django.shortcuts import render

# Create your views here.


def index(request):
    # return render(request, 'home/../templates/home/index.html')
    return render(request, 'home/../home/index.html')