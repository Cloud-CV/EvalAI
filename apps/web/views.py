from django.shortcuts import render


def home(request, template_name="index.html"):
    """
    Home Page View.
    """
    return render(request, template_name)
