import argparse
import os
import queue
import sys

import pafy
import vlc
from googleapiclient.discovery import build

from helpers.loader import DEVELOPER_KEY

DEVELOPER_KEY = 'AIzaSyAjDg9c8VOQiUdTlmmT3zKkGPvjR9i1e4c'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

VIDEO_QUEUE = queue.Queue()
COMMAND_QUEUE = queue.Queue()

instance = vlc.Instance()
player = instance.media_player_new()


def play(video):
    best = video.getbest()
    playurl = best.url
    media = instance.media_new(playurl)
    media.get_mrl()
    player.set_media(media)
    player.play()
    return video.length


def pafy_video(video_id):
    url = 'https://www.youtube.com/watch?v={0}'.format(video_id)
    vid = pafy.new(url)


def pafy_playlist(playlist_id):
    url = "https://www.youtube.com/playlist?list={0}".format(playlist_id)
    return pafy.get_playlist(url)


def youtube_add_video(query):
    parser = argparse.ArgumentParser()
    parser.add_argument('--q', help='Search term', default='Google')
    parser.add_argument('--max-results', help='Max results', default=10)
    args = parser.parse_args()
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        maxResults=args.max_results
    ).execute()

    videos = []
    for search_result in search_response.get('items', []):
        if search_result['id']['kind'] == 'youtube#video':
            videos.append('%s' % (search_result['id']['videoId']))

    for video in videos:
        url = "https://www.youtube.com/watch?v=" + video
        video = pafy.new(url)
        if video.length < 600:
            VIDEO_QUEUE.put(video)
            msg = "Dodałem {} do playlisty.".format(video.title)
            print(msg)
            break


def youtube_add_playlist(query):
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--q', help='Search term', default='Google')
        parser.add_argument('--max-results', help='Max results', default=20)
        args = parser.parse_args()
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

        search_response = youtube.search().list(
            q=query,
            part='id,snippet',
            maxResults=args.max_results
        ).execute()

        playlists = []

        for search_result in search_response.get('items', []):
            if search_result['id']['kind'] == 'youtube#playlist':
                playlists.append('%s' % (search_result['id']['playlistId']))

        if playlists is not None:
            print(playlists)
            i = 0
            for item in pafy_playlist(playlists[0])['items']:
                try:
                    video = pafy.new(item['pafy'].watchv_url)
                    VIDEO_QUEUE.put(video)
                    print("Added {} to playlist.".format(video.title))
                    i += 1
                    if i > 50:
                        break
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        raise Exception
