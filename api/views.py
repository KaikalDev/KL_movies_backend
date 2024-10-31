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
        
        if not search_title:
            return Response({"error": "O parâmetro 'Title' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        page = int(request.query_params.get('page', 1))
        items_per_page = 5

        local_movies = Movie.objects.filter(title__icontains=search_title)
        local_serializer = MoviesSerializer(local_movies, many=True)
        combined_movies = list(local_serializer.data)

        if len(combined_movies) >= page * items_per_page:
            total_pages = ceil(len(combined_movies) / items_per_page)
            start_index = (page - 1) * items_per_page
            end_index = start_index + items_per_page
            paginated_movies = combined_movies[start_index:end_index]
            return Response({
                "total_pages": total_pages,
                "current_page": page,
                "results": paginated_movies
            }, status=status.HTTP_200_OK)

        key = '5e7b999c'
        url = f"http://www.omdbapi.com/?apikey={key}"
        params = {
            's': search_title,
            'type': 'movie',
            'page': 1
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if data.get('Response') == 'True':
                total_results = int(data.get('totalResults', 0))
                external_total_pages = min(ceil(total_results / 10), 3)

                for page_num in range(1, external_total_pages + 1):
                    params['page'] = page_num
                    response = requests.get(url, params=params)
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
                    else:
                        break

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

        except requests.RequestException:
            return Response({"error": "Falha na conexão com a API externa."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
