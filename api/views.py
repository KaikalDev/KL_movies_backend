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
        
        movies = Movie.objects.filter(title__icontains=search_title)
        if movies.exists():
            page = int(request.query_params.get('page', 1))
            items_per_page = 5
            total_items = movies.count()
            total_pages = ceil(total_items / items_per_page)
            start_index = (page - 1) * items_per_page
            end_index = start_index + items_per_page

            paginated_movies = movies[start_index:end_index]
            serializer = MoviesSerializer(paginated_movies, many=True)
            return Response({
                "total_pages": total_pages,
                "current_page": page,
                "results": serializer.data
            }, status=status.HTTP_200_OK)
        
        key = '5e7b999c'
        url = f"http://www.omdbapi.com/?apikey={key}"

        params = {
            's': search_title,
            'type': 'movie',
            'y': request.query_params.get('Year', None),
            'page': 1
        }
        
        movies_data = []
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('Response') == 'True':
                total_results = int(data.get('totalResults', 0))
                external_total_pages = ceil(total_results / 10)

                for page in range(1, external_total_pages + 1):
                    params['page'] = page
                    response = requests.get(url, params=params)
                    data = response.json()
                    
                    if data.get('Response') == 'True':
                        for movie_data in data['Search']:
                            movie, created = Movie.objects.get_or_create(
                                title=movie_data['Title'],
                                year=int(movie_data['Year']),
                                imdbID=movie_data['imdbID'],
                                typeMovie=movie_data['Type'],
                                poster=movie_data['Poster']
                            )
                            movies_data.append(movie)
                    else:
                        break
                
                page = int(request.query_params.get('page', 1))
                items_per_page = 5
                total_pages = ceil(len(movies_data) / items_per_page)
                start_index = (page - 1) * items_per_page
                end_index = start_index + items_per_page

                paginated_movies = movies_data[start_index:end_index]
                serializer = MoviesSerializer(paginated_movies, many=True)
                return Response({
                    "total_pages": total_pages,
                    "current_page": page,
                    "results": serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": data.get("Error")}, status=status.HTTP_404_NOT_FOUND)
        
        except requests.RequestException:
            return Response({"error": "Falha na conexão com a API externa."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
