import re
import sys
from setuptools import find_packages
from setuptools import setup
import distutils.spawn
import subprocess


def get_version():
    filename = "seg_utils/__init__.py"
    with open(filename) as f:
        match = re.search(
            r"""^__version__ = ['"]([^'"]*)['"]""", f.read(), re.M
        )
    if not match:
        raise RuntimeError("{} doesn't contain __version__".format(filename))
    version = match.groups()[0]
    return version


def get_long_description():
    with open("README.md") as f:
        long_description = f.read()
    """
    try:
        import github2pypi

        return github2pypi.replace_url(
            slug="nicoloesch/segmentation_utils", content=long_description
        )
    except Exception:
    """
    return long_description


def get_install_requires():
    PY3 = sys.version_info[0] == 3
    assert PY3

    install_requires = [
        "imgviz>=0.11.0",
        "matplotlib<3.3",  # for PyInstaller
        "numpy",
        "Pillow>=2.8.0",
        "PyYAML",
        "qtpy",
        "termcolor",
        "PyQT5",
        "opencv-python",
        "imgviz"
    ]

    """
    # Find python binding for qt with priority:
    # PyQt5 -> PySide2 -> PyQt4,
    # and PyQt5 is automatically installed on Python3.
    QT_BINDING = None

    try:
        import PyQt5  # NOQA

        QT_BINDING = "pyqt5"
    except ImportError:
        pass

    if QT_BINDING is None:
        try:
            import PySide2  # NOQA

            QT_BINDING = "pyside2"
        except ImportError:
            pass

    if QT_BINDING is None:
        print("Please install PyQt5 for python 3\n",
              file=sys.stderr)
        sys.exit(1)
        assert PY3
            # PyQt5 can be installed via pip for Python3
            install_requires.append("PyQt5")
            QT_BINDING = "pyqt5"
    del QT_BINDING

    if os.name == "nt":  # Windows
        install_requires.append("colorama")
    """
    return install_requires


def main():
    version = get_version()

    """
    if sys.argv[1] == "release":
        if not distutils.spawn.find_executable("twine"):
            print(
                "Please install twine:\n\n\tpip install twine\n",
                file=sys.stderr,
            )
            sys.exit(1)

        commands = [
            "python tests/docs_tests/man_tests/test_labelme_1.py",
            "git tag v{:s}".format(version),
            "git push origin master --tag",
            "python setup.py sdist",
            "twine upload dist/labelme-{:s}.tar.gz".format(version),
        ]
        for cmd in commands:
            subprocess.check_call(shlex.split(cmd))
        sys.exit(0)
    """
    setup(
        name="seg_utils",
        version="0.0.1-dev",
        packages=find_packages(exclude=["github2pypi"]),
        description="Semantic Segmentation Tool for medical applications",
        long_description=get_long_description(),
        long_description_content_type="text/markdown",
        author="Nico Lösch",
        author_email="nico.loesch95@gmail.com",
        url="https://github.com/nicoloesch/segmentation_utils",
        install_requires=get_install_requires(),
        license="GPLv3",
        keywords="Image Annotation, Machine Learning",
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "Natural Language :: English",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: Implementation :: CPython",
            "Programming Language :: Python :: Implementation :: PyPy",
        ],
        package_data={"seg_utils": ["resource/icons/*", "config/*.yaml"]},
        entry_points={
            "console_scripts": [
                "seg-utils=seg_utils.main:main", ],
        })


if __name__ == "__main__":
    main()
