import os
import requests
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from math import ceil
from .models import Movie
from .serializers import MoviesSerializer

class MovieView(APIView):
    def get(self, request, *args, **kwargs):
        search_title = request.query_params.get('Title')
        page = request.query_params.get('page', 1)

        if not search_title:
            return Response({"error": "O parâmetro 'Title' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            page = int(page)
            if page < 1:
                raise ValueError("O parâmetro 'page' deve ser um número positivo.")
        except ValueError:
            return Response({"error": "O parâmetro 'page' é inválido."}, status=status.HTTP_400_BAD_REQUEST)

        items_per_page = 5
        local_movies = Movie.objects.filter(title__icontains=search_title)
        local_serializer = MoviesSerializer(local_movies, many=True)
        combined_movies = list(local_serializer.data)

        if not combined_movies:
            combined_movies = self.fetch_movies_from_api(search_title)

        return self.paginate_movies(combined_movies, page, items_per_page)

    def fetch_movies_from_api(self, search_title):
        key = os.getenv('OMDB_API_KEY')
        url = "http://www.omdbapi.com/"
        params = {
            'apikey': key,
            's': search_title,
            'type': 'movie',
            'page': 1
        }

        combined_movies = []

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get('Response') == 'True':
                total_results = int(data.get('totalResults', 0))
                external_total_pages = min(ceil(total_results / 10), 3)

                for page_num in range(1, external_total_pages + 1):
                    params['page'] = page_num
                    response = requests.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()

                    if data.get('Response') == 'True':
                        for movie_data in data['Search']:
                            movie, created = Movie.objects.update_or_create(
                                imdbID=movie_data['imdbID'],
                                defaults={
                                    'title': movie_data['Title'],
                                    'year': int(movie_data['Year']),
                                    'typeMovie': movie_data['Type'],
                                    'poster': movie_data['Poster']
                                }
                            )
                            combined_movies.append(MoviesSerializer(movie).data)

        except requests.RequestException:
            pass

        return combined_movies

    def paginate_movies(self, combined_movies, page, items_per_page):
        total_items = len(combined_movies)
        total_pages = ceil(total_items / items_per_page)
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        paginated_movies = combined_movies[start_index:end_index]

        return Response({
            "total_pages": total_pages,
            "current_page": page,
            "results": paginated_movies
        }, status=status.HTTP_200_OK)
