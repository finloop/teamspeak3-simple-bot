import datetime
import logging
import os
import queue as Queue
import subprocess
import sys
import threading
import time
from datetime import timedelta
from subprocess import Popen
from time import sleep

import ts3
import validators

from helpers.loader import apikey, ADMINS, USERS
from helpers.teamspeak import sendcurrchannelmsg
from helpers.youtube import VIDEO_QUEUE, COMMAND_QUEUE, youtube_add_video, player, play, youtube_add_playlist, \
    youtube_add_playlist_from_link, \
    youtube_add_video_from_link

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-9s) %(message)s', filename="./logs.txt")

CONTROLS_QUEUE = Queue.Queue()
YOUTUBE_QUEUE = Queue.Queue()


def split(txt, seps):
    default_sep = seps[0]
    # we skip seps[0] because that's the default seperator
    for sep in seps[1:]:
        txt = txt.replace(sep, default_sep)
    return [i.strip() for i in txt.split(default_sep)]


class ProducerThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(ProducerThread, self).__init__()
        self.target = target
        self.name = name

    def run(self):
        time.sleep(5)
        ts3conn = ts3.query.TS3ClientConnection("telnet://localhost:25639")
        ts3conn.exec_("auth", apikey=apikey)
        botCLID = 0
        my_clid = ts3conn.query("clientlist").all()
        for client in my_clid:
            if client['client_nickname'] == 'BotPrzemka' and client['clid'] is not 0:
                botCLID = client['clid']
                query = ts3conn.query("clientmove", cid=10109, clid=botCLID)
                # ts3conn.exec_query(query)
                logging.debug("Executing query: {0}".format(query))
                sleep(0.5)
                sendcurrchannelmsg(
                    "Witam wszystkich na czacie. Bot made by [url=https://github.com/lordozo]Lordozo[/url]")
                break
        ts3conn.close()
        while True:
            try:
                ts3conn = ts3.query.TS3ClientConnection("telnet://localhost:25639")
                ts3conn.exec_("auth", apikey=apikey)
                ts3conn.exec_("clientnotifyregister", event="notifytextmessage", schandlerid=0)
                while True:
                    event = ts3conn.wait_for_event()
                    if not COMMAND_QUEUE.full():
                        COMMAND_QUEUE.put(event.parsed[0])
                        logging.debug("Putting {0} to COMMAND_QUEUE".format(event.parsed[0]))
                    else:
                        logging.debug('Queue is full....')
                    sleep(0.5)
            except Exception as e:
                logging.debug("Exception: {0}".format(str(e)))
            sleep(0.5)


class FirstConsumerThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(FirstConsumerThread, self).__init__()
        self.target = target
        self.name = name

    def run(self):
        while True:
            try:
                if not COMMAND_QUEUE.empty():
                    command = COMMAND_QUEUE.get()
                    logging.debug("Processing {0} as a user command".format(command))
                    if (command['invokeruid'] in ADMINS) or (command['invokeruid'] in USERS):
                        # command['msg'] = command['msg'].replace('\\\\s', ' ')
                        if command['msg'].startswith("!song"):
                            s = command['msg'][command['msg'].index(' ') + 1:]
                            try:
                                s = s.replace('[URL]', '')
                                s = s[:s.index('[')]
                            except Exception:
                                print("not link...")
                            if len(s) >= 1:
                                if validators.url(s):
                                    YOUTUBE_QUEUE.put({"type": "songlink", "link": s})
                                else:
                                    logging.debug("Adding {0} as a add video command".format(command))
                                    YOUTUBE_QUEUE.put({"type": "video", "query": s})
                                # youtube_add_video(s)
                        if command['msg'].startswith("!playlist"):
                            s = command['msg'][command['msg'].index(' ') + 1:]
                            try:
                                s = s.replace('[URL]', '')
                                s = s[:s.index('[')]
                            except Exception:
                                print("not link...")
                            if len(s) >= 1:
                                if validators.url(s):
                                    YOUTUBE_QUEUE.put({"type": "playlistlink", "link": s})
                                else:
                                    logging.debug("Adding {0} as a add playlist command".format(command))
                                    YOUTUBE_QUEUE.put({"type": "playlist", "query": s})
                            # youtube_add_playlist(s)
                        elif command['msg'].startswith("!skipall"):
                            CONTROLS_QUEUE.put("SKIPALL")
                        elif command['msg'].startswith("!skip"):
                            logging.debug("Adding {0} as a add skip command".format(command))
                            CONTROLS_QUEUE.put("SKIP")
                        elif command['msg'].startswith("!move"):
                            ts3conn = ts3.query.TS3ClientConnection("telnet://localhost:25639")
                            ts3conn.exec_("auth", apikey=apikey)
                            ts3conn.exec_("clientnotifyregister", event="any", schandlerid=0)
                            my_clid = ts3conn.query("clientlist").all()
                            botCLID = 0
                            for client in my_clid:
                                if client['client_nickname'] == 'BotPrzemka' and client['clid'] is not 0:
                                    botCLID = client['clid']
                                    break
                            s = command['msg'][command['msg'].index(' ') + 1:]
                            print(s)
                            if len(s) >= 1:
                                print(s)
                                try:
                                    a = int(s)
                                    print(a)
                                    print('--------')
                                    query = ts3conn.query("clientmove", cid=s, clid=botCLID)
                                    ts3conn.exec_query(query)
                                    logging.debug("Executing query: {0}".format(query))
                                except Exception:
                                    query = ts3conn.query("channellist")
                                    ts3conn.exec_query(query)
                                    channels = query.all()
                                    for channel in channels:
                                        print(channel)
                                        if s in channel['channel_name']:
                                            cid = channel['cid']
                                            print(cid)
                                            query = ts3conn.query("clientmove", cid=cid, clid=botCLID)
                                            ts3conn.exec_query(query)
                                            logging.debug("Executing query: {0}".format(query))
                                            break
                        elif command['msg'].startswith("!adduser"):
                            s = command['msg'][command['msg'].index(' ') + 1:]
                            if len(s) >= 3:
                                if s not in USERS:
                                    USERS.append(s)
                                    msg = "Dodaję użytkownika o UID {0}".format(s)
                                    sendcurrchannelmsg(msg)
                                    with open("users.txt", "w+") as f:
                                        for user in USERS:
                                            f.write("{0}\n".format(user))
                        elif command['msg'].startswith("!deluser"):
                            s = command['msg'][command['msg'].index(' ') + 1:]
                            if len(s) >= 3:
                                if s in USERS:
                                    USERS.remove(s)
                                    msg = "Usuwam użytkownika o UID {0}".format(s)
                                    sendcurrchannelmsg(msg)
                                    with open("users.txt", "w+") as f:
                                        for user in USERS:
                                            f.write("{0}\n".format(user))
                        elif command['msg'].startswith("!help"):
                            sb = "!song [tytuł piosenki z yt lub link]\n" \
                                 "!playlist [tytuł playlisty z yt, doda się max 20 lub link]\n" \
                                 "!skip - przeskakuje jedną piosenkę dalej\n" \
                                 "!skipall - przeskakuje całą playlistę\n" \
                                 "!adduser [UID bez znaku =]\n" \
                                 "!deluser [UID bez znaku =]\n" \
                                 "!move [ID kanału lub jego nazwa]"
                            sendcurrchannelmsg(sb)

                sleep(0.03)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                logging.debug("Exception: {0}".format(e))
                sleep(0.1)


class SecondConsumerThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(SecondConsumerThread, self).__init__()
        self.target = target
        self.name = name
        return

    def run(self):
        now = datetime.datetime.utcnow() + timedelta(seconds=60)
        stop = datetime.datetime.utcnow()
        isPaused = False
        while True:
            try:
                now = datetime.datetime.utcnow()
                if not VIDEO_QUEUE.empty():
                    if (stop - now).total_seconds() <= 2 or isPaused:
                        # next song
                        isPaused = False
                        video = VIDEO_QUEUE.get()
                        logging.debug("Starting video: {0}".format(video))
                        s = play(video)
                        stop = datetime.datetime.utcnow() + timedelta(seconds=s)
                        logging.debug("Playing next song: {0}".format(video))
                        msg = "Teraz gram {0}".format(video.title)
                        sendcurrchannelmsg(msg)
                    elif not CONTROLS_QUEUE.empty() and not isPaused:
                        command = CONTROLS_QUEUE.get()
                        if command == "SKIP":
                            # asked for skip
                            player.pause()
                            video = VIDEO_QUEUE.get()
                            logging.debug("Starting video: {0}".format(video))
                            s = play(video)
                            isPaused = False
                            stop = datetime.datetime.utcnow() + timedelta(seconds=s)
                            logging.debug("Skipping and playing : {0}".format(video))
                            msg = "Teraz gram {0}".format(video.title)
                            sendcurrchannelmsg(msg)
                        if command == "SKIPALL":
                            # asked for skip
                            player.pause()
                            while not VIDEO_QUEUE.empty():
                                try:
                                    VIDEO_QUEUE.get(False)
                                except Queue.Empty:
                                    continue
                                VIDEO_QUEUE.task_done()
                            logging.debug("Skipping all videos.")
                            isPaused = False
                            stop = datetime.datetime.utcnow() + timedelta(seconds=1)
                elif not CONTROLS_QUEUE.empty() and (not isPaused or player.is_playing):
                    command = CONTROLS_QUEUE.get()
                    if command == "SKIP":
                        # asked for skip
                        player.pause()
                        isPaused = True
                        logging.debug("SKIPPING")
                    elif command == "SKIPALL":
                        isPaused = True
                        player.pause()
                        logging.debug("SKIPPING ALL")
                        sendcurrchannelmsg("Próbuję pominąć wszytskie utwory.")
                        while not VIDEO_QUEUE.empty():
                            try:
                                VIDEO_QUEUE.get(False)
                            except Queue.Empty:
                                continue
                            VIDEO_QUEUE.task_done()
                sleep(0.1)
            except Exception as e:
                logging.debug("Exception: {0}".format(e))
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                logging.debug("Exception: {0}".format(e))
                sleep(0.1)


class YoutubeWorker(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(YoutubeWorker, self).__init__()
        self.target = target
        self.name = name

    def run(self):
        while True:
            try:
                if not YOUTUBE_QUEUE.empty():
                    obj = YOUTUBE_QUEUE.get()
                    if obj['type'] is 'video':
                        # add video to playlist
                        youtube_add_video(obj['query'])
                    elif obj['type'] is 'playlist':
                        # add playlist to playlist
                        youtube_add_playlist(obj['query'])
                    elif obj['type'] is 'playlistlink':
                        youtube_add_playlist_from_link(obj['link'])
                    elif obj['type'] is 'songlink':
                        youtube_add_video_from_link(obj['link'])
                sleep(0.5)
            except Exception as e:
                logging.debug("Exception: {0}".format(e))
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                logging.debug("Exception: {0}".format(e))
                sleep(0.1)


if __name__ == '__main__':
    Popen('pulseaudio -vvv', stderr=subprocess.DEVNULL, shell=True)
    print(
        '-------------------============================================================================---------------------------------------------------HELLLOOOOOOOOO')
    time.sleep(2)
    Popen(
        'cd ~ && cd TeamSpeak3-Client-linux_amd64 && xvfb-run --auto-servernum --server-args=\'-screen 0 640x480x24:32\' ./ts3client_runscript.sh',
        stderr=subprocess.DEVNULL, shell=True)

    p = ProducerThread(name='producer')
    fc = FirstConsumerThread(name='firstconsumer')
    sc = SecondConsumerThread(name='secondconsumer')
    ytworker = YoutubeWorker(name='youtubeworker')
    p.start()
    fc.start()
    sc.start()
    ytworker.start()
