import requests, json
from haversine import haversine, Unit

# 구글 지도에서 주변 음식점 검색하기
def get_nearby_restaurants(api_key, keyword, latitude, longitude, radius=1000, language='ko'):
    endpoint_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    params = {
        'location': f"{latitude},{longitude}",
        'radius': radius,
        #'type': 'restaurant',
        'keyword': keyword,
        'language': language,
        'key': api_key
    }
    
    response = requests.get(endpoint_url, params=params)
    results = json.loads(response.text)

    nearby_restaurants_array = []

    for restaurant in results['results']:
        name = restaurant['name']
        address = restaurant['vicinity']
        rating = restaurant.get('rating', 'N/A')
        lat = restaurant['geometry']['location']['lat']
        lng = restaurant['geometry']['location']['lng']
        place_id = restaurant["place_id"]
        distance = "{:0.2f}".format(haversine((latitude, longitude), (lat, lng))) # 기본 단위는 km
 
        nearby_restaurants_array.append({"name": name, "adress": address, "rating": rating, "distance": distance, "place_id": place_id})
    
    return nearby_restaurants_array

# nearby_restaurants = get_nearby_restaurants(api_key, keyword, latitude, longitude)