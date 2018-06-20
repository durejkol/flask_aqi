import json
import re
import requests
import yaml
from geopy.distance import vincenty
from geopy.geocoders import GoogleV3


class GoogleMapsService:
    def __init__(self):
        """
        Initialization to geopy's GoogleV3 geocoder.
        See readme.md for details
        """
        with open("config.yml", 'r') as ymlfile:
            self.cfg = yaml.load(ymlfile)
            self.google_api_key = self.cfg['google_api_key']
            self.geocoder = GoogleV3(self.google_api_key)

    def remove_local_number(self, address):
        """
        Method takes address provided by user, and returns
        it without local number
        ex: "Foo 1/3 -> Foo 1"
        """
        regex_results = re.search(r"(\d{1,3}\w{0,1}(\s{0,1}/\s{0,1}\d{1,3}))",
                                  address)
        if regex_results:
            if len(regex_results.groups()) == 2:
                self.address = address.replace(regex_results.group(2), "")

    def get_geocoding(self, address):
        """
        Method takes address provided by user, and returns
        Google Geocoding V3 response dictionary
        """
        self.address = self.remove_local_number(address)
        if len(address) > 1:
            geocoded_address = self.geocoder.geocode(address)
            if geocoded_address:
                self.location = geocoded_address.raw

    def get_lat_and_lng(self):
        """
        Method returns lat and lng from address geocoded in get_geocoding()
        """
        self.lat = self.location['geometry']['location']['lat']
        self.lng = self.location['geometry']['location']['lng']
        self.address = self.geocoder.reverse(str(self.lat)+", "+str(self.lng))
        return [self.lat, self.lng]

class AQIApiService:
    def __init__(self):
        with open("config.yml", 'r') as ymlfile:
            self.cfg = yaml.load(ymlfile)
            self.aqicn_api_key = self.cfg['aqicn_api_key']
        self.googleClient = GoogleMapsService()
        
    def get_aqi_from_address(self, address):
        self.googleClient.get_geocoding(address)
        if hasattr(self.googleClient,'location'):
            self.address = address
            self.address_coords = self.googleClient.get_lat_and_lng()
            url = f"https://api.waqi.info/feed/geo:{str(self.address_coords[0])};\
                   {str(self.address_coords[1])}/?token={str(self.aqicn_api_key)}"
            self.api_response = json.loads(requests.get(url).text)
            self.parse_api_response()
            return True
        else:
            return False

    def get_measurment_time(self):
        """
        Method gets measurment time from aqicn's api response
        """
        self.measurment_time = self.api_response['data']['time']['s']

    def get_pm25_and_pm10_value(self):
        """
        Method gets pm 25 and pm10 value from aqicn's api response
        if it is provided
        """
        pm25_value = self.api_response['data']['iaqi'].get('pm25')
        pm10_value = self.api_response['data']['iaqi'].get('pm10')

        if pm25_value:
            self.pm25_value = pm25_value['v']
        if pm10_value:
            self.pm10_value = pm10_value['v']

    def get_aqi_from_lat_lng(self,lat,lng):
        self.address_coords = [float(lat), float(lng)]
        url = f"https://api.waqi.info/feed/geo:{str(self.address_coords[0])};\
              {str(self.address_coords[1])}/?token={str(self.aqicn_api_key)}"
        self.api_response = json.loads(requests.get(url).text)
        self.parse_api_response()

    def parse_api_response(self):
        """
        Method parses aqicn response and extract aqi value, measure point name,
        measure point coords and distance.
        """
        self.aqi_value = self.api_response.get("data").get("aqi")
        self.get_measurment_time()
        self.get_pm25_and_pm10_value()
        self.measure_point_name = self.api_response.get("data").get("city").get("name")
        self.measure_point_coords = list(self.api_response["data"]["city"]["geo"])
        if abs(self.measure_point_coords[0] - self.address_coords[0]) > 5: #some aqicn "geo" values are in reversed order
            swap = self.measure_point_coords[0]
            self.measure_point_coords[0] = self.measure_point_coords[1]
            self.measure_point_coords[1] = swap
        self.calculate_distance()
        self.calculate_map_zoom()
        self.calculate_map_center()
        self.interpret_results()

    def calculate_distance(self):
        """
        Method calculates distance to closest aqi measure point and store it
        as integer and as string with proper unit depending on distance
        """
        self.distance = int(vincenty(self.address_coords, self.measure_point_coords).meters)
        if self.distance > 1000:
            self.distance_str = f"{str(round(self.distance/1000, 2))}km"
        else:
            self.distance_str = f"{str(self.distance)}m"

    def calculate_map_zoom(self):
        """
        Method takes distance and return map_zoom value which is needed in leaflet
        """
        if self.distance < 500:
            self.map_zoom = 15
        elif self.distance < 1000:
            self.map_zoom = 14
        elif self.distance < 1000000:
            self.map_zoom = 15 - int(self.distance**0.245/2)
        else:
            self.map_zoom = 0
            
    def calculate_map_center(self):
        """
        Method takes coords and return map_center value which is needed in leaflet
        """
        lat = (self.measure_point_coords[0] + self.address_coords[0])/2
        lng = (self.measure_point_coords[1] + self.address_coords[1])/2
        self.map_center = [lat, lng]
    def interpret_results(self):
        """
        Method interprets aqi value according to "About the Air Quality Levels"
        table which can be found at aqicn.org website
        """
        if self.aqi_value < 50:
            self.air_quality = "Dobra" 
            self.aqi_interpretation = "Jakość powietrza jest uznawana za zadowalającą," \
                                      "a zanieczyszczenie powietrza stanowi niewielkie" \
                                      " ryzyko lub jego brak."
            self.bootstrap_class = "list-group-item-success"
        elif self.aqi_value < 100:
            self.air_quality = "Średnia" 
            self.aqi_interpretation = "Jakość powietrza jest dopuszczalna, jednak niektóre" \
                                      " zanieczyszczenia mogą być umiarkowanie szkodliwe dla" \
                                      " bardzo małej liczby osób, które są niezwykle wrażliwe" \
                                      " na zanieczyszczenie powietrza."
            self.bootstrap_class = "list-group-item-warning"
        elif self.aqi_value < 150:
            self.air_quality = "Niezdrowa dla osób wrażliwych" 
            self.aqi_interpretation = "U osób wrażliwych mogą wystąpić negatywne skutki dla" \
                                      " zdrowia. Większość populacji może nie odczuwać" \
                                      " negatywnych objawów."
            self.bootstrap_class = "list-group-item-danger"
        elif self.aqi_value < 200:
            self.air_quality = "Niezdrowa" 
            self.aqi_interpretation = "Każdy może zacząć doświadczać negatywnych skutków" \
                                      " zdrowotnych. U osób wrażliwych mogą wystąpić " \
                                      "poważniejsze skutki zdrowotne."
            self.bootstrap_class = "list-group-item-danger"
        elif self.aqi_value < 300:
            self.air_quality = "Bardzo niezdrowa" 
            self.aqi_interpretation = "Ostrzeżenie zdrowotne, poziom alarmowy. " \
                                      "Bardzo prawdopodobny negatywny wpływ na całą populację."
            self.bootstrap_class = "list-group-item-danger"
        else:
            self.air_quality = "Zagrożenie dla życia" 
            self.aqi_interpretation = "Alarm Zdrowotny - każdy może doświadczyć " \
                                      "poważniejszych skutków zdrowotnych."
            self.bootstrap_class = "list-group-item-danger"
