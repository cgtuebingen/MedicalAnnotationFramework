## Description
Segmentation Utility intended for segmenting medical images with ease. The application is based on 
[PyQT 5.15](https://doc.qt.io/qtforpython/ "PyQT documentation") 
and contains two windows, where the user can pick from:

1. `ui.selection_ui` shows the segmentation annotations already made side by side with a notes field to
track changes and give alteration options
   
2. `ui.label_ui` is a UI inspired by 
   [labelme](https://github.com/wkentaro/labelme "Labelme Github") with improved functionality.
This includes performance fixes, an altered structure and more readable code. Additionally, the drawing of shapes
is refined as well as the saving. This includes saving into an SQL database.

Both files are called by their respective main function, which connects the UI elements with real functionality 
(`src.label_main`, `src.viewer_main`). Alternatively, the `src.selection_main` can be called, which opens a dialog
where one can pick between the aforementioned main GUI.

## Functionality
### Implemented Features
- tight SQL integration
- efficient labeling with polygon, rectangle, circle and outline tracking
- adapted context menu

### To-Do and requested features
- export options for COCO/VOC Segmentation 
- undo/redo buttons to revert to previous states

## Requirements
- Ubuntu / macOS / Windows
- Python3
- [PyQt5](https://doc.qt.io/qtforpython/)

## Installation

### Anaconda (Python 3.8)
```bash
conda create --name=<your_env_name> python=3.8
conda activate <your_env_name>
pip install pyqt5  # pyqt5 can be installed via pip on python3
pip install seg_utils
```
#### Note for Linux Users
The repository requires both `PyQt5` and `opencv-python`. There might be a conflict within the base version of `PyQt5`
and its binaries that ship with Linux leading to the following error
```bash
QObject::moveToThread: Current thread (0x557c88f2ec90) is not the object's thread (0x557c8970c830).
Cannot move to target thread (0x557c88f2ec90)
```

This can be fixed by building `opencv-python` from source as described [here](https://stackoverflow.com/questions/52337870/python-opencv-error-current-thread-is-not-the-objects-thread)
```bash
conda activate <your_env_name>
pip install --no-binary opencv-python opencv-python
```

## Know Issues
### Database
Make sure, your database is composed similarly to the one specified in `utils.database` specified in the following in 
shortened notation:
```python
# 'videos' table with the original (relative) video path, the (relative) path of the converted vide 
# and the duration in ms of the video
""" video_id INTEGER, origin_path TEXT, conv_path TEXT, duration"""


# 'images' table with the (relative) video path of the extracted image, the (relative) path of the extracted image,
# and the frame number of said image
""" image_id INTEGER, video_path TEXT, image_path TEXT, frame_num INTEGER"""


# 'labels' table with the (relative) image path, a binary object containing all labels as a list of dicts and N classes
# of respective labels, i.e. class_tumour
""" label_id INTEGER, image_path TEXT, label_list"""
```

### Folder Structure
Make sure your folder structure is similar to following as the database is dependent on the labeled output folders, 
which are set manually. Therefore, have at least the folder `SegmentationClassVisualization` 
directly underneath the database:

```bash
│ database.db
├── converted
│   ├── video_0001.mp4
│   │         .
│   │         .
│   │         .
│   ├── video_XXXX.mp4
├── images
│   ├── video_0001_0001.png
│   │         .
│   │         .
│   │         .
│   ├── video_XXXX_XXXX.png
├── labels
│   ├── class_names.txt
│   ├── PNGImages
│   │   ├── video0001_0001.png
│   │   │       .
│   │   │       .
│   │   │       . 
│   │   ├── video_XXXX_XXXX.png
│   ├── SegmentationClassVisualization
│   │   ├── video0001_0001.png
│   │   │       .
│   │   │       .
│   │   │       . 
│   │   ├── video_XXXX_XXXX.png
```



## Development
### Building standalone application
```bash
# navigate to the base folder seg_utils containing setup.py
pip install .
pip install pyinstaller
pyinstaller labelme.spec
```
This creates a folder `dist`, where an executable can be found.


### Working with UI Files (deprecated)
```bash
# conda environment needs to be active otherwise there will not be a pyuic5 command
pyuic5 --from-imports=<Package_Name> -x <UI_File>.ui -o <UI_File>.py  # specifiy the name given by <UI_File>
# and the import statement <Package_Name> as one would in Python with the full path to the package 
# e.g. seg_utils.src
pyrcc5 <Resource_File>.qrc -o <Resource_File>_rc.py
```


## Acknowledgement

This repo is inspired by [labelme](https://github.com/wkentaro/labelme "Labelme Github").
