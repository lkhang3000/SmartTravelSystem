from django.shortcuts import render

# Create your views here.
def get_home(request):
    return render (request, 'homepage.html')

def user_input(request):
    return render(request, 'userInput.html')

def user_login(request):
    return render(request, 'login.html')