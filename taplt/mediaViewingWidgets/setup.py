from setuptools import setup


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="media-viewing-widgets",
    version="0.0.1",
    author="",
    author_email="",
    description="A pyqt widget library for viewing various media formats",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/daniel89-code/media-viewing-widgets",
    packages=['media_viewing_widgets'],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU GENERAL PUBLIC LICENSE",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3',
    install_requires=['numpy',
                      'PyQt6',
                      'openslide-python']
)
