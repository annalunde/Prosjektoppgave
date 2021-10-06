import pandas as pd
import os

class Preprocessor:
    def __init__(self, data_path):
        self.data_path = data_path
        

    def import_data_RAT(self):
        files = [os.path.join(self.data_path, filename) for filename in os.listdir(self.data_path) if filename.startswith("Ride Requests-")]
        data = []
        for f in files:
                data.append(pd.read_csv(f, index_col=None, header=0))
        df = pd.concat(data, axis=0, ignore_index=True)
        chosen_columns = ["Request Creation Time",  "Wheelchair Accessible", "Request ID", "Rider ID", "Number of Passengers", "Requested Pickup Time", "Requested Dropoff Time", "Origin Lat", "Origin Lng", "Destination Lat", "Destination Lng", "Reason For Travel"]
        data = df[chosen_columns]
        print(data.head())

def main():
    preprocessor = None

    try:
        preprocessor = Preprocessor(data_path="/Users/Anna/Desktop/Prosjektoppgave/Kodebase/Prosjektoppgave/Data")
        print("Preprocessing data: ")
        preprocessor.import_data_RAT()
        


    except Exception as e:
        print("ERROR:", e)
    

if __name__ == "__main__":
    main()