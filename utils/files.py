import pycurl
import certifi
import os
from io import BytesIO


def save_file(data, path):

    path = strip_invalid_chars(path)

    # create folder if not existing
    path_folder_end = len(path) - 1

    while path_folder_end > 0 and path[path_folder_end] != "/":
        path_folder_end -= 1

    path_folder = "." if path_folder_end == 0 else path[0:path_folder_end]

    if not path_exists(path_folder):
        os.mkdir(path_folder)

    with open(path, "w") as file:
        file.write(data)


def read_file(path):
    with open(path, "r") as file:
        result = file.readlines()
    return result


def download(link, download_path):

    print("Downloading")

    with open(download_path, "wb") as file:
        c = pycurl.Curl()
        c.setopt(pycurl.URL, link)
        c.setopt(pycurl.CAINFO, certifi.where())
        c.setopt(pycurl.WRITEFUNCTION, file.write)
        c.setopt(pycurl.FOLLOWLOCATION, 1)

        c.perform()

        resp_code = c.getinfo(pycurl.RESPONSE_CODE)
        if resp_code < 200 or resp_code > 299:
            raise ConnectionError("Error. Response code is: {}".format(resp_code))


def download_web_content(link):
    buff = download_bytes(link)
    print("Decoding results using the {} format".format("iso-8859-1"))
    return buff.getvalue().decode("iso-8859-1")


def download_bytes(link):
    buff = BytesIO()

    c = pycurl.Curl()
    c.setopt(pycurl.URL, link)
    c.setopt(pycurl.CAINFO, certifi.where())
    c.setopt(pycurl.WRITEDATA, buff)
    c.setopt(pycurl.FOLLOWLOCATION, 1)

    c.perform()

    resp_code = c.getinfo(pycurl.RESPONSE_CODE)
    if resp_code < 200 or resp_code > 299:
        raise ConnectionError("Error on download_bytes for argument {}. Response code is: {}".format(link, resp_code))

    return buff


def remote_stream(link, stream_callback):
    c = pycurl.Curl()
    c.setopt(pycurl.URL, link)
    c.setopt(pycurl.WRITEFUNCTION, stream_callback)
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.perform()

    resp_code = c.getinfo(pycurl.RESPONSE_CODE)
    if resp_code < 200 or resp_code > 299:
        raise ConnectionError("Error. Response code is: {}".format(resp_code))


def get_from_cache(id, cache_root):

    cache_path = cache_root + "/{}".format(id)
    if path_exists(cache_path):
        return cache_path + "/" + os.listdir(cache_path)[0]
    return ""


def path_exists(path):
    exists = False
    try:
        os.stat(path)
        exists = True
    except FileNotFoundError:
        pass
    return exists


def strip_invalid_chars(path):
    return path.translate(str.maketrans("~#%&*{}:<>?+|", " " * 13))
