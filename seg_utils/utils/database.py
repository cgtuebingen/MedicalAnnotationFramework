import sqlite3
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
    filename TEXT NOT NULL UNIQUE,
    patient INTEGER,
    FOREIGN KEY (patient) REFERENCES patients(uid));"""

CREATE_IMAGES_TABLE = """
    CREATE TABLE IF NOT EXISTS images (
    uid INTEGER PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    patient INTEGER,
    FOREIGN KEY (patient) REFERENCES patients(uid));"""

CREATE_WSI_TABLE = """
    CREATE TABLE IF NOT EXISTS 'whole slide images' (
    uid INTEGER PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    patient INTEGER,
    biopsy_id INTEGER,
    year INTEGER,
    staining TEXT,
    width INTEGER,
    height INTEGER,
    manufacturer TEXT,
    institution TEXT,
    FOREIGN KEY (patient) REFERENCES patients(uid));"""

CREATE_PATIENTS_TABLE = """
    CREATE TABLE IF NOT EXISTS patients (
    uid INTEGER PRIMARY KEY,
    some_id INTEGER UNIQUE,
    another_id INTEGER);"""

CREATE_LABELS_TABLE = """
    CREATE TABLE IF NOT EXISTS labels (
    uid INTEGER PRIMARY KEY,
    label_class TEXT NOT NULL UNIQUE);"""

ADD_ANNOTATION = "INSERT INTO annotations (modality, file, patient, shape, label) VALUES (?, ?, ?, ?, ?);"
ADD_VIDEO = "INSERT INTO videos (filename, patient) VALUES (?, ?);"
ADD_IMAGE = "INSERT INTO images (filename, patient) VALUES (?, ?);"
ADD_WSI = "INSERT INTO 'whole slide images' (filename, patient) VALUES (?, ?);"
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

        with self.connection:
            self.cursor.execute(f"PRAGMA foreign_keys = ON;")

    def add_annotation(self, modality: int, file: int, patient: int, shape: bytes, label: int):
        """ adds an entry to the annotation table using the parameter values"""
        with self.connection:
            self.cursor.execute(ADD_ANNOTATION, (modality, file, patient, shape, label))

    def add_file(self, filename: str, modality: int, patient: str):
        """
        adds a file to the database
        :param filename: the name of the file to be added
        :param modality: indicates whether it is a video (0), image (1) or whole slide image (2)
        :param patient: a patient id which may be added to the database
        """
        with self.connection:

            # check if patient already exists, add if necessary
            p = self.cursor.execute("""SELECT uid FROM patients WHERE some_id = ?""", (patient,)).fetchone()
            patient = p[0] if p else self.add_patient(patient)

            if modality == 0:
                self.cursor.execute(ADD_VIDEO, (filename, patient))
            elif modality == 1:
                self.cursor.execute(ADD_IMAGE, (filename, patient))
            elif modality == 2:
                self.cursor.execute(ADD_WSI, (filename, patient))

    def add_label(self, label_class: str):
        """ add a new label class to database"""
        with self.connection:
            self.cursor.execute(ADD_LABEL, (label_class,))

    def add_patient(self, some_id: str, another_id: str = "2"):
        """ add a new patient to database
        returns the uid of the new patient"""
        with self.connection:
            # make sure patient does not already exist
            if self.cursor.execute("SELECT uid FROM patients WHERE some_id = ?", (some_id,)).fetchone():
                return
            self.cursor.execute(ADD_PATIENT, (some_id, another_id))
            result = self.cursor.execute("SELECT uid FROM patients WHERE some_id = ?", (some_id,)).fetchone()
        return result[0]

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

    def get_column_names(self, table_name: str) -> list:
        """
        :param table_name: the table to be searched in
        :return: all column names of the specified table
        """
        with self.connection:
            columns = self.cursor.execute("PRAGMA table_info({})".format(table_name)).fetchall()
        return [col[0] for col in columns]

    def get_images(self) -> list:
        """ returns a list of all image names which are currently stored in the database"""
        with self.connection:
            image_paths = self.cursor.execute("SELECT filename FROM images").fetchall()
        return [image_path[0] for image_path in image_paths]

    def get_label_classes(self) -> list:
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

    def get_patients(self):
        """returns all patient ids (not the uids)"""
        with self.connection:
            result = self.cursor.execute("SELECT some_id FROM patients").fetchall()
        return [res[0] for res in result]

    def get_patient_by_filename(self, filename: str):
        """returns the corresponding patient uid of an image"""
        with self.connection:
            self.cursor.execute("SELECT patient FROM images WHERE filename = ?", (filename,))
            return self.cursor.fetchone()[0]

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


def check_for_bytes(lst: List[tuple]) -> Union[List[list], list]:
    """ Iterates over a list of tuples and de-pickles byte objects. The output is converted depending on how many entries
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
