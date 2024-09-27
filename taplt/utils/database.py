import enum
import sqlite3
import pickle
import pathlib
import shutil
import os
import uuid

from typing import List, Union
from taplt.utils.project_structure import modality, create_project_structure, Structure, Modality
from taplt.utils.settings import SETTINGS, get_tooltip

from PySide6.QtCore import Signal, QObject, QSettings

# uid is the unique patent id, and therefore it needs to be a string, since most of the ids are hashes

CREATE_PATIENTS_TABLE = """
    CREATE TABLE IF NOT EXISTS patients (
        uid TEXT PRIMARY KEY);"""

CREATE_VIDEOS_TABLE = """
    CREATE TABLE IF NOT EXISTS videos (
        uid TEXT,
        filename TEXT NOT NULL,
        PRIMARY KEY (uid, filename),
        FOREIGN KEY (uid) REFERENCES patients(uid)
            ON DELETE CASCADE ON UPDATE CASCADE);"""

CREATE_IMAGES_TABLE = """
    CREATE TABLE IF NOT EXISTS images (
        uid TEXT,
        filename TEXT NOT NULL,
        PRIMARY KEY (uid, filename),
        FOREIGN KEY (uid) REFERENCES patients(uid)
            ON DELETE CASCADE ON UPDATE CASCADE);"""

CREATE_WSI_TABLE = """
    CREATE TABLE IF NOT EXISTS slides (
        uid TEXT,
        filename TEXT NOT NULL,
        biopsy_id INTEGER,
        year INTEGER,
        staining TEXT,
        width INTEGER,
        height INTEGER,
        manufacturer TEXT,
        institution TEXT,
        PRIMARY KEY (uid, filename),
        FOREIGN KEY (uid) REFERENCES patients(uid)
            ON DELETE CASCADE ON UPDATE CASCADE);"""

# TODO: Add foreign key constraints for uid and filename so that it references only one table
CREATE_ANNOTATIONS_TABLE = """
    CREATE TABLE IF NOT EXISTS annotations (
        annotation_id TEXT PRIMARY KEY,
        frame_number INTEGER,
        uid TEXT,
        filename TEXT NOT NULL,
        shape_type TEXT NOT NULL,
        flags BLOB,
        group_id TEXT,
        comment TEXT,
        label TEXT NOT NULL);"""

CREATE_LABELS_TABLE = """
    CREATE TABLE IF NOT EXISTS labels (
        uid TEXT,
        label TEXT NOT NULL,
        filename TEXT,
        PRIMARY KEY (uid, label, filename)
        FOREIGN KEY (uid) REFERENCES patients(uid)
            ON DELETE CASCADE ON UPDATE CASCADE);"""

CREATE_POINTS_TABLE = """
    CREATE TABLE IF NOT EXISTS points (
        annotation_id TEXT,
        vertex_id INTEGER,
        x FLOAT,
        y FLOAT,
        PRIMARY KEY (annotation_id, x, y),
        FOREIGN KEY (annotation_id) REFERENCES annotations(annotation_id)
            ON DELETE CASCADE ON UPDATE CASCADE);"""

FILE_TABLES = ['images', 'videos', 'slides']

ADD_PATIENT = "INSERT INTO patients (uid) VALUES (?);"
ADD_VIDEO = "INSERT INTO videos (uid, filename) VALUES (?, ?);"
ADD_IMAGE = "INSERT INTO images (uid, filename) VALUES (?, ?);"
ADD_WSI = "INSERT INTO slides (uid, filename) VALUES (?, ?);"
ADD_ANNOTATION = ("INSERT INTO annotations "
                  "(annotation_id, frame_number, uid, filename, shape_type, flags, group_id, comment, label) "
                  "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);")
ADD_LABEL = "INSERT INTO labels (uid, label, filename) VALUES (?, ?, ?);"
ADD_POINTS = "INSERT INTO points (annotation_id, vertex_id, x, y) VALUES (?, ?, ?, ?);"

DELETE_FILE_ANNOTATIONS = "DELETE FROM annotations WHERE annotation_id = ?;"


