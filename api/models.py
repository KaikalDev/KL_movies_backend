from django.db import models

# Create your models here.
class Movie(models.Model):
    title = models.CharField(max_length=100)
    year = models.IntegerField()
    imdbID = models.CharField(max_length=9, unique=True)
    typeMovie = models.CharField(max_length=100)
    poster = models.URLField()
