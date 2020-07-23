#!/usr/bin/env python3.8

import os
import pickle
import subprocess
import sys
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

api_service_name = "youtube"
api_version = "v3"
client_secrets_file = "client_secret.json"
YOUTUBE_URL="https://www.youtube.com/watch?v="


def process_video(videoId, videoTitle):
    title = "".join(e for e in videoTitle if e.isalnum() or e == " ")
    value = subprocess.run(["ls", "|", "grep \"" + title + "\""], capture_output=True)
    if value.stdout == b'':
        subprocess.run(["youtube-dl", "-o", "/home/pi/Videos/%(title)s.%(ext)s", YOUTUBE_URL+videoId])

def main(channelName):

    # Get credentials and create an API client

    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
            creds = flow.run_console()
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=creds)

    request = youtube.search().list(
        part="snippet",
        q=channelName
    )

    response = request.execute()
    channelId = response["items"][0]["snippet"]["channelId"]

    request = youtube.channels().list(
        part="contentDetails",
        id=channelId
    )
    response = request.execute()

    uploads = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=uploads,
        maxResults=50
    )
    response = request.execute()
    totalRes = response["pageInfo"]["totalResults"]

    nextToken = None
    while True:
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads,
            maxResults=50,
            pageToken=nextToken
        )
        response = request.execute()
        for item in response["items"]:
            videoId = item["snippet"]["resourceId"]["videoId"]
            videoTitle = item["snippet"]["title"]
            process_video(videoId, videoTitle)
        if "nextPageToken" in response:
            nextToken = response["nextPageToken"]
        else:
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Requires name of channel as argument")
        exit(1)
    channelName = sys.argv[1]
    main(channelName)
