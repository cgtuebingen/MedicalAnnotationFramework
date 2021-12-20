import sqlite3
import os
import pickle

from typing import List, Union

# TODO: 'file' value references the uid in either 'videos', 'images', or 'whole slide images'
#  (depends on 'modality' value),
#  therefore no foreign key constraint here; need to implement it somewhere else (?)
CREATE_ANNOTATIONS_TABLE = """
    CREATE TABLE IF NOT EXISTS annotations (
    uid INTEGER PRIMARY KEY,
    modality INTEGER NOT NULL,
    file INTEGER NOT NULL,
    patient INTEGER NOT NULL,
    shape BLOB,
    label INTEGER NOT NULL,
    FOREIGN KEY (patient) REFERENCES patients(uid),
    FOREIGN KEY (label) REFERENCES labels(uid));"""

CREATE_VIDEOS_TABLE = """
    CREATE TABLE IF NOT EXISTS videos (
    uid INTEGER PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE);"""

CREATE_IMAGES_TABLE = """
    CREATE TABLE IF NOT EXISTS images (
    uid INTEGER PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE);"""

CREATE_WSI_TABLE = """
    CREATE TABLE IF NOT EXISTS 'whole slide images' (
    uid INTEGER PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE);"""

CREATE_PATIENTS_TABLE = """
    CREATE TABLE IF NOT EXISTS patients (
    uid INTEGER PRIMARY KEY,
    some_id INTEGER,
    another_id INTEGER);"""

CREATE_LABELS_TABLE = """
    CREATE TABLE IF NOT EXISTS labels (
    uid INTEGER PRIMARY KEY,
    label_class TEXT NOT NULL UNIQUE);"""

ADD_ANNOTATION = "INSERT INTO annotations (modality, file, patient, shape, label) VALUES (?, ?, ?, ?, ?);"
ADD_VIDEO = "INSERT INTO videos (filename) VALUES (?);"
ADD_IMAGE = "INSERT INTO images (filename) VALUES (?);"
ADD_WSI = "INSERT INTO 'whole slide images' (filename) VALUES (?);"
ADD_PATIENT = "INSERT INTO patients (some_id, another_id) VALUES (?, ?);"
ADD_LABEL = "INSERT INTO labels (label_class) VALUES (?);"

DELETE_FILE_ANNOTATIONS = "DELETE FROM annotations WHERE modality = ? AND file = ?"


