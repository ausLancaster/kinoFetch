from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
import requests
import re


class Site(ABC):
    url = ""
    html = ""
    listings = ""

    def fetch_html(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()

            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Request Error: Unable to fetch HTML from {self.url}. URL for session times may have changed.")

    @abstractmethod
    def scrape_html(self):
        pass

    def process(self):
        print(f"Processing...\n")
        Site.html = self.fetch_html()
        Site.listings = self.scrape_html()
        print(f"Scraped listings: \n\n{self.listings}")


class Palace(Site):
    Site.url = "https://www.palacecinemas.com.au/session-times"
    cinemas = ["pentridge-cinema"]

    def __init__(self):
        return

    def scrape_html(self):
        result = ""
        soup = BeautifulSoup(Site.html, "html.parser")
        cinema_elements = soup.find_all('div', 'quick-times-cinema')
        for div in cinema_elements:
            try:
                print(f"{div.h3}")
                cinema_name = div.h3.string
                result += f"{cinema_name.capitalize()}\n\n"
                # get films
                films = div.find_all('div', 'quick-times-film')
            except AttributeError:
                print(f"Scraping Error: Unable to fetch cinema.")
                continue
            for film in films:
                try:
                    # get title and remove rating
                    title = film.p.a.b.string
                    pattern = r'\s*\([^)]*\)$'
                    title = re.sub(pattern, '', title)
                    result += f"{title}\n"
                except AttributeError:
                    print(f"Film Scraping Error: Unable to fetch film.")
                    continue
            result += "\n"
        if result.isalpha():
            print(f"Scraping Error: Results are empty")
        return result


palace = Palace()
palace.process()
