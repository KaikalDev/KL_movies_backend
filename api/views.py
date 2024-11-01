import requests
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from math import ceil

class MovieView(APIView):
    ITEMS_PER_PAGE = 5

    def get(self, request, *args, **kwargs):
        search_title = request.query_params.get('Title')
        year = request.query_params.get('year')
        page = int(request.query_params.get('page', 1))

        if not search_title:
            return Response({"error": "O parâmetro 'Title' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        api_movies = self.fetch_movies_from_api(search_title, year)

        return self.paginate_movies(api_movies, page)

    def fetch_movies_from_api(self, search_title, year=None):
        api_key = '5e7b999c'
        url = "http://www.omdbapi.com/"
        params = {
            'apikey': api_key,
            's': search_title,
            'type': 'movie',
            'y': year,
            'page': 1
        }

        movies = []
        try:
            while True:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get('Response') != 'True':
                    break

                movies.extend(data.get('Search', []))

                if len(movies) >= int(data.get('totalResults', len(movies))):
                    break

                params['page'] += 1

            return movies

        except requests.RequestException:
            return []

    def paginate_movies(self, movies, page):
        total_items = len(movies)
        total_pages = ceil(total_items / self.ITEMS_PER_PAGE)
        start_index = (page - 1) * self.ITEMS_PER_PAGE
        end_index = start_index + self.ITEMS_PER_PAGE
        paginated_movies = movies[start_index:end_index]

        return Response({
            "total_pages": total_pages,
            "current_page": page,
            "results": paginated_movies
        }, status=status.HTTP_200_OK)
