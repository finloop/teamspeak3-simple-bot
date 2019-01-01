#!/usr/bin/python3

import ts3



def sendcurrchannelmsg(msg):
    with ts3.query.TS3ClientConnection("telnet://localhost:25639") as ts3conn:
        ts3conn.exec_("auth", apikey=apikey)

        # Register for events
        ts3conn.exec_("clientnotifyregister", event="any", schandlerid=0)
        my_clid = ts3conn.query("clientlist").all()
        clid = 0
        for client in my_clid:
            if client["client_nickname"] == "BotPrzemka":
                clid = client['clid']

        query = ts3conn.query("sendtextmessage", msg=msg, targetmode=2, target=clid)
        ts3conn.exec_query(query)
