import os
import argparse
import json


def create_model_folder(folder_name: str) -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(script_dir, folder_name)

    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        print(f"Folder '{models_dir}' created.")

    return models_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="create a model folder")
    parser.add_argument(
        "-mf",
        "--model_folder",
        type=str,
        default="models",
        help="name for the folder where the models will be stored in local",
    )
    args = parser.parse_args()
    model_folder = args.model_folder
    models_dir = create_model_folder(folder_name=model_folder)

    # Prepare paths for XCom
    output_paths = {
        "models_dir": models_dir
    }
    # Print JSON string as the last line for XCom
    print(json.dumps(output_paths))
