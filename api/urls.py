from django.urls import path
from .views import MovieView

urlpatterns = [
    path('api/', MovieView.as_view(), name='movie-search'),
]
