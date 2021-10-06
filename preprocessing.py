import pandas as pd
import os
import numpy as np
#from decouple import config


class Preprocessor:
    def __init__(self, data_path):
        self.data_path = data_path

    def import_data_TT(self):
        files = [
            os.path.join(self.data_path, filename)
            for filename in os.listdir(self.data_path)
            if filename.startswith("Statistik")
        ]
        data = []
        for f in files:
            data.append(pd.read_csv(f, index_col=None, header=0))
        df = pd.concat(data, axis=0, ignore_index=True)
        chosen_columns = [
            "Id",
            "Hämt-tid",
            "Lämna-tid",
            "Resetyp",
            "Krav",
            "H-lat",
            "H-lon",
            "L-lat",
            "L-lon",
        ]
        df = df[chosen_columns]
        df = df.drop(df[df["Resetyp"] != "FRI"].index)
        df = df.drop("Resetyp", 1)
        df = df.rename(columns={"Id": "Request ID", "Hämt-tid": "Requested Pickup Time", "Lämna-tid": "Requested Dropoff Time", "H-lat": "Origin Lat", "H-lon": "Origin Lng", "L-lat": "Destination Lat", "L-lon": "Destination Lng"})
        df.insert(0, "Request Creation Time", df["Requested Pickup Time"])
        df.insert(1, "Wheelchair Accessible", 0)
        df["Wheelchair Accessible"] = np.where(df["Krav"].str.contains("WHEL"),1,0)
        df = df.drop("Krav", 1)
        df.insert(3, "Rider ID", None)
        df.insert(4, "Number of Passengers", 1)
        df.insert(len(df.columns), "Reason For Travel", None)

        date_time = []
        date = df["Requested Pickup Time"].values.tolist()
        time = df["Requested Dropoff Time"].values.tolist()

        for i in range(len(df.index)):
            date_time.append(date[i][0:10]+" "+time[i])

        df["Requested Dropoff Time"] = date_time
        print(df.columns)
        print(df.head())
        df.to_csv("data_TT.csv")


def main():
    preprocessor = None

    try:
        preprocessor = Preprocessor(data_path=r"C:\Users\Bruker\OneDrive - NTNU\Documents\9. semester\Prosjektoppgave\Prosjektoppgave\Data")
        print("Preprocessing data: ")
        preprocessor.import_data_TT()

    except Exception as e:
        print("ERROR:", e)


if __name__ == "__main__":
    main()