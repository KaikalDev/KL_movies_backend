from django.db import models

class Movie(models.Model):
    title = models.CharField(max_length=255)
    year = models.CharField(max_length=4)
    poster = models.URLField()
    imdbID = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.title
