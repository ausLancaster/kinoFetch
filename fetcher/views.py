from django.shortcuts import render


# Create your views here.
def home(request):
    context = {"listings": "Placeholder for listings", "user_report": "Reported findings"}
    return render(request, 'fetcher/fetcher.html', context)
