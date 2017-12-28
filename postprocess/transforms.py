import subprocess
import utils.files as files


def convert_file_to_mp3(file_path, extra_meta, result_path, result_filename=None):

    if result_filename is None and "author" in extra_meta and "title" in extra_meta:
        result_filename = "{} - {}".format(extra_meta["title"], extra_meta["author"])

    if result_filename is not None:
        result_filename = files.strip_invalid_chars(result_filename)\
            .encode("utf-8")\
            .decode('unicode-escape')

    args = ["-i {}".format(file_path),
            "-metadata title=\"{}\"".format(extra_meta["title"] if "title" in extra_meta else ""),
            "-metadata author=\"{}\"".format(extra_meta["author"] if "author" in extra_meta else ""),
            "-metadata album=\"{}\"".format(extra_meta["album"] if "album" in extra_meta else ""),
            "-codec:a libmp3lame",
            "\"{}.mp3\"".format(result_path + "/{}".format("result" if result_filename is None else result_filename))]

    # ffmpeg -i "input.extension"
    #   -metadata title="title" -metadata author="artist" -metadata album="album" -codec:a libmp3lame "output.mp3"
    subprocess.call("ffmpeg " + " ".join(args))

    return "{}/{}.mp3".format(result_path, result_filename)
