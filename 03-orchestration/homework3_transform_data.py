import pandas as pd
import pickle
from sklearn.feature_extraction import DictVectorizer
import os
import scipy.sparse
from typing import Union, Any, Dict
import numpy as np
import argparse
import json


def create_X(
    dicts: list[Dict[str, Any]], dv: Union[DictVectorizer, None] = None
) -> tuple[scipy.sparse.csr_matrix, DictVectorizer]:
    if dv is None:
        # The `sparse=True` argument specifies that the output of the transformation
        # should be a SciPy sparse matrix rather than a dense NumPy array.
        dv = DictVectorizer(sparse=True)
        X = dv.fit_transform(dicts)
    else:
        X = dv.transform(dicts)

    return X, dv


def transform_data(
    df_train_path: str, df_val_path: str, models_dir: str
) -> tuple[scipy.sparse.csr_matrix, np.ndarray[Any, Any], scipy.sparse.csr_matrix, np.ndarray[Any, Any], DictVectorizer]:
    print(f"df_train_path: {df_train_path}")
    print(f"df_val_path: {df_val_path}")
    print(f"models_dir: {models_dir}")

    df_train = pd.read_parquet(df_train_path)
    df_val = pd.read_parquet(df_val_path)

    target = "duration"
    categorical = ['PULocationID', 'DOLocationID']
    train_dicts = df_train[categorical].to_dict(orient='records')
    val_dicts = df_val[categorical].to_dict(orient='records')

    X_train, dv = create_X(train_dicts)
    X_val, _ = create_X(val_dicts, dv)

    y_train = df_train[target].values
    y_val = df_val[target].values

    del df_train, df_val

    return X_train, y_train, X_val, y_val, dv


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transform the train and validation data")
    parser.add_argument("--df_train_path", type=str, help="path to train df")
    parser.add_argument("--df_val_path", type=str, help="path to validation df")
    parser.add_argument("--models_dir", type=str, help="path to models dir")
    args = parser.parse_args()
    df_train_path = args.df_train_path
    df_val_path = args.df_val_path
    models_dir = args.models_dir

    X_train, y_train, X_val, y_val, dv = transform_data(
        df_train_path=df_train_path, df_val_path=df_val_path, models_dir=models_dir
    )

    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Define output file paths for transformed data within the temp directory
    x_train_out_path = os.path.join(temp_dir, "X_train.npz")
    y_train_out_path = os.path.join(temp_dir, "y_train.npy")
    x_val_out_path = os.path.join(temp_dir, "X_val.npz")
    y_val_out_path = os.path.join(temp_dir, "y_val.npy")
    # Define path for the DictVectorizer (preprocessor) in the models directory
    if not models_dir:
        raise ValueError("models_dir is not set.")
    dv_path = os.path.join(models_dir, "preprocessor.b")

    # Save the transformed data arrays/matrices
    scipy.sparse.save_npz(x_train_out_path, X_train)
    np.save(y_train_out_path, y_train)
    scipy.sparse.save_npz(x_val_out_path, X_val)
    np.save(y_val_out_path, y_val)
    # Save the DictVectorizer
    with open(dv_path, "wb") as f_out:
        pickle.dump(dv, f_out)

    # Remove the original Parquet files from df_train_path and df_val_path
    if os.path.exists(df_train_path):
        os.remove(df_train_path)

    if os.path.exists(df_val_path):
        os.remove(df_val_path)

    # Prepare paths for XCom output
    # This JSON string must be the last print output of the script for Airflow XCom to work correctly
    output_xcom_paths = {
        "x_train_path": x_train_out_path,
        "y_train_path": y_train_out_path,
        "x_val_path": x_val_out_path,
        "y_val_path": y_val_out_path,
        "dv_path": dv_path,
    }
    print(json.dumps(output_xcom_paths))
