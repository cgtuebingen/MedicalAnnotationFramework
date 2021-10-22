import os
from database import SQLiteDatabase
import ffmpeg
from seg_utils.utils.video_sampling import get_duration


def mpg_to_mp4(base_dir: str = "/home/nico/isys/data",
               source_dir: str = "/home/nico/isys/data/source",
               output_folder: str = "converted",
               database_name: str = "database.db",
               quiet: bool = False):
    """ Convert videos in mpg format to mp4

        :param str base_dir: filepath of the base folder where everything starts from
        :param str source_dir: source directory name
        :param str output_folder: folder name of the output folder in the base dir
        :param str database_name: name of the database file with extension
        :param bool quiet: if the frame contains a tumour
        """
    db = SQLiteDatabase(os.path.join(base_dir, database_name))
    db.create_videos_table()
    for element in sorted(os.listdir(source_dir)):
        counter = db.get_num_entries("videos")  # call here necessary for the recursion
        elem_path = os.path.join(source_dir, element)
        if os.path.isfile(elem_path):
            # check if it is not already included
            extensions = [".mpg", ".mp4"]
            if any(ext == os.path.splitext(element)[1] for ext in extensions):
                # string format for at least 9999 videos
                conv_filename = f"{output_folder}/video{counter+1:04d}.mp4"
                origin = source_dir.replace(base_dir+'/', '') + f"/{element}"

                # this is only a dummy value as conversion influences with durations due to adding and deleting frames
                duration = 1
                out_file = os.path.join(base_dir, conv_filename)
                # checks if video exists already so it returns False if it does since the add didnt work
                # prevents overwrite
                if db.add_video(origin, conv_filename, duration):
                    ffmpeg.input(elem_path).output(out_file).run(quiet=quiet)
                    # conversion to mp4 from mpg changes some frame timings. As i only reside on the mp4 versions,
                    # i need to update the value again in the database
                    db.update_entry('videos', "origin", origin, "duration", get_duration(out_file) * 1000.0)

            else:
                continue

        elif os.path.isdir(elem_path):
            mpg_to_mp4(source_dir=elem_path)
        else:
            pass


if __name__ == "__main__":
    mpg_to_mp4()
