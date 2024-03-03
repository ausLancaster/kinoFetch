from django.db import models


class Listing(models.Model):
    SCREENING_TYPES = {}
    title = models.CharField(max_length=200)
    director_credit = models.CharField(max_length=200)
    runtime = models.IntegerField()
    year = models.IntegerField()
    days = models.CharField(max_length=50)
    screening_type = models.CharField(max_length=50)