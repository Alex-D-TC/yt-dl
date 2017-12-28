from utils.files import save_file


def log_ret(link):
    print(link)
    return link


def log_meta(log_meta_dir, data):
    meta_idx = 0
    with open(log_meta_dir + "/meta") as file:
        meta_idx = int(file.readline())

    save_file(data, log_meta_dir + "/meta_{0}".format(meta_idx))
    save_file(str(meta_idx + 1), log_meta_dir + "/meta")
    return data
