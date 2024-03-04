from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime, timedelta
from . import scraper


# Create your views here.
def home(request):
    return render(request, 'fetcher/base.html')


def update_listings(request):
    palace = scraper.Palace()
    listings = palace.process()
    # save_movie_dictionary(Cinema.movie_dictionary)
    print(f"Made {scraper.Cinema.omdb_calls} OMDB calls")
    starting_date = scraper.Cinema.get_starting_date()
    end_date = starting_date + timedelta(days=6)
    date_range = f"{starting_date.strftime('%B %#d')} - {end_date.strftime('%B %#d')}"
    context = {"date_range": date_range, "listings": listings}
    return render(request, 'fetcher/listings.html', context)
