import requests
import json
import getpass

username = ""
password = ""
pandora_base = "https://www.pandora.com"
csrf_header = "X-CsrfToken"
auth_token_header = "X-AuthToken"
csrf_token = ""
auth_token = ""
webname = ""
likes_length = 0
likes = []
premium = False

#Prompts the user for their Pandora credentials
def get_creds():
    global username, password 
    username = raw_input("Pandora email: ")
    password = getpass.getpass("Pandora password: ")

#Obtains the CSRF-token, used in the session cookie and in a header
def get_csrf_cookie():
    print "\nObtaining necessary information..."
    try:
        response = requests.get(pandora_base)
        global csrf_token
        csrf_token = response.cookies['csrftoken']
    except:
        print "An error occurred, make sure you have access to " + pandora_base + " from your location"
        exit()

#Authenticates the user with the supplied credentials and
#obtains the auth_token and the webname of the user
def authenticate():
    path = "/api/v1/auth/login"
    cookies = {
        "csrftoken": csrf_token
    }
    headers = {
        csrf_header: csrf_token
    }
    params = {
        "username": username,
        "password": password
    }
    try:
        response = requests.post(pandora_base + path, json=params, cookies=cookies, headers=headers)
        global auth_token, webname
        auth_token = response.json()['authToken']
        webname = response.json()['webname']
        print "Success! Fetching your likes..."
    except:
        print "An error occurred, make sure the supplied credentials are valid"
        exit()

#Gets the total number of the user likes
def fetch_likes_length():
    path = "/api/v1/station/getFeedback"
    cookies = {
        "csrftoken": csrf_token
    }
    headers = {
        csrf_header: csrf_token,
        auth_token_header: auth_token
    }
    params = {
        "pageSize": 1,
        "startIndex": 0,
        "webname": webname
    }
    try:
        response = requests.post(pandora_base + path, json=params, cookies=cookies, headers=headers)
        global likes_length
        likes_length = int(response.json()['total'])
        print "Found " + str(likes_length) + " likes"
    except:
        print "An error occurred, aborting..."
        exit() 

#Fetches the user likes and puts them in a list of dicts
def fetch_likes():
    start_index = 0
    run = True
    path = "/api/v1/station/getFeedback"
    cookies = {
        "csrftoken": csrf_token
    }
    headers = {
        csrf_header: csrf_token,
        auth_token_header: auth_token
    }
    try:
        while run:
            params = {
                "pageSize": 100,
                "startIndex": start_index,
                "webname": webname
            }
            response = requests.post(pandora_base + path, json=params, cookies=cookies, headers=headers)
            feedback_json = response.json()['feedback']
            if len(feedback_json) < 100:
                run = False
            global likes
            for feedback in feedback_json:
                likes.append({
                    "song_title": feedback['songTitle'].encode("utf-8"),
                    "artist_name": feedback['artistName'].encode("utf-8"),
                    "album_title": feedback['albumTitle'].encode("utf-8"),
                    "music_id": feedback['musicId'][1:].encode("utf-8"),
                    "audio_url": "N/A"
                })
            start_index = start_index + 100
        check_on_demand()
    except:
        print "An error occurred, aborting..."
        exit()

#Writes the likes into an HTML document, can be viewed by many software types
#Browsers, Excel, etc.
def write_likes():
    file_name = webname + ".html"
    top = """<html><head>
            <meta http-equiv="content-type" content="text/plain; charset=UTF-8"/>
            <style>
            .Head { background-color:gray; color:white; }
            </style></head><body>
            <table border=1>
            <tr><td class=Head>Song Title</td><td class=Head>Artist Name</td><td class=Head>Album Title</td><td class=Head>Music ID</td><td class=Head>Audio URL</td></tr>
            """
    try:
        with open(file_name, "w") as likes_file:
            likes_file.write(top)
            for like in likes:
                line = "<tr><td>" + like['song_title'] + "</td><td>" + like['artist_name'] + "</td><td>" + like['album_title'] + "</td><td>" + like['music_id'] + "</td><td>" + like['audio_url'] + "</td></tr>"
                likes_file.write(line)
            likes_file.write("</table></body></html>")
        likes_file.close()
        print "Likes written to " + file_name + ", open it with a browser or in Excel"
    except:
        print "Likes file couldn't be written, aborting..."
    exit()

def get_playback_url(music_id):
    path = "/api/v1/ondemand/getAudioPlaybackInfo"
    cookies = {
        "csrftoken": csrf_token
    }
    headers = {
        csrf_header: csrf_token,
        auth_token_header: auth_token
    }
    params = {
        "pandoraId": "TR:" + str(music_id),
        "sourcePandoraId": "TR:" + str(music_id)
    }
    response = requests.post(pandora_base + path, json=params, cookies=cookies, headers=headers)
    try:
        return response.json()['audioURL'].encode("utf-8")
    except:
        return response.json()['errorString'].encode("utf-8")

def check_on_demand():
    playback_message = get_playback_url(1)
    if  playback_message == "LISTENER_NOT_AUTHORIZED":
        print "User is not a Pandora Premium subscriber, likes can't be downloaded"
    else:
        global premium
        premium = True
        print "User is a Pandora Premium subscriber, likes can be downloaded"

def download_likes():
    print "Downloading liked tracks..."
    i = 1.0
    for like in likes:
        like['audio_url'] = get_playback_url(like['music_id'])
        if i%20 == 0:
            print "{0:.0f}% done".format((i/likes_length) * 100)
        i += 1

def download_prompt():
    if not premium:
        return
    download = raw_input("Attempt to download liked tracks? [y/n]")
    if download.lower() == 'y':
        download_likes()

funcs = [get_creds, get_csrf_cookie, authenticate, fetch_likes_length, fetch_likes, download_prompt, write_likes]
for func in funcs:
    func()