import pandas as pd
import os
from decouple import config
from datetime import datetime
from datetime import timedelta
import numpy as np


class ModelPreprocessor:
    def __init__(self, data_path):
        self.data_path = data_path

    def process_RAT_before_8(self, date):
        df = pd.read_csv(self.data_path)
        df.drop("Unnamed: 0", inplace=True, axis=1)
        df.drop("Rider ID", inplace=True, axis=1)
        df.drop(
            "Reason For Travel", inplace=True, axis=1
        )  # here 26168 was null out of 26891

        valid_date = datetime(date[0], date[1], date[2])
        next_day = valid_date + timedelta(days=1)

        df_filtered = df[
            (
                (df["Requested Pickup Time"] > str(valid_date))
                & (df["Requested Pickup Time"] < str(next_day))
            )
            | (
                (df["Requested Dropoff Time"] > str(valid_date))
                & (df["Requested Dropoff Time"] < str(next_day))
            )
        ]
        # print(df_filtered.info)

        # Filter out the requests that arrived before 8 o'clock of the specific date
        time = datetime(date[0], date[1], date[2], 8)
        df_filtered_before_8 = df_filtered[
            (df_filtered["Request Creation Time"] <= str(time))
        ]
        # print(df_filtered_before_8.info)

        return df_filtered_before_8

    def add_time_windows(self, df):
        df["Requested Pickup Time"] = pd.to_datetime(
            df["Requested Pickup Time"], format="%Y-%m-%d %H:%M:%S"
        )
        df["Requested Dropoff Time"] = pd.to_datetime(
            df["Requested Dropoff Time"], format="%Y-%m-%d %H:%M:%S"
        )

        df["T_S_L_P"] = (df["Requested Pickup Time"] - timedelta(minutes=5)).fillna(
            df["Requested Dropoff Time"] - timedelta(hours=6)
        )
        df["T_S_L_D"] = (df["Requested Dropoff Time"] - timedelta(minutes=5)).fillna(
            df["Requested Pickup Time"]
        )
        df["T_S_U_P"] = (df["Requested Pickup Time"] + timedelta(minutes=5)).fillna(
            df["Requested Dropoff Time"]
        )
        df["T_S_U_D"] = (df["Requested Dropoff Time"] + timedelta(minutes=5)).fillna(
            df["Requested Pickup Time"] + timedelta(hours=6)
        )
        df["T_H_L_P"] = (df["Requested Pickup Time"] - timedelta(minutes=15)).fillna(
            df["Requested Dropoff Time"] - timedelta(hours=6)
        )
        df["T_H_L_D"] = (df["Requested Dropoff Time"] - timedelta(minutes=15)).fillna(
            df["Requested Pickup Time"]
        )
        df["T_H_U_P"] = (df["Requested Pickup Time"] + timedelta(minutes=15)).fillna(
            df["Requested Dropoff Time"]
        )
        df["T_H_U_D"] = (df["Requested Dropoff Time"] + timedelta(minutes=15)).fillna(
            df["Requested Pickup Time"] + timedelta(hours=6)
        )

        df.to_csv("Data/Test/test_data.csv")
        return df


def main():
    preprocessor = None

    try:
        preprocessor = ModelPreprocessor(data_path=config("data_path_RAT"))
        filtered_data = preprocessor.process_RAT_before_8(date=[2021, 5, 10])
        preprocessor.add_time_windows(filtered_data)

    except Exception as e:
        print("ERROR:", e)


if __name__ == "__main__":
    main()
