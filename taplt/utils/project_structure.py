import os
import shutil
import enum

SLIDE_EXTENSIONS = ['tif', 'svs', 'ndpi', '.vms', '.vmu', '.scn', '.mrxs', '.tiff', '.svslide', '.bif']

class Modality(enum.IntEnum):
    video = 0
    image = 1
    slide = 2


class Structure:
    IMAGES_DIR = "/data/images/"
    VIDEOS_DIR = "/data/videos/"
    SLIDES_DIR = "/data/slides/"
    FILE_DIRS = [IMAGES_DIR, VIDEOS_DIR, SLIDES_DIR]
    DATABASE_DEFAULT_NAME = '/database.db'


def check_environment(project_path: str) -> bool:
    """This function checks for a given path whether it is a valid project location,
    i.e. whether it contains a 'data' folder with videos, images and whole slide images"""
    for file_dir in Structure.FILE_DIRS:
        if not os.path.exists(project_path + file_dir):
            return False
    return True


def create_project_structure(project_path: str):
    """This method takes the user-specified project location and
     (1) creates the necessary directories for the project
     (2) calls the Database class to create an empty database with the desired structure"""
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
    os.makedirs(project_path)
    for file_dir in Structure.FILE_DIRS:
        os.makedirs(project_path + file_dir)


def modality(filepath: str) -> Modality:
    """This method uses the 'filetype' library to detect the type of the given file
    returns: 'video', 'image' or 'slide'"""
    if filepath.endswith('mp4'):
        return Modality.video
    if filepath.endswith('jpg') or filepath.endswith('png'):
        return Modality.image
    if any(filepath.endswith(ext) for ext in SLIDE_EXTENSIONS):
        return Modality.slide
    raise Exception("This filetype is not supported")
