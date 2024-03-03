from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime, timedelta
from . import scraper


# Create your views here.
def home(request):
    starting_date = scraper.Cinema.get_starting_date()
    if starting_date is None:
        pass # TODO: error
    end_date = starting_date + timedelta(days=6)
    date_range = f"{starting_date.strftime('%B %d')} - {end_date.strftime('%B %d')}"
    context = {"day_range": date_range}
    return render(request, 'fetcher/base.html', context)


def update_listings(request):
    palace = scraper.Palace()
    listings = palace.process()
    # save_movie_dictionary(Cinema.movie_dictionary)
    print(f"Made {scraper.Cinema.omdb_calls} OMDB calls")
    return render(request, 'fetcher/listings.html', {"listings": listings})
