import pandas as pd
import os
from decouple import config


class Preprocessor:
    def __init__(self, data_path_RAT):
        self.data_path_RAT = data_path_RAT

    def process_data_RAT(self):
        files = [
            os.path.join(self.data_path_RAT, filename)
            for filename in os.listdir(self.data_path_RAT)
            if filename.startswith("Ride Requests-")
        ]
        data = []
        for f in files:
            data.append(pd.read_csv(f, index_col=None, header=0))
        df = pd.concat(data, axis=0, ignore_index=True)

        # convert yes no to 1 and 0
        df["Wheelchair"] = df["Wheelchair Accessible"].map({"Yes": 1, "No": 0})

        chosen_columns = [
            "Request Creation Time",
            "Wheelchair",
            "Request ID",
            "Rider ID",
            "Number of Passengers",
            "Requested Pickup Time",
            "Requested Dropoff Time",
            "Origin Lat",
            "Origin Lng",
            "Destination Lat",
            "Destination Lng",
            "Reason For Travel",
        ]
        data = df[chosen_columns]
        print(data.head())
        data.to_csv("data_RAT.csv")


def main():
    preprocessor = None

    try:
        preprocessor = Preprocessor(data_path_RAT=config("data_path_RAT"))
        print("Preprocessing data: ")
        preprocessor.process_data_RAT()

    except Exception as e:
        print("ERROR:", e)


if __name__ == "__main__":
    main()
