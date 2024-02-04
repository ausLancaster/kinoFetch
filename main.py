from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import requests
import re
import traceback
class Site(ABC):
    session_url = ""
    html = ""
    listings = ""
    initialized = False
    nearest_thursday = None
    current_year = None

    def __init__(self):
        if not self.initialized:
            self._initialize_once(self)
            self.initialized = True

    @staticmethod
    def _initialize_once(self):
        today = datetime.now()
        today = today.replace(hour=12, minute=0, second=0, microsecond=0)
        days_to_thursday = (today.weekday() - 3) % 7
        Site.nearest_thursday = today - timedelta(days=days_to_thursday)

    @staticmethod
    def fetch_html(url):
        try:
            cookie_variable = {"user-set-location": "VIC"}
            session = requests.Session()
            session.cookies.update(cookie_variable)
            response = session.get(url)
            response.raise_for_status()

            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Request Error: Unable to fetch HTML from {url}. URL for session times may have changed.")
            print(f"{e}")

    @abstractmethod
    def scrape_html(self):
        pass

    def process(self):
        print(f"Processing...\n")
        Site.current_year = str(datetime.now().year)
        Site.html = Site.fetch_html(self.session_url)
        Site.listings = self.scrape_html()
        print(f"Scraped listings: \n\n{self.listings}")

    @staticmethod
    def is_within_week(target_date):
        date_difference = target_date - Site.nearest_thursday
        return timedelta(days=0) <= date_difference <= timedelta(days=6)


class Palace(Site):
    Site.session_url = "https://www.palacecinemas.com.au/session-times"
    cinemas = ["pentridge-cinema"]

    def scrape_html(self):
        result = ""
        soup = BeautifulSoup(Site.html, "html.parser")
        cinema_elements = soup.find_all('div', 'quick-times-cinema')
        for div in cinema_elements:
            try:
                cinema_name = div.h3.string
                cinema_name = cinema_name.capitalize()

                result += f"{cinema_name}\n\n"
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
                    # limit to times during the coming week (previous Thursday to next Thursday)
                    date_divs = film.find_all('div', 'single-day-time')
                    any_session_within_week = False;
                    for date_div in date_divs:
                        data_day_value = date_div.get('data-day')
                        data_day_value = data_day_value.replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                        data_day_value += " " + str(Site.current_year)
                        date_obj = datetime.strptime(data_day_value, "%a %d %b %Y")
                        if not Site.is_within_week(date_obj):
                            continue
                        else:
                            any_session_within_week = True
                    if any_session_within_week:
                        result += f"{title}"
                        result += "\n"
                    # find director and year
                except (AttributeError, ValueError) as e:
                    print(f"Scraping Error: Unable to fetch film.")
                    print(f"Reason: {e}")
                    traceback.print_exc()
                    break
            result += "\n"
            break
        if result.isalpha():
            print(f"Scraping Error: Results are empty")
        return result


palace = Palace()
palace.process()
