from celery import Celery
from celery.result import AsyncResult
from cinema import Palace, Cinema

app = Celery()


@app.task
def scrape_all_listings():
    palace = Palace()
    print(f"{palace.process()}")
    # save_movie_dictionary(Cinema.movie_dictionary)
    print(f"Made {Cinema.omdb_calls} OMDB calls")