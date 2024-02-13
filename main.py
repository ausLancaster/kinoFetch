from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import requests
import re
import traceback
from urllib.parse import quote
import json

OMDB_URL = "https://www.omdbapi.com/?apikey=d6d62bc2"
MOVIE_DICTIONARY_FILENAME = "movie_dictionary.json"
DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def load_movie_dictionary():
    with open(MOVIE_DICTIONARY_FILENAME, 'r') as file:
        dictionary = json.load(file)
    return dictionary


def save_movie_dictionary(dictionary):
    with open(MOVIE_DICTIONARY_FILENAME, 'w') as file:
        json.dump(dictionary, file)


class Site(ABC):
    session_url = ""
    cookies = ""
    html = ""
    listings = ""
    initialized = False
    nearest_thursday = None
    current_year = None
    omdb_calls = 0
    result = ""
    movie_dictionary = load_movie_dictionary()

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
    def fetch_html(url, cookies=None):
        try:
            session = requests.Session()
            if cookies:
                session.cookies.update(cookies)
            response = session.get(url)
            response.raise_for_status()

            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Request Error: Unable to fetch HTML from {url}. URL may have changed.")
            print(f"{e}")

    @staticmethod
    def fetch_json(url, cookies=None):
        try:
            session = requests.Session()
            if cookies:
                session.cookies.update(cookies)
            response = session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request Error: Unable to fetch HTML from {url}. URL may have changed.")
            print(f"{e}")

    @abstractmethod
    def scrape_html(self):
        pass

    def process(self):
        print(f"Processing...\n")
        Site.current_year = str(datetime.now().year)
        Site.html = Site.fetch_html(self.session_url, Site.cookies)
        Site.listings = self.scrape_html()
        print(f"--- LISTINGS ---: \n\n\n{self.listings}")

    @staticmethod
    def is_within_week(target_date):
        date_difference = target_date - Site.nearest_thursday
        return timedelta(days=0) <= date_difference <= timedelta(days=6)


