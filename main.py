import youtube.download as yt_download
import argparse
import server.server as server
import utils.files as files

# obtain video metadata
# http://youtube.com/get_video_info?video_id=sRvtSH1_H0w
# convert using ffmpeg: ffmpeg -i "input.extension" -codec:a libmp3lame "output.mp3"
# convert usinf ffmpeg:
# ffmpeg -i "input.extension" -metadata title="title" -metadata author="artist" -metadata album="album" -codec:a libmp3lame "output.mp3"

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Process some integers.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-yt_id', type=str,
                       help='The id of the youtube video')
    parser.add_argument('-out_path', type=str,
                        help='Folder where to store the result',
                        default=".")
    group.add_argument('-serv_bind',
                       type=int,
                       help='Specify the port to which the bind the server on, if you wish to use the utility as a server')

    args = parser.parse_args()

    if args.serv_bind is not None:
        server.start_serv(args.serv_bind)
    else:

        yt_id = args.yt_id
        res_path = args.out_path
        codec_type = "video/mp4;+codecs=\"avc1.42001E,+mp4a.40.2\""
        extra_known_meta = {}
        yt_download.extract_download(yt_id, res_path, codec_type, extra_known_meta)
