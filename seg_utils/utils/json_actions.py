import os
import pickle
import sys
import json
import glob
from pathlib import Path
from database import SQLiteDatabase


def main():
    four = 4
    label_dir = "/home/nico/isys/data/images"
    database_path = "/home/nico/isys/data/database.db"
    replaceTraceWithPolygon(database_path, label_dir)


def convert_json_to_sql(image_dir: str, database_path: str):
    database = SQLiteDatabase(database_path)
    database.create_labels_table()
    for idx, file in enumerate(sorted(glob.glob(os.path.join(image_dir, "*.json")))):
        try:
            _file = open(file)
            _json = json.load(_file)
            if _json['imageData']:
                del _json['imageData']
            label_list = [_label for _label in _json['shapes']]
            database.add_label("images/" + _json['imagePath'], label_list)
            print(f"Processed Label {idx+1}/{len(glob.glob(os.path.join(image_dir, '*.json')))}")
        except ValueError:
            pass


def remove_label_category(database_path: str, label_dir: str, category: str):
    database = SQLiteDatabase(database_path)
    for idx, file in enumerate(sorted(glob.glob(os.path.join(label_dir, "*.json")))):
        with open(file, 'r') as _file:
            _json = json.load(_file)
        for _idx, _shape in enumerate(_json['shapes']):
            if _shape['label'] == category:
                _json['shapes'].pop(_idx)
            else:
                continue
            four = 4
        with open(file, 'w') as data_file:
            # Save file to json again - DEPRECATED as soon as i work with full database support
            json.dump(_json, data_file)
            label_list = [_label for _label in _json['shapes']]
            filename = "images/" + os.path.basename(file).replace(".json", ".png")
            database.update_entry("labels", "image_path", filename, "label_list", pickle.dumps(label_list))
            print(f"Processed Label {idx + 1}/{len(glob.glob(os.path.join(label_dir, '*.json')))}")


def replaceTraceWithPolygon(database_path: str, label_dir: str):
    database = SQLiteDatabase(database_path)
    for idx, file in enumerate(sorted(glob.glob(os.path.join(label_dir, "*.json")))):
        with open(file, 'r') as _file:
            _json = json.load(_file)
        for _idx, _shape in enumerate(_json['shapes']):
            if _shape['shape_type'] == 'trace':
                _shape['shape_type'] = 'polygon'
        with open(file, 'w') as data_file:
            # Save file to json again - DEPRECATED as soon as i work with full database support
            json.dump(_json, data_file)
            label_list = [_label for _label in _json['shapes']]
            filename = "images/" + os.path.basename(file).replace(".json", ".png")
            database.update_entry("labels", "image_path", filename, "label_list", pickle.dumps(label_list))
            print(f"Processed Label {idx + 1}/{len(glob.glob(os.path.join(label_dir, '*.json')))}")

if __name__ == "__main__":
    main()