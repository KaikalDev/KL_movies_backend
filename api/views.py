import requests
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from math import ceil
from .models import Movie
from .serializers import MovieSerializer

class MovieView(APIView):
    ITEMS_PER_PAGE = 5

    def get(self, request, *args, **kwargs):
        search_title = request.query_params.get('Title')
        year = request.query_params.get('year')
        page = int(request.query_params.get('page', 1))

        if not search_title:
            return Response({"error": "O parâmetro 'Title' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        filters = {'title__icontains': search_title}
        if year:
            filters['year'] = year

        local_movies = Movie.objects.filter(**filters)
        local_serializer = MovieSerializer(local_movies, many=True)
        combined_movies = list(local_serializer.data)

        if combined_movies:
            return self.paginate_movies(combined_movies, page)

        api_movies = self.fetch_movies_from_api(search_title)
        combined_movies.extend(api_movies)

        return self.paginate_movies(combined_movies, page)

    def fetch_movies_from_api(self, search_title):
        api_key = '5e7b999c'
        url = "http://www.omdbapi.com/"
        params = {'apikey': api_key, 's': search_title, 'type': 'movie'}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get('Response') == 'True':
                api_movies = []
                for movie_data in data.get('Search', []):
                    movie, created = Movie.objects.update_or_create(
                        imdbID=movie_data['imdbID'],
                        defaults={
                            'title': movie_data['Title'],
                            'year': movie_data['Year'],
                            'poster': movie_data['Poster'],
                        }
                    )
                    api_movies.append(MovieSerializer(movie).data)

                return api_movies
            else:
                return []

        except requests.RequestException:
            return []

    def paginate_movies(self, combined_movies, page):
        total_items = len(combined_movies)
        total_pages = ceil(total_items / self.ITEMS_PER_PAGE)
        start_index = (page - 1) * self.ITEMS_PER_PAGE
        end_index = start_index + self.ITEMS_PER_PAGE
        paginated_movies = combined_movies[start_index:end_index]

        return Response({
            "total_pages": total_pages,
            "current_page": page,
            "results": paginated_movies
        }, status=status.HTTP_200_OK)
