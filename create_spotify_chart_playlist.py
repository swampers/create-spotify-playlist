from bs4 import BeautifulSoup
import argparse
import urllib.parse
import datetime
import base64
import requests
import os
import spotipy
import string
import random
from spotipy.oauth2 import SpotifyOAuth
import logging
from config import *
import update_spotify_playlist_pic
import find_spotify_track

logging.basicConfig(filename='chartplaylist.log', level=logging.WARNING)

def get_args():
    parser = argparse.ArgumentParser(description='Scrapes UK Singles Chart data and creates a Spotify playlist')
    parser.add_argument('-y','--yearLong', required=False, default=False, help='Flag: use a full year of data?', action="store_true")
    parser.add_argument('-t','--topX',required=False, default=5, help="Top X hits used from each week's chart",type=int)
    parser.add_argument('-p','--playlistID',required=False, default='', help="PlaylistID (from Spotify) to overwrite")
    parser.add_argument('-s','--start',required=False, default=datetime.date.today(), help="Start date for playlist (in ISO format) - omit for timewarp update", type=datetime.date.fromisoformat)
    return parser.parse_args()


def main():
        
    args = get_args()

    #Sign in
    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, 
                            client_secret=client_secret,
                            redirect_uri=redirect_uri,
                            scope=scope,
                            username=username))

    yearLong = args.yearLong 
    top_x = args.topX

    if args.playlistID == '':
        newPlaylist = True
    else:
        newPlaylist = False 
    
    if yearLong:
        startdate = datetime.date(int(args.start.year),1,1)
    else:
        startdate = args.start

    stopdate = (startdate,datetime.date(int(startdate.year),12,31))[yearLong]

    #print(args)
    randyear = 0
    today = datetime.date.today()
    
    if startdate == today:
        yearLong = False
        top_x = 40
        randyear = random.choice([2,5,5,10,10,10,10,25,25,25,25,30,30,30,35,35,40,40,45,50,55])
        startdate = datetime.date(int(today.year) - randyear, int(today.month), int(today.day))
        stopdate = startdate
        #print(yearLong, top_x, randyear, startdate, stopdate)
        
    
    period = (stopdate - startdate).days
    #print("Period: " + str(period))
    if period < 0 or (period >=1 and period < 7): exit()  #We want one particular day, or we want multiple weeks.

    weeks = (abs(period) // 7 ) + 1
    #print("Weeks: " + str(weeks))

    if randyear == 0:
        playlistDescription = "UK " + ("Top " + str(top_x) + " ","Number 1 " )[top_x==1] + "hits from " + (str(startdate.year) + " - chronologically", startdate.strftime('%d-%m-%Y'))[period==0] + ". (Scraped from UK Official Singles Chart.)"
        #print(playlistDescription)
        
        playlistName = "UK " + ("Top ","Number 1 " )[top_x==1] + "Hits: " + (str(startdate.year), startdate.strftime('%d-%m-%Y'))[period==0]
        #print(playlistName)
        
        cover_title = "UK " + ("Top Hits","Number 1s" )[top_x==1] 
        cover_date = (str(startdate.year), startdate.strftime('%d-%m-%Y'))[period==0]
        if not newPlaylist: 
            playlist = args.playlistID
        else:
            playlist = spotify.user_playlist_create(username, playlistName, True, False, playlistDescription)['id']
            #print(playlist)

    else:
        playlistDescription = "UK Top " + str(top_x) + " hits from this week, " + str(randyear) + " years ago. Updated weekly, every Monday. (Scraped from UK Official Singles Chart.)"
        playlistName = "UK Top " + str(top_x) + " Hits: Timewarp"
        cover_title = "UK Top " + str(top_x) 
        cover_date = "Timewarp"
        playlist = target_playlist
        print(playlistDescription)
        print(playlistName)
        print(cover_title)
        print(cover_date)
        print(playlist)
    
    downloaddate = startdate - datetime.timedelta((startdate.weekday() +1)%7)  #URLs are dated for the Sunday

    # We don't want stupidly large playlists
    if top_x * weeks >= 1000: exit()

    filelist = [] #for quicker access later
    
    # download any pages not already downloaded
    for week in range(0,weeks):
        urldate = downloaddate + datetime.timedelta(week*7)
        #print(urldate)
        url = f"https://www.officialcharts.com/charts/singles-chart/{urldate.strftime('%Y%m%d')}"
        
        local_filename = f"raw/charts/{url.strip('/').split('/')[-1]}"
        filelist.append(local_filename)
        if not os.path.exists(local_filename):
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

    # Initialise playlist files
    if os.path.exists("playlist"): os.remove("playlist")  #This one is used to create the playlist
    if os.path.exists("playlist0"): os.remove("playlist0")  #This one will have duplicates



    with open("playlist0","w") as outfile:
        for path in filelist:
            with open(path, "rb") as file:
                year = int(path[-8:-4])
                month = int(path[-4:-2])
                day = int(path[-2:])
                file_start_date = datetime.date(year,month,day)
                file_end_date = file_start_date + datetime.timedelta(days=6)

                #Verify the file is within the range we want
                if (period > 7 and file_end_date >= startdate and file_end_date <= stopdate) or (period == 0 and file_end_date >= stopdate and file_start_date <= startdate): 
                        
                    soup = BeautifulSoup(file, features = "lxml")
                    
                    rows = [row for row in soup.select("table.chart-positions tr") if len(row.select("td")) == 7]
                    
                    if len(rows) < top_x: top_x = len(rows) #If it's looking for top 100 but only 40 exist, look for 40
                    
                    for i in range(top_x):
                        row = rows[i]
                        position = row.select("span.position")[0].text
                        track = row.select("div.track div.title a")[0].text
                        artist = row.select("div.track div.artist a")[0].text
                        
                        track_id = find_spotify_track.find_track(artist, track)
                        if track_id is not None:
                            outfile.write(track_id+"\n")

                if (file_end_date + datetime.timedelta(1) ) > stopdate: 
                    break

    outfile.close()

    #Deduplicate lines in playlist0 -> playlist 
    lines_seen = set() # holds lines already seen
    outfile = open("playlist", "w")
    for line in open("playlist0", "r"):
        if line not in lines_seen: # not a duplicate
            outfile.write(line)
            lines_seen.add(line)
    outfile.close()
      
    tracks = ['']
    outfile = open("playlist", "r")
    i = 0
    for line in outfile:
        tracks[0] = line.split("\n")[0]
        try:
            if i==0:
                spotify.playlist_replace_items(playlist, tracks)
            else:
                spotify.playlist_add_items(playlist, tracks)
            i += 1
        except:
            #print("Error: "+ tracks[0])
            exit()
    outfile.close()

    spotify.playlist_change_details(playlist, name=playlistName, description=playlistDescription)
    
    update_spotify_playlist_pic.random_pic(playlist,cover_title,cover_date)
    
    
if __name__ == '__main__':
    main()