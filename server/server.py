import http.server as server
import utils.files as files
import youtube.download as yt_download
import urllib
import os


def start_serv(port):
    server_address = ("", port)
    http_serv = server.HTTPServer(server_address, RequestHandler)
    print("Bound on port {}".format(port))
    http_serv.serve_forever()


class RequestHandler(server.SimpleHTTPRequestHandler):
    def do_GET(self):
        qs_data = parse_qs(self.path)
        print(qs_data)

        if "v" in qs_data:
            cache_root = os.path.abspath("serv_cache/vid").replace("\\", "/")
            cache_path = cache_root + "/{}".format(qs_data["v"])

            try:
                # small quality mp4: video/3gpp;+codecs=\"mp4v.20.3,+mp4a.40.2\"
                # medium quality mp4: video/mp4;+codecs=\"avc1.42001E,+mp4a.40.2\"

                res_path = files.get_from_cache(qs_data["v"], cache_root)
                if len(res_path) == 0:
                    os.mkdir(cache_path)
                    res_path = yt_download.extract_download(
                        qs_data["v"], cache_path, "video/mp4;+codecs=\"avc1.42001E,+mp4a.40.2\"", {})

            except BaseException as e:
                print(e.args)
                res_path = ""

            if len(res_path) != 0:
                print(res_path)

                filename_end = len(res_path)
                filename_start = filename_end - 1
                while filename_start > 0 and res_path[filename_start - 1] != "/":
                    filename_start -= 1

                self.write_headers(200,
                                   [
                                       ("Content-Type", "application/octet-stream"),
                                       ("Content-Disposition", "attachment; filename=\"" + res_path[filename_start:filename_end] +"\"")
                                   ])

                with open(res_path, "rb") as file:
                    file_data = file.read()
                    self.wfile.write(file_data)

            else:
                self.write_headers(500, [])
                self.wfile.write("An error occurred".encode("iso-8859-15"))

        else:
            self.write_headers(500, [])

    def write_headers(self, resp_code, headers):
        self.send_response(resp_code)
        for header in headers:
            self.send_header(header[0], header[1])
        self.end_headers()


def parse_qs(path):
    path = path[2:].split("&")
    kv = {}
    for token in path:
        token_split = token.split("=")
        kv[urllib.parse.unquote(token_split[0])] = urllib.parse.unquote(token_split[1])

    return kv
