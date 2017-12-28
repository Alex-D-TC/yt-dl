from utils.functional import Error
import re
import urllib
import utils.string as string
import utils.logging as logging
import utils.files as files
import js2py
import postprocess.transforms as transforms
import tempfile


def extract_download(yt_id, dest, in_codec_type, extra_known_meta=None):
    data = files.download_web_content("https://www.youtube.com/watch?v={}".format(yt_id))
    return _extract_data(data, dest, in_codec_type, extra_known_meta)


def _extract_data(html, dest, in_codec_type, extra_known_meta=None):

    tmp_path = tempfile.gettempdir() + "/tmp-yt-dl.mp4"

    e = _get_extract_data_base_flow(html, in_codec_type)
    e.process(lambda x: files.download(x, tmp_path))\
        .error(print)

    vid_meta = _extract_metadata(html)

    if not e.err_state:
        return transforms.convert_file_to_mp3(tmp_path,
                                              {} if extra_known_meta is None else extra_known_meta,
                                              dest,
                                              vid_meta["title"])

    return ""


def _extract_metadata(html):
    extra_meta = {}

    # get video title
    title_loc_pat = "\"title\":\""
    found_vid_title_start = string.boyer_moore_horspool(html, title_loc_pat, 0, 1)[0] + len(title_loc_pat)
    found_vid_title_end = found_vid_title_start
    while html[found_vid_title_end] != "\"":
        found_vid_title_end += 1

    extra_meta["title"] = html[found_vid_title_start:found_vid_title_end]

    return extra_meta


def _get_extract_data_base_flow(html, codec_type):
    m = Error(html) \
        .process(_get_raw_url_encoded_data) \
        .process(_log_html) \
        .process(_parse_url_encoded_data) \
        .process(_log_url_encoded) \
        .process(lambda x: [x, lambda y: _extract_decryptor(html)(y), codec_type]) \
        .process(lambda x: _prepare_link(*x)) \
        .process(_decode_url) \
        .process(logging.log_ret)
    return m


def _get_raw_url_encoded_data(data):
    pat = "\"url_encoded_fmt_stream_map\":"
    pat_end = "\""
    found_url = string.boyer_moore_horspool(data, pat)
    found_end_url = string.boyer_moore_horspool(data, pat_end, found_url[0] + len(pat) + 1)
    start_idx = found_url[0] + len(pat) + 1
    end_idx = found_end_url[0]

    return data[start_idx:end_idx]


def _parse_url_encoded_data(raw_url_encoded):

    buff_split = raw_url_encoded.split(",")

    meta_data = dict()
    meta_data["urls"] = []

    url_re = re.compile(r'(url=|itag=|quality=|type=|s=).*')

    for s in buff_split:
        if s[-1] == "\n":
            s = s[:-1]

        if len(s) == 0:
            continue

        s_split = s.split(r"\u0026")

        # if it starts with itag, place in urls, else place in the top
        if url_re.match(s_split[0]):
            url_data = {}
            for token in s_split:
                if len(token) == 0:
                    continue
                token_split = token.split("=")
                url_data[token_split[0]] = urllib.parse.unquote(token_split[1])
            meta_data["urls"].append(url_data)
        else:
            for token in s_split:
                if len(token) == 0:
                    continue
                token_split = token.split("=")
                meta_data[token_split[0]] = urllib.parse.unquote(token_split[1])

    return meta_data


def _decode_url(url):
    return urllib.parse.unquote(url)


def _prepare_link(url_encoded_data, decryption_func, codec_type):

    url = ""
    url_s = None

    for url_data in url_encoded_data["urls"]:

        found_s = "s" in url_data

        if "type" in url_data and url_data["type"] == codec_type:
            url = url_data["url"]
            if found_s:
                url_s = url_data["s"]
            else:
                url_s = None

    if url_s is not None:
        decrypted = decryption_func(url_s)
        url = url + "&signature={0}".format(decrypted)

    return url


def _get_jsplayer_url(data):
    pat = "player/base"
    found = string.boyer_moore_horspool(data, pat)
    pat = "<script"
    found = string.boyer_moore_horspool(data, pat, found[0] - 200, 1)
    pat = "src="
    found_start = string.boyer_moore_horspool(data, pat, found[0], 1)
    pat = "\""
    found_end = string.boyer_moore_horspool(data, pat, found_start[0] + 5, 1)

    return "https://www.youtube.com{0}".format(data[found_start[0]+5:found_end[0]])


def _extract_decryptor(data):

    jsplayer_id = files.strip_invalid_chars(_get_jsplayer_url(data).replace("/", "-"))

    js_cache_root = "./res/serv_cache/jsplayer"
    js_path = files.get_from_cache(jsplayer_id, js_cache_root)

    if len(js_path) != 0:
        data = files.read_file(js_path)
        func_id = data[0][:-1]
        js_code = "".join(data[1:])
        return lambda x: js2py.eval_js(js_code + "{}(\"{}\")".format(func_id, x))

    data_js = files.download_web_content(_get_jsplayer_url(data))

    sig_pat = ".set(\"signature\","
    sig_locations = string.boyer_moore_horspool(data_js, sig_pat)
    func_name = None
    for s_loc in sig_locations:
        s_loc += len(sig_pat)

        if func_name is not None:
            continue

        if data_js[s_loc:s_loc+2][-1] != ".":
            # found it
            func_name_end = string.boyer_moore_horspool(data_js, "(", s_loc, 1)
            func_name = data_js[s_loc:func_name_end[0]]

    # return decrypter
    code = _relevant_code_of_identifier(func_name, data_js)

    # save code
    files.save_file("{}\n{}".format(func_name, code), js_cache_root + "/{}/base.js".format(jsplayer_id))

    return lambda x: js2py.eval_js(code + "{}(\"{}\")".format(func_name, x))


def _get_code_blocks_for_func(func_root, in_code):

    code_segments = []
    id_re = re.compile(r';?\s*(%s\s*=|function %s\()' % (func_root, func_root))

    found = id_re.search(in_code)

    # get function start idx
    start_idx = found.span()[0]
    while not in_code[start_idx].isalpha():
        start_idx += 1

    # get the end of the code segment
    end_idx = string.get_end_of_code_sequence(in_code, start_idx)

    code_segments.append((start_idx, end_idx))

    # get the object id which holds all the functions used by the 'decrypter'
    obj_id_pat = ".split(\"\");"
    found = string.boyer_moore_horspool(in_code, obj_id_pat, start_idx, 1)
    start_idx = found[0] + len(obj_id_pat)
    end_idx = start_idx
    while in_code[end_idx].isalpha():
        end_idx += 1
    obj_id = in_code[start_idx:end_idx]

    # get the code defining the object
    found = re.search(r';?\s*%s=' % obj_id, in_code)
    start_idx = found.span()[0]
    while not in_code[start_idx].isalpha():
        start_idx += 1

    end_idx = string.get_end_of_code_sequence(in_code, start_idx)

    code_segments.append((start_idx, end_idx))
    code_segments.reverse()

    # return the locations of the code segment for the 'decrypter' function and the object it depends on
    return code_segments


def _relevant_code_of_identifier(id_name, in_code):
    # pretty print the resulting code blocks for usage with a javrascript interpreter
    return ";".join(list(map(lambda x: in_code[x[0]:x[1]], _get_code_blocks_for_func(id_name, in_code)))) + ";"


def _log_url_encoded(url_encoded_data):
    logging.log_meta("./res/meta_url", str(url_encoded_data))
    return url_encoded_data


def _log_html(html):
    logging.log_meta("./res/meta_html", html)
    return html