class SQLiteDatabase(QObject):
    """class to control an SQL database. inherits a QObject to enable pyqt-signal transfer"""
    sUpdate = Signal(list, int, str, list, list, dict)
    sImportFile = Signal(list)
    sOpenSettings = Signal(list)
    sApplySettings = Signal(list)
    sPreviewDatabase = Signal(list, list)

    def __init__(self):
        super(SQLiteDatabase, self).__init__()
        self.connection = None
        self.cursor = None
        self.location = ""
        self.file_tables = FILE_TABLES
        self.is_initialized = False
        self.settings = None  # type: QSettings
        self.database_path = "none"

    def add_annotation(self, frame_number: int, uid: int, file: str, shape: dict, label: str):
        """ adds an entry to the annotation table using the parameter values"""
        with self.connection:
            self.cursor.execute(ADD_ANNOTATION, (frame_number, uid, file, shape, label))

    def add_file(self, filepath: str, uid: str):
        """
        adds a file to the database
        :param filepath: the name of the file to be added
        :param uid: a patient id which may be added to the database
        """
        with self.connection:

            # check if patient already exists, add if necessary
            p = self.cursor.execute("""SELECT uid FROM patients WHERE uid = ?""", (uid,)).fetchone()
            uid = p[0] if p else self.add_patient(uid)
            mod = modality(filepath)

            # copy to project location and add to database
            if mod == Modality.video:
                shutil.copy(filepath, self.location + Structure.VIDEOS_DIR)
                self.cursor.execute(ADD_VIDEO, (uid, os.path.basename(filepath)))
            elif mod == Modality.image:
                shutil.copy(filepath, self.location + Structure.IMAGES_DIR)
                self.cursor.execute(ADD_IMAGE, (uid, os.path.basename(filepath)))
            elif mod == Modality.slide:
                shutil.copy(filepath, self.location + Structure.SLIDES_DIR)
                self.cursor.execute(ADD_WSI, (uid, os.path.basename(filepath)))

    def add_label(self, uid: str, label: str, filename: str):
        """ add a new label class to database"""
        with self.connection:
            # make sure label does not already exist
            if self.cursor.execute("SELECT label FROM labels WHERE uid = ? AND filename = ?",
                                   (uid, filename)).fetchone():
                return
            self.cursor.execute(ADD_LABEL, (uid, label, filename))

    def add_patient(self, uid: str):
        """ add a new patient to database
        returns the uid of the new patient"""
        with self.connection:
            # make sure patient does not already exist
            if self.cursor.execute("SELECT uid FROM patients WHERE uid = ?", (uid,)).fetchone():
                return
            self.cursor.execute(ADD_PATIENT, (uid,))
            # TODO: Why is this step necessary? We can just return the uid
            result = self.cursor.execute("SELECT uid FROM patients WHERE uid = ?", (uid,)).fetchone()
        return result[0]

    def create_annotation_entry(self, filename: str, label_dict: dict, uid: str, frame_number: int = -1):
        """
        Creates an annotation entry dictionary.

        :param filename: The name of the file associated with the annotation.
        :type filename: str
        :param label_dict: The dictionary containing label information.
        :type label_dict: dict
        :param uid: The unique identifier for the patient.
        :type uid: str
        :param frame_number: The frame number associated with the annotation, defaults to -1.
        :type frame_number: int, optional
        :return: A dictionary representing the annotation entry.
        :rtype: dict
        """
        annotation_id = str(uuid.uuid4())
        annotation_entry = {'annotation_id': annotation_id,
                            'frame_number': frame_number,
                            'uid': uid,
                            'filename': filename,
                            'points': label_dict['points'],
                            'shape_type': label_dict['shape_type'],
                            'flags': label_dict['flags'],
                            'group_id': label_dict['group_id'],
                            'comment': label_dict['comment'],
                            'label': label_dict['label']
                            }

        return annotation_entry

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
            self.cursor.execute(CREATE_POINTS_TABLE)

    def delete_file(self, filename: str, cur_img_idx: int):
        """ this method deletes a file from the database and removes all corresponding annotations
        updates the gui afterwards while regarding the possible image switching"""
        deleted_idx = 0
        images = self.get_images()
        for i in range(len(images)):
            if images[i] == filename:
                deleted_idx = i
        if cur_img_idx == 0:
            new_img_idx = 0
        elif deleted_idx <= cur_img_idx:
            new_img_idx = cur_img_idx - 1
        else:
            new_img_idx = cur_img_idx

        modality, file = self.get_uids_from_filename(filename)
        table_name = self.file_tables[modality]
        with self.connection:
            self.cursor.execute(DELETE_FILE_ANNOTATIONS, (modality, file))
            self.cursor.execute("DELETE FROM {} WHERE filename = ?".format(table_name), (filename,))
        self.update_gui(new_img_idx)

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
            images = self.cursor.execute("SELECT uid, filename FROM images").fetchall()
        return [(image[0], image[1]) for image in images]

    def get_videos(self) -> list:
        """ returns a list of all video names which are currently stored in the database"""
        with self.connection:
            videos = self.cursor.execute("SELECT uid, filename FROM videos").fetchall()
        return [(video[0], video[1]) for video in videos]

    def get_slides(self) -> list:
        """ returns a list of all wsi names which are currently stored in the database"""
        with self.connection:
            wsis = self.cursor.execute("SELECT uid, filename FROM slides").fetchall()
        return [(wsi[0], wsi[1]) for wsi in wsis]

    def get_all_labels(self) -> list:
        """
        :return: a list of all label classes which are currently stored in the database
        """
        with self.connection:
            label_classes = self.cursor.execute("SELECT label FROM labels").fetchall()
        return [label_class[0] for label_class in label_classes]

    def get_labels_for_file(self, uid, file):
        """
        :param image: the image name to be searched in
        :return: a list of all label shapes related to the specified image
        """
        with self.connection:
            labels = self.cursor.execute("""SELECT label FROM labels
                                            WHERE uid = ? AND filename = ?""", (uid, file)).fetchall()

        return check_for_bytes(labels)

    def get_patients(self):
        """returns all patient uids"""
        with self.connection:
            result = self.cursor.execute("SELECT uid FROM patients").fetchall()
        return [res[0] for res in result]

    # def get_patient_by_filename(self, filename: str, moda: int):
    #     """returns the corresponding patient uid of an image"""
    #     if moda == Modality.image:
    #         with self.connection:
    #             self.cursor.execute("SELECT uid FROM images WHERE filename = ?", (filename,))
    #             return self.cursor.fetchone()[0]
    #     elif moda == Modality.video:
    #         with self.connection:
    #             self.cursor.execute("SELECT uid FROM videos WHERE filename = ?", (filename,))
    #             return self.cursor.fetchone()[0]
    #     elif moda == Modality.slide:
    #         with self.connection:
    #             self.cursor.execute("SELECT uid FROM slides WHERE filename = ?", (filename,))
    #             return self.cursor.fetchone()[0]

    # TODO: This is deprecated
    # def get_patient_by_uid(self, patient_uid: int):
    #     """returns the id/patient info from the patients table by the corresponding uid"""
    #     self.cursor.execute("SELECT some_id FROM patients WHERE uid = ?", (patient_uid,))
    #     return self.cursor.fetchone()[0]

    def get_settings(self):
        """retrieves the values stored in the settings file"""
        settings = list()
        for key in self.settings.allKeys():
            value = self.settings.value(key)
            tooltip = get_tooltip(key)
            settings.append((key, value, tooltip))
        return settings

    # def get_uid_from_filename(self, table_name: str, filename: str) -> int:
    #     """
    #     :param table_name: videos, images, or whole slide images
    #     :param filename: name of the file
    #     :return: the uid which is related to the specified file
    #     """
    #     with self.connection:
    #         query = f"SELECT uid FROM {table_name} WHERE filename = ?"
    #         self.cursor.execute(query, (filename,))
    #         result = self.cursor.fetchone()
    #     return result[0] if result is not None else None

    # def get_uids_from_filename(self, filename: str) -> tuple:
    #     """
    #     :param filename: name of the file
    #     :return: a tuple holding: modality uid (video/image/whole slide image) and file uid
    #     """
    #     modality, file = None, None
    #     for i, table_name in enumerate(self.file_tables):
    #         file = self.get_uid_from_filename(table_name, filename)
    #         if file is not None:
    #             modality = i
    #             break
    #     return modality, file

    # def get_uid_from_label(self, label: str) -> int:
    #     """
    #     :param label: the label class to get the uid from
    #     :return: the uid of the label class if existing
    #     """
    #     with self.connection:
    #         self.cursor.execute("""SELECT uid FROM labels WHERE label_class = ?""", (label,))
    #         result = self.cursor.fetchone()
    #     return result[0] if result is not None else None

    def initialize(self, database_path: str, files: dict = None):
        """
        Connect to database as initialization
        :param database_path: path to the database
        :param files: initially added files in case of newly created project
        """
        self.location = str(pathlib.Path(database_path).parents[0])
        # indicates a new project - set up project environment
        if files is not None:
            create_project_structure(self.location)

        self.connection = sqlite3.connect(database_path)
        self.database_path = database_path
        self.cursor = self.connection.cursor()

        # indicates a new project - add initial files
        if files is not None:
            self.create_initial_tables()
            for file, patient in files.items():
                self.add_file(file, patient)
            self.settings = QSettings(self.location + '/settings', QSettings.Format.NativeFormat)
            self.update_settings(SETTINGS)
        else:
            self.settings = QSettings(self.location + '/settings', QSettings.Format.NativeFormat)

        with self.connection:
            self.cursor.execute(f"PRAGMA foreign_keys = ON;")

        self.is_initialized = True
        self.update_gui()
        settings = self.get_settings()
        self.sApplySettings.emit(settings)

    def open_settings(self):
        """emits a signal to open the settings dialog"""
        settings = self.get_settings()
        self.sOpenSettings.emit(settings)

    def prepare_files(self, files_uid: list, moda: dict) -> list:
        """goes through all filenames and returns them as full paths,
        in a tuple together with a boolean indicating whether there is at least 1 annotation in the image"""
        result = list()
        for file_uid in files_uid:
            labels = self.get_labels_for_file(file_uid[0], file_uid[1])
            populated = True if labels else False
            if moda[file_uid[1]] == Modality.image:
                file = self.location + Structure.IMAGES_DIR + file_uid[1]
            elif moda[file_uid[1]] == Modality.video:
                file = self.location + Structure.VIDEOS_DIR + file_uid[1]
            else:
                file = self.location + Structure.SLIDES_DIR + file_uid[1]
            result.append((file, populated))
        return result

    def preview_database(self, table_name: str):
        """collects all information from the specified table and emits a signal"""
        with self.connection:
            headers = self.cursor.execute("PRAGMA table_info({})".format(table_name)).fetchall()
            headers = [header[1] for header in headers]
            content = self.cursor.execute("SELECT * FROM {}".format(table_name)).fetchall()
        self.sPreviewDatabase.emit(headers, content)

    def save(self, current_labels: list, img_idx: int):
        files_uid = self.get_images()
        files_uid += self.get_videos()
        files_uid += self.get_slides()
        if files_uid:
            file = files_uid[img_idx]
            entries = list()
            for lbl in current_labels:
                label_dict, label = lbl.to_dict()
                self.add_label(file[0], label, file[1])
                entries.append(self.create_annotation_entry(file[1], label_dict, file[0]))
            self.update_image_annotations(entries=entries)

    def send_import_info(self):
        existing_patients = self.get_patients()
        self.sImportFile.emit(existing_patients)

    def update_image_annotations(self, entries: list):
        """
        updates the annotations associated with a given image
        :param image_name: the image to be updated
        :param entries: list of dictionaries representing the annotation entries
        """
        with self.connection:
            # add new, updated list of annotations
            self.cursor.execute("PRAGMA foreign_keys = ON;")
            for entry in entries:
                if not self.cursor.execute("""SELECT annotation_id FROM annotations WHERE annotation_id = ?""",
                                           (entry['annotation_id'],)).fetchone():
                    self.cursor.execute(ADD_ANNOTATION, (entry['annotation_id'], entry['frame_number'], entry['uid'],
                                                         entry['filename'], entry['shape_type'],
                                                         entry['flags'], entry['group_id'], entry['comment'],
                                                         entry['label']))
                    [self.cursor.execute(ADD_POINTS, (entry['annotation_id'], i, point[0], point[1])) for i, point
                     in enumerate(entry['points']) if not
                     self.cursor.execute("""SELECT x, y FROM points WHERE annotation_id = ? AND x = ? AND y = ?""",
                                         (entry['annotation_id'], point[0], point[1])).fetchone()]

    def update_gui(self, img_idx: int = 0):
        """gathers all information about the project and updates the database"""
        images_uid = self.get_images()
        videos_uid = self.get_videos()
        slides_uid = self.get_slides()

        moda = {image[1]: Modality.image for image in images_uid}
        moda.update({video[1]: Modality.video for video in videos_uid})
        moda.update({slide[1]: Modality.slide for slide in slides_uid})

        files_uid = images_uid
        files_uid.extend(videos_uid)
        files_uid.extend(slides_uid)

        if files_uid:
            file = files_uid[img_idx]
            labels = self.get_labels_for_file(file[0], file[1])
            # TODO: Make this work for videos
            annotations = self.cursor.execute("SELECT annotation_id, shape_type, flags, group_id, comment, label FROM "
                                              "annotations WHERE uid = ? AND filename = ?",
                                              (file[0], file[1])).fetchall()

            annotation_ids = [annotation[0] for annotation in annotations]

            annotations_dict = {
                annotation[0]: {
                    'shape_type': annotation[1],
                    'flags': annotation[2],
                    'group_id': annotation[3],
                    'comment': annotation[4],
                    'label': annotation[5]
                }
                for annotation in annotations
            }

            for annotation_id in annotation_ids:
                points = self.cursor.execute("SELECT vertex_id, x, y FROM points WHERE annotation_id = ?",
                                             (annotation_id,)).fetchall()
                annotations_dict[annotation_id]['points'] = sorted(points)

            patient = file[0]
        else:
            labels, patient, annotation_ids, annotations_dict = [], "", [], {}

        files = self.prepare_files(files_uid, moda)
        classes = self.get_all_labels()
        self.sUpdate.emit(files, img_idx, patient, classes, annotation_ids, annotations_dict)

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

    def update_settings(self, settings: list):
        """saves the specified settings in the QSettings file"""
        for setting in settings:
            self.settings.setValue(setting[0], setting[1])


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