class Palace(Site):
    Site.base_url = "https://www.palacecinemas.com.au"
    Site.session_url = Site.base_url + "/session-times"
    Site.cookies = {"user-set-location": "VIC"}
    blacklist = ["Opéra de Paris", "Paris Opera Ballet", "Opera di Roma", "Royal Ballet", "Royal Opera", "NT LIVE"]
    cinema_list = ['Kino cinema'] # , 'Pentridge cinema', 'Palace balwyn cinema', 'Palace brighton bay', 'Palace cinema como', 'Palace dendy brighton', 'Palace westgarth', 'Palace penny lane']

    def scrape_html(self):
        soup = BeautifulSoup(Site.html, "html.parser")
        cinema_elements = soup.find_all('div', 'quick-times-cinema')
        for div in cinema_elements:
            try:
                cinema_name = div.h3.string
                cinema_name = cinema_name.capitalize()

                if cinema_name in self.cinema_list:
                    self.cinema_list.remove(cinema_name)
                    self.result += f"{cinema_name}\n\n"
                else:
                    continue
                # get films
                films = div.find_all('div', 'quick-times-film')
            except AttributeError:
                print(f"Scraping Error: Unable to fetch cinema.")
                traceback.print_exc()
                continue
            for film in films:
                try:
                    self.process_film(film)
                except (AttributeError, ValueError) as e:
                    print(f"Scraping Error: Unable to fetch film.")
                    print(f"Reason: {e}")
                    traceback.print_exc()
                    continue
            Site.result += "\n"
            break
        if Site.result.isalpha():
            print(f"Scraping Error: Results are empty")
        return Site.result

    def process_film(self, film):
        # get title
        title = film.p.a.b.string
        # skip blacklisted titles
        skip_movie = False
        for blacklisted_string in self.blacklist:
            if blacklisted_string in title:
                skip_movie = True
        if skip_movie:
            return
        # remove rating
        pattern = r'\s*\([^)]*\)$'
        title = re.sub(pattern, '', title)
        # remove brackets
        title = re.sub(pattern, '', title)
        # limit to times during the coming week (previous Thursday to next Thursday)
        date_divs = film.find_all('div', 'single-day-time')
        any_session_within_week = False
        for date_div in date_divs:
            data_day_value = date_div.get('data-day')
            data_day_value = data_day_value.replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
            data_day_value += " " + str(Site.current_year)
            date_obj = datetime.strptime(data_day_value, "%a %d %b %Y")
            if not Site.is_within_week(date_obj):
                continue
            else:
                any_session_within_week = True
                # create week string
                day_of_week = date_obj.weekday()
                first_letter = DAY_NAMES[day_of_week][0]
        if not any_session_within_week:
            return
        Site.result += f"{title}"
        Site.result += "\n"
        movie_link_a = film.p.a
        movie_link_url = Site.base_url + movie_link_a['href']
        # find director and year from OMDB
        if title in Site.movie_dictionary:
            details = Site.movie_dictionary[title]
        else:
            # func
            film_details_json = Site.fetch_json(OMDB_URL + "&t=" + quote(title))
            Site.omdb_calls += 1
            if film_details_json.get("Response") == 'True':
                details = film_details_json
            else:
                print(f"Scraping Error: Unable to find film details for {title}.")
                Site.result += "\n"
                return
        # get director from palace's movie page for purposes of disambiguating movie titles
        movie_page = Site.fetch_html(movie_link_url, Site.cookies)
        movie_soup = BeautifulSoup(movie_page, 'html.parser')
        director_tag = movie_soup.find('h4', string='Director')
        director_list = details.get("Director")
        director_list = director_list.split(", ")
        if director_tag:
            palace_director_list = director_tag.find_next_sibling('p').text.strip()
            palace_director_list = palace_director_list.split(", ")
            director_match = False
            for d in palace_director_list:
                if d in director_list:
                    director_match = True
                    break
            if not director_match:
                match_details = self.search_omdb_for_film_and_director(title, palace_director_list)
                if match_details is not None:
                    details = match_details
                    director_list = details.get("Director")
                    director_list = director_list.split(", ")
        Site.movie_dictionary[title] = details
        # append details to result
        if len(director_list) > 1:
            director_list = ', '.join(director_list[:-1]) + ' & ' + director_list[-1]
        else:
            director_list = director_list[0]
        formatted_runtime = re.sub(r'(\d+)\s*min', r'\1m', details.get("Runtime"))
        Site.result += f"{director_list}, {details.get("Year")}, {formatted_runtime}\n"
        Site.result += "\n"
        return

    @staticmethod
    def search_omdb_for_film_and_director(title, director_list1):
        # func
        film_search_json = Site.fetch_json(OMDB_URL + "&s=" + quote(title))
        Site.omdb_calls += 1
        if film_search_json:
            total = film_search_json["totalResults"]
            total = int(total)
            if total is not None and total > 1:
                search_results = film_search_json['Search']
                for film in search_results:
                    imdb_id = film["imdbID"]
                    film_details_json = Site.fetch_json(OMDB_URL + "&i=" + imdb_id)
                    Site.omdb_calls += 1
                    if film_details_json:
                        director_list2 = film_details_json["Director"]
                        director_list2 = director_list2.split(", ")
                        for director in director_list2:
                            if director in director_list1:
                                print(f"Disambiguated {title} to be the following:\n {film_details_json}\n")
                                return film_details_json
                    else:
                        print(f"Error: failed to fetch {title} by id ({imdb_id}) on OMDB")
                print(f"{film_search_json}")
                print(f"No matching director found in in OMDB: \"{title}\" {film_search_json['Search'][0]["Director"]} vs {director_list1}")
        else:
            print(f"Error: failed to search {title} on OMDB")
        return None


movie_dictionary = load_movie_dictionary()
palace = Palace()
palace.process()
save_movie_dictionary(movie_dictionary)
print(f"Made {Site.omdb_calls} OMDB calls")

