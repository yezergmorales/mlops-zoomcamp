import pandas as pd
import argparse
import json
import os


def read_dataframe(color_line: str, year: int, month: int) -> pd.DataFrame:
    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{color_line}_tripdata_{year:4}-{month:02}.parquet"
    df = pd.read_parquet(url)
    print(f"------------------------> raw records-{year}-{month}: df.shape: {df.shape}")

    if color_line == "yellow":
        df["duration"] = df.tpep_dropoff_datetime - df.tpep_pickup_datetime
    else:
        df["duration"] = df.lpep_dropoff_datetime - df.lpep_pickup_datetime

    df.duration = df.duration.dt.total_seconds() / 60
    df = df[(df.duration >= 1) & (df.duration <= 60)]

    categorical = ["PULocationID", "DOLocationID"]
    df[categorical] = df[categorical].astype(str)

    return df


def load_data(color_line: str, year: int, month: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_year = year
    train_month = month
    if train_month == 12:
        val_year = year + 1
        val_month = 1
    else:
        val_year = year
        val_month = month + 1

    df_train = read_dataframe(color_line=color_line, year=train_year, month=train_month)
    df_val = read_dataframe(color_line=color_line, year=val_year, month=val_month)
    print(f"------------------------> df_train.shape: {df_train.shape} --> year: {train_year}, month: {train_month}")
    print(f"------------------------> df_val.shape: {df_val.shape} --> year: {val_year}, month: {val_month}")

    return df_train, df_val


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load train and validation data")
    parser.add_argument("-cl", "--color_line", type=str, help="Color line for the NYC taxi data")
    parser.add_argument("-y", "--year", type=int, help="Year for the training data")
    parser.add_argument("-m", "--month", type=int, help="Month for the training data")

    args = parser.parse_args()
    year = args.year
    month = args.month
    color_line = args.color_line
    df_train, df_val = load_data(color_line=color_line, year=year, month=month)

    # Define file paths
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    train_path = os.path.join(temp_dir, "df_train.parquet")
    val_path = os.path.join(temp_dir, "df_val.parquet")

    # Save dataframes
    df_train.to_parquet(train_path, index=False)
    df_val.to_parquet(val_path, index=False)

    del df_train, df_val

    # Prepare paths for XCom
    output_paths = {
        "df_train_path": train_path,
        "df_val_path": val_path
    }
    # Print JSON string as the last line for XCom
    print(json.dumps(output_paths))
