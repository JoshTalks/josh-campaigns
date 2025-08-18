from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .forms import UserRegistrationForm
from django.contrib import messages

from django.conf import settings
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
