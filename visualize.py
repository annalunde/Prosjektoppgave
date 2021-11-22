import pandas as pd
import numpy as np
from decouple import config

# import requests
import folium  # Mapping application
from IPython.display import display

# import geopy.distance  # Calculate distance between starting and ending points


class Visualizer:
    def __init__(self, data_path_before, data_path_after):
        self.data_path_before = data_path_before
        self.data_path_after = data_path_after

    def generate_map(
        self,
        data,
        map_location,
        map_style,
        start_lat_col,
        start_long_col,
        start_color,
        end_lat_col,
        end_long_col,
        end_color,
    ):

        """

        Background:
        This function will return a folium map with starting and ending trip location markers.

        Inputs:

        map_location: This is where you want to set the default location for the map. Format: [lat_value,long_value]
        map_style: The style of map you want to render. I am using "cartodbpositron" style.
        start_lat_col: Column where your trip starting latitude points are.
        start_long_col: Column where your trip starting longitude points are.
        start_color: The color of the starting circle you want to render on the folium map.
        end_lat_col: Column where your trip ending latitude points are.
        end_long_col: Column where your trip ending longitude points are.
        end_color: The color of the ending circle you want to render on the folium map.

        Outputs:

        folium_map: This is the folium map we created.


        """

        # generate a new map
        folium_map = folium.Map(location=map_location, zoom_start=11, tiles=map_style)

        # for each row in the data, add a cicle marker
        data_size = len(data)
        counter = 1
        for index, row in data.iterrows():
            if counter < 9:
                # add starting location markers to the map
                folium.CircleMarker(
                    location=(row[start_lat_col], row[start_long_col]),
                    color=start_color,
                    radius=5,
                    weight=1,
                    fill=True,
                ).add_to(folium_map)

                # add end location markers to the map
                folium.CircleMarker(
                    location=(row[end_lat_col], row[end_long_col]),
                    color=end_color,
                    radius=5,
                    weight=1,
                    fill=True,
                ).add_to(folium_map)

            if counter == 9:
                # add starting location markers to the map
                folium.CircleMarker(
                    location=(row[start_lat_col], row[start_long_col]),
                    color="#DB9D15",
                    radius=5,
                    weight=1,
                    fill=True,
                ).add_to(folium_map)

                # add end location markers to the map
                folium.CircleMarker(
                    location=(row[end_lat_col], row[end_long_col]),
                    color="#47A77E",
                    radius=5,
                    weight=1,
                    fill=True,
                ).add_to(folium_map)
            
            if counter > 9:
                # add starting location markers to the map
                folium.CircleMarker(
                    location=(row[start_lat_col], row[start_long_col]),
                    color="#A86ED4",
                    radius=5,
                    weight=1,
                    fill=True,
                ).add_to(folium_map)

                # add end location markers to the map
                folium.CircleMarker(
                    location=(row[end_lat_col], row[end_long_col]),
                    color="#A86ED4",
                    radius=5,
                    weight=1,
                    fill=True,
                ).add_to(folium_map)

            counter += 1

        folium_map.save("map_requests.html")

    def visualize_on_map(self):
        data_before = pd.read_csv(self.data_path_before)
        data_after = pd.read_csv(self.data_path_after)
        data = data_before.append(data_after)

        # Let's add the starting and ending lat longs to the folium map using the generate_map function
        return self.generate_map(
            data,
            [59.9139, 10.7522],
            "cartodbpositron",
            "Origin Lat",
            "Origin Lng",
            "#E2366B",
            "Destination Lat",
            "Destination Lng",
            "#30506B",
        )


def main():
    visualizer = None

    try:
        visualizer = Visualizer(data_path_before=config("data_path_case_study"),data_path_after=config("data_path_case_study_events"))
        print("Visualizing data: ")
        visualizer.visualize_on_map()

    except Exception as e:
        print("ERROR:", e)


if __name__ == "__main__":
    main()
