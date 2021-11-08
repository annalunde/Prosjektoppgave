import requests
from decouple import config

url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=40.6655101%2C-73.89188969999998&destinations=40.659569%2C-73.933783%7C40.729029%2C-73.851524%7C40.6860072%2C-73.6334271%7C40.598566%2C-73.7527626&key={api_keys}".format(
    api_keys=config("api_key_for_requests")
)

payload = {}
headers = {}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)