class SQLiteDatabase:
    """class to control an SQL database"""
    def __init__(self, database_path: str, new_db: bool = False):
        """
        Connect to database as initialization
        :param database_path: path to the database
        :param new_db: indicates whether the database already exists or not
        """
        self.connection = sqlite3.connect(database_path)
        self.cursor = self.connection.cursor()
        self.file_tables = ['videos', 'images', "'whole slide images'"]

        if new_db:
            self.create_initial_tables()
            # TODO: many functions require the existence of at least one image.
            #  Maybe exchange filler image by something else
            # self.set_filler(True)
            self.add_patient(10, 100)  # TODO: Implement Patient references

        with self.connection:
            self.cursor.execute(f"PRAGMA foreign_keys = ON;")

    def add_annotation(self, modality: int, file: int, patient: int, shape: bytes, label: int):
        """ adds an entry to the annotation table using the parameter values"""
        with self.connection:
            self.cursor.execute(ADD_ANNOTATION, (modality, file, patient, shape, label))

    def add_file(self, filename: str, filetype: str):
        """
        adds a file to the database
        :param filename: the name of the file to be added
        :param filetype: indicates whether it is a video, image or whole slide image
        """
        with self.connection:

            # TODO: Extend by other accepted types, substitute 'whatever' by actual WSI type
            if filetype in ['mp4']:
                self.cursor.execute(ADD_VIDEO, (filename,))
            elif filetype in ['png', 'jpg', 'jpeg']:
                self.cursor.execute(ADD_IMAGE, (filename,))
            elif filetype in ['whatever']:
                self.cursor.execute(ADD_WSI, (filename,))

    def add_label(self, label_class: str):
        """ add a new label class to database"""
        with self.connection:
            self.cursor.execute(ADD_LABEL, (label_class,))

    def add_patient(self, some_id: int, another_id: int):
        """ add a new patient to database"""
        with self.connection:
            self.cursor.execute(ADD_PATIENT, (some_id, another_id))

    def create_initial_tables(self):
        """
        sets up the structure defined in
        https://docs.google.com/spreadsheets/d/1lJ_ywagiQVbEQ2LyJdRZNwUjUeGSy73Z2PXkOzsXx6U/edit#gid=0
        """
        with self.connection:
            self.cursor.execute(CREATE_VIDEOS_TABLE)
            self.cursor.execute(CREATE_IMAGES_TABLE)
            self.cursor.execute(CREATE_WSI_TABLE)
            self.cursor.execute(CREATE_PATIENTS_TABLE)
            self.cursor.execute(CREATE_LABELS_TABLE)
            self.cursor.execute(CREATE_ANNOTATIONS_TABLE)

    def delete_file(self, filename: str):
        """ this method deletes a file from the database and removes all corresponding annotations"""
        modality, file = self.get_uids_from_filename(filename)
        table_name = self.file_tables[modality]
        with self.connection:
            self.cursor.execute(DELETE_FILE_ANNOTATIONS, (modality, file))
            self.cursor.execute("DELETE FROM {} WHERE filename = ?".format(table_name), (filename,))

    def filler_exists(self):
        """ checks if database contains a filler image
        :return: bool; True if filler exists, False otherwise
        """
        with self.connection:
            filler = self.cursor.execute("SELECT filename FROM images WHERE filename = 'images/filler.png'").fetchone()
        return True if filler else False

    def get_images(self):
        """
        :return: a list of all image names which are currently stored in the database
        """
        with self.connection:
            image_paths = self.cursor.execute("SELECT filename FROM images").fetchall()
        return [image_path[0] for image_path in image_paths]

    def get_column_names(self, table_name: str):
        """
        :param table_name: the table to be searched in
        :return: all column names of the specified table
        """
        with self.connection:
            columns = self.cursor.execute("PRAGMA table_info({})".format(table_name)).fetchall()
        return [col[0] for col in columns]

    def get_label_classes(self):
        """
        :return: a list of all label classes which are currently stored in the database
        """
        with self.connection:
            label_classes = self.cursor.execute("SELECT label_class FROM labels").fetchall()
        return [label_class[0] for label_class in label_classes]

    def get_label_from_imagepath(self, imagepath: str):
        """
        :param imagepath: the image name to be searched in
        :return: a list of all label shapes related to the specified image
        """
        with self.connection:
            image_id = self.get_uid_from_filename("images", imagepath)
            labels = self.cursor.execute("""SELECT shape FROM annotations
                                            WHERE modality = 1 AND file = ?""", (image_id,)).fetchall()
        return check_for_bytes(labels)

    def get_uid_from_filename(self, table_name: str, filename: str) -> int:
        """
        :param table_name: videos, images, or whole slide images
        :param filename: name of the file
        :return: the uid which is related to the specified file
        """
        with self.connection:
            query = "SELECT uid FROM " + table_name + " WHERE filename = ?"
            self.cursor.execute(query, (filename,))
            result = self.cursor.fetchone()
        return result[0] if result is not None else None

    def get_uids_from_filename(self, filename: str) -> tuple:
        """
        :param filename: name of the file
        :return: a tuple holding: modality uid (video/image/whole slide image) and file uid
        """
        modality, file = None, None
        for i, table_name in enumerate(self.file_tables):
            file = self.get_uid_from_filename(table_name, filename)
            if file is not None:
                modality = i
                break
        return modality, file

    def get_uid_from_label(self, label: str) -> int:
        """
        :param label: the label class to get the uid from
        :return: the uid of the label class if existing
        """
        with self.connection:
            self.cursor.execute("""SELECT uid FROM labels WHERE label_class = ?""", (label,))
            result = self.cursor.fetchone()
        return result[0] if result is not None else None

    def update_image_annotations(self, image_name: str, entries: list):
        """
        updates the annotations associated with a given image
        :param image_name: the image to be updated
        :param entries: list of dictionaries representing the annotation entries
        """
        with self.connection:

            # delete all currently stored annotations for the image
            modality, file = self.get_uids_from_filename(image_name)
            self.cursor.execute("""DELETE FROM annotations WHERE modality = ?
                                AND file = ?""", (modality, file))

            # add new, updated list of annotations
            for entry in entries:
                self.cursor.execute("""INSERT INTO annotations (modality, file, patient, shape, label) 
                    VALUES (:modality, :file, :patient, :shape, :label)""", entry)

    def update_labels(self, classes: list):
        """
        goes through a list of label class names and adds them to database if they don't already exist
        :param classes: list of label classes
        """
        with self.connection:
            for label_class in classes:
                self.cursor.execute("""SELECT * FROM labels WHERE label_class = ?""", (label_class,))
                if not self.cursor.fetchone():
                    self.cursor.execute("""INSERT INTO labels (label_class) VALUES (?)""", (label_class,))

    def set_filler(self, f: bool):
        """
        either adds or removes a filler to/from database
        filler should be added when database contains no other files
        :param f: whether filler should be added or removed
        """
        filler = 'images/filler.png'
        if f:
            self.add_file(filler, 'png')
        else:
            self.delete_file(filler)


def check_for_bytes(lst: List[tuple]) -> Union[List[list], list]:
    """ Iterates over a list of tuples and depickles byte objects. The output is converted depending on how many entries
    the initial list contains. If its just one per sub-list, each of them is removed

        :param tuple lst: tuple to be searched for
        :returns: Either a List of Lists or just a List depending on how many entries are put in
    """
    lst = convert_to_list(lst)
    for _list_idx, _list_entry in enumerate(lst):

        # this replaces lists with only one entry
        if len(_list_entry) == 1:
            if isinstance(_list_entry[0], bytes):
                lst[_list_idx] = pickle.loads(_list_entry[0])
            else:
                lst[_list_idx] = _list_entry[0]
        else:
            for _tuple_idx, _value in enumerate(list(_list_entry)):
                if isinstance(_value, bytes):
                    lst[_list_idx][_tuple_idx] = pickle.loads(_value)
                else:
                    continue

    if len(lst) == 1:
        # lst = lst[0]
        pass

    return lst


def convert_to_list(lst: List[tuple]) -> List[list]:
    return [list(elem) for elem in lst]


if __name__ == "__main__":
    db = SQLiteDatabase("../examples/dummybase.db")
    with db.connection:
        db.cursor.execute("SELECT some_id FROM patients WHERE another_id = 12")
    print("Did it work?")
