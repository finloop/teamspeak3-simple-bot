with open("apikey.txt") as f:
    lines = [line.rstrip('\n') for line in f]
    apikey = lines[0]

with open("admins.txt") as f:
    lines = [line.rstrip('\n') for line in f]
    ADMINS = lines

with open("users.txt") as f:
    lines = [line.rstrip('\n') for line in f]
    USERS = lines

with open("apikey_yt") as f:
    lines = [line.rstrip('\n') for line in f]
    DEVELOPER_KEY = lines[0]
