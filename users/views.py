from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from .forms import UserRegistrationForm
from django.contrib import messages

from django.cadminonf import settings
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.core.mail import EmailMessage, send_mail
from sendgrid.helpers.mail import SandBoxMode, MailSettings


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            email = form.cleaned_data.get("email")
            mydict = {'username': username}
            html_template = 'users/index.html'
            html_message = render_to_string(html_template, context=mydict)
            subject = 'Welcome to My App'
            email_from = settings.DEFAULT_FROM_EMAIL
            recipient_list = [email]
            message = EmailMessage(subject, html_message,
                                   email_from,
                                   recipient_list)
            message.content_subtype = 'html'
            message.send()
            messages.success(
                request, f"Hi {username}, your account has been created successfully!")
            return redirect("home")
    else:
        form = UserRegistrationForm()

    context = {
        "form": form
    }
    return render(request, 'users/register.html', context)


def home(request):
    return render(request, "users/home.html")

def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('outreach:dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    context = {
        "form": form
    }
    return render(request, "users/login.html", context)
