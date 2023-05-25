from django.shortcuts import render


def index(request):
    return render(request, 'index.html')


def about_us(request):
    return render(request, 'about-us.html')


def contacts(request):
    return render(request, 'contacts.html')


def typography(request):
    return render(request, 'typography.html')