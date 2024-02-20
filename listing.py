from datetime import datetime, timedelta
import re


class Listing:

    def __init__(self, title, director_credit, runtime, year, days, screening_type="default"):
        self.title = title
        self.director_credit = director_credit
        self.runtime = runtime
        self.year = year
        self.days = days
        self.screening_type = screening_type

    def to_markup(self):
        markup = self.title + "\n"
        markup += self.screening_info_to_markup() + "\n"
        markup += self.weekly_times_to_string()
        return markup

    def screening_info_to_markup(self):
        if len(self.director_credit) > 1:
            director_markup = ', '.join(self.director_credit[:-1]) + ' & ' + self.director_credit[-1]
        else:
            director_markup = self.director_credit[0]
        formatted_runtime = re.sub(r'(\d+)\s*min', r'\1m', self.runtime)
        return f"{director_markup}, {self.year}, {formatted_runtime}"

    def weekly_times_to_string(self):
        string = ""
        if len(self.days) >= 5:
            pass
        for day in self.days:
            string += day
        return "times"

