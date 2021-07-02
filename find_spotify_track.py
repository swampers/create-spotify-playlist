import argparse
import datetime
import requests
import os
import spotipy
import string
from spotipy.oauth2 import SpotifyOAuth
import logging
from config import *

logging.basicConfig(filename='findtrack.log', level=logging.WARNING)

def get_args():
    parser = argparse.ArgumentParser(description='Retrieves the Spotify Track ID for a given artist and track')
    parser.add_argument('-a','--Artist', required=True, help='Artist name')
    parser.add_argument('-t','--Track', required=True, help='Track name')
    return parser.parse_args()


def main():
        
    args = get_args()

    artist = args.Artist
    track = args.Track

    r = find_track(artist, track)
    
    print(r)
    return r

def find_track(artist, track):

    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, 
                            client_secret=client_secret,
                            redirect_uri=redirect_uri,
                            scope=scope,
                            username=username))

                        
    clean_track = track.split(" FT ")[0].split(" {")[0].split("/")[0]
    if clean_track[0] == "(": clean_track = clean_track.split(") ")[-1]
    clean_track = clean_track.split(" (")[0]
    clean_track = clean_track.translate(str.maketrans('', '', string.punctuation))  #sometimes this doesn't help!!
    #print(clean_track)
    
    clean_artist = artist.split(" FT ")[0].split(" FEATURING ")[0].split(" WITH ")[0].split(" AND ")[0].split("{")[0]
    if clean_artist[0:4] == "THE ": clean_artist = clean_artist[4:]
    #print(clean_artist)
    
    response = spotify.search(q = 'track:"' + clean_track + '" artist:' + clean_artist , type = 'track', market = 'GB')
    
    try:
        track_id = response['tracks']['items'][0]['id']
    except:
        track_id = None
        
    if track_id == None:    
        # How to find the track if this didn't work?
        # Search without artist
        response = spotify.search(q = 'track:' + clean_track, type = 'track', market = 'GB', limit = 1)
        
        try:
            new_id = response['tracks']['items'][0]['id']  #First response
            new_name = response['tracks']['items'][0]['artists'][0]['name'] #Artist of first response
            #If the artist of the first response matches up with the artist on the webpage, we found the track
            # (Punctuation is mostly removed on the website, but spotify tends to keep it)
            new_name = new_name.translate(str.maketrans('', '', string.punctuation)).upper() 
            clean_artist = clean_artist.translate(str.maketrans('', '', string.punctuation)).upper() 
            if new_name[0:4] == "THE ": new_name = new_name[4:]
            minlen = min(len(new_name),len(clean_artist))
            if new_name[:minlen] == clean_artist[:minlen]: track_id = new_id
            
        except:
            track_id = None
    
    if track_id == None:    
        # How to find the track if this didn't work?
        # Search without artist, and don't remove punctuation from track title
        #print(track)
        
        new_track = track.split(" FT ")[0].split(" {")[0].split("/")[0]
        if new_track[0] == "(": new_track = new_track.split(") ")[-1]
        new_track = new_track.split(" (")[0]
        response = spotify.search(q = 'track:' + new_track, type = 'track', market = 'GB', limit = 1)
                            
        try:
            new_id = response['tracks']['items'][0]['id']  #First response
            new_name = response['tracks']['items'][0]['artists'][0]['name'] #Artist of first response
            #If the artist of the first response matches up with the artist on the webpage, we found the track
            # (Punctuation is mostly removed on the website, but spotify tends to keep it)
            new_name = new_name.translate(str.maketrans('', '', string.punctuation)).upper() 
            if new_name[0:4] == "THE ": new_name = new_name[4:]
            minlen = min(len(new_name),len(clean_artist))
            #print(str(new_name[:minlen] == clean_artist[:minlen]))
            if new_name[:minlen] == clean_artist[:minlen]: 
                track_id = new_id
                clean_track = new_track
        except:
            track_id = None
    
    if track_id == None:    
        #Just try the query without cleaning and without specifying track and artist.
        
        response = spotify.search(q =  track + ' ' + artist, type = 'track', market = 'GB', limit = 1)
        
        try:
            new_id = response['tracks']['items'][0]['id']
            new_name = response['tracks']['items'][0]['artists'][0]['name']
            new_track = response['tracks']['items'][0]['name']

            new_name = new_name.translate(str.maketrans('', '', string.punctuation)).upper() 
            if new_name[0:4] == "THE ": new_name = new_name[4:]
            minlen = min(len(new_name),len(clean_artist))
            
            new_track = new_track.translate(str.maketrans('', '', string.punctuation)).upper() 
            minlen2 = min(len(new_track),len(clean_track))
            
            if new_name[:minlen] == clean_artist[:minlen] and new_track[:minlen2] == clean_track[:minlen2]: 
                track_id = new_id
                clean_track = new_track
                clean_artist = new_name
        except:
            track_id = None
            
    if track_id == None:
        #Translate via dicts (below)
        
        trans_artist = translate_artist(artist)
        trans_track = translate_track(track)
        
        if (trans_artist != artist) or (trans_track != track): #Don't want an infinite loop!
            track_id = find_track(trans_artist,trans_track)  #Put it back into the search method above
        else:
            track_id = None
        
    
    if track_id is not None: 
        return track_id
    else:
        logging.warning('TRACK: ' + track + ' ARTIST: ' + artist )
        return None

def translate_artist(artist):

    lookup_artist = {
                    "(MC SAR &) THE REAL MCCOY":"THE REAL MCCOY"
                   ,"P DIDDY":"DIDDY"
                   ,"PUFF DADDY":"DIDDY"
                   ,"P DIDDY FT NICOLE SCHERZINGER":"DIDDY"
                   ,"PUFF DADDY FT JIMMY PAGE":"DIDDY"
                   ,"PINK":"P!NK"
                   ,"MACKLEMORE/RYAN LEWIS/DALTON":"MACKLEMORE"
                   ,"OZZY & KELLY OSBOURNE":"KELLY OSBOURNE"
                   ,"WIZARD OF OZ FILM CAST":"THE MUNCHKINS"
                   ,"GRANDE/CYRUS/LANA DEL REY":"ARIANA GRANDE"
                   ,"FATBOYSLIM/RIVASTARR/BEARDYMAN":"FATBOY SLIM"
                   ,"BAZ LUHRMANN":"QUINDON TARVER JOSH ABRAHAMS"
                   ,"LAURYN HILL":"MS. LAURYN HILL"
                   ,"C&C MUSIC FACTORY FEATURING FREEDOM WILLIAMS":"C&C MUSIC FACTORY"
                   ,"T.REX":"T. REX"
                   ,"PEREZ 'PREZ' PRADO":"PEREZ PRADO"
                   ,"PEREZ 'PREZ' PRADO & HIS ORCH":"PEREZ PRADO"
                   ,"MOUSSE T VS HOT'N'JUICY":"MOUSSE T."
                   ,"TOM JONES & MOUSSE T":"MOUSSE T."
                   ,"TERENCE TRENT D'ARBY":"SANANDA MAITREYA"
                   ,"JOE DOLCE MUSIC THEATRE":"JOE DOLCE"
                   ,"PATRICK MACNEE AND HONOR BLACKMAN":"HONOR BLACKMAN"
                   ,"TOM JONES & STEREOPHONICS":"TOM JONES"
                   ,"J.J. BARRIE":"J J BARRIE"
                   ,"MARY J BLIGE & U2":"MARY J. BLIGE"
                   ,"RUN-D.M.C. VS JASON NEVINS":"RUN-D.M.C."
                   ,"THE FOUR SEASONS":"FRANKIE VALLI & THE FOUR SEASONS"
                   ,"LITTLE JIMMY OSMOND":"JIMMY OSMOND"
                   ,"ARIANA GRANDE & SOCIAL HOUSE":"ARIANA GRANDE"
                   ,"OLLIE AND JERRY":"OLLIE & JERRY"
                   ,"BEYONCE & SHAKIRA":"BEYONCÉ"
                   ,"ALICE DEEJAY":"ALICE DJ"
                   ,"RICHARD X VS LIBERTY X":"LIBERTY X"
                   ,"JOBOXERS":"JO BOXERS"
                   ,"BOYSTOWN GANG":"BOYS TOWN GANG"
                   ,"DETROIT SPINNERS":"THE SPINNERS"
                   ,"GALAXY FEATURING PHIL FEARON":"GALAXY"
                   ,"ALEXANDRA BURKE/ERICK MORILLO":"ALEXANDRA BURKE"
                   ,"LUTHER VANDROSS & MARIAH CAREY":"LUTHER VANDROSS"
                   ,"PINK FT WILLIAM ORBIT":"P!NK"
                   ,"HARRIS/PHARRELL/PERRY/BIG SEAN":"CALVIN HARRIS"
                   ,"MELANIE B":"MEL B"
                   ,"GEORGE MICHAEL AND QUEEN WITH LISA STANSFIELD":"GEORGE MICHAEL"
                   ,"DUNCAN JAMES & KEEDIE":"ANDREW LLOYD WEBBER"
                   ,"ANOTHER LEVEL/GHOSTFACE KILLAH":"ANOTHER LEVEL"
                   ,"EMF/REEVES AND MORTIMER":"EMF"
                   ,"CELINE DION & R KELLY":"R. KELLY"
                   ,"STILTSKIN":"RAY WILSON"
                   ,"WILL I AM FT CODY WISE":"WILL.I.AM"
                   ,"WILL I AM":"WILL.I.AM"
                   ,"TIESTO/DZEKO/PREME/POST MALON":"TIËSTO"
                   ,"KEVIN ROWLAND AND DEXY'S MIDNIGHT RUNNERS":"DEXY'S MIDNIGHT RUNNERS"
                   ,"APOLLO FOUR FORTY":"APOLLO 440"
                   ,"MAN 2 MAN MEETS MAN PARRISH":"MAN 2 MAN"
                   ,"TRUE STEPPERS/BOWERS/BECKHAM":"TRUE STEPPERS"
                   ,"DAVID BOWIE AND BING CROSBY":"BING CROSBY"
                   ,"LISA STANSFIELD/DIRTY ROTTEN..":"COLDCUT"
                   ,"THE BEATMASTERS FEATURING THE COOKIE CREW":"THE BEAT MASTERS"
                   ,"BENNY BENASSI PTS THE BIZ":"BENNY BENASSI"
                   ,"CHRISTINA MILIAN/YOUNG JEEZY":"CHRISTINA MILIAN"
                   ,"ROBBIE WILLIAMS & GARY BARLOW":"GARY BARLOW"
                   ,"SUPERMEN LOVERS/MANI HOFFMAN":"THE SUPERMEN LOVERS"
                   ,"STARSOUND":"STARS ON 45"
                   ,"STAR SOUND":"STARS ON 45"
                   ,"REBEL MC AND DOUBLE TROUBLE":"DOUBLE TROUBLE"
                   ,"MARTI WEBB":"ANDREW LLOYD WEBBER"
                   ,"BARBRA STREISAND & CELINE DION":"BARBRA STREISAND"
                   ,"TWEETS":"THE TWEETS"
                   ,"(SYMBOL)":"PRINCE"
                   ,"SETTLE/GREATEST SHOWMAN ENS":"KEALA SETTLE"
                   ,"SARAH BRIGHTMAN/ANDREA BOCELLI":"FRANCESCO SARTORI"
                   ,"IRONIK/CHIPMUNK/ELTON JOHN":"IRONIK"
                   ,"GIORGIO MORODER AND PHILIP OAKEY":"PHIL OAKEY"
                   ,"FREAKPOWER":"FREAK POWER"
                   ,"D MOB FEATURING GARY HAISMAN":"D MOB"
                   ,"RONAN KEATING FT LULU":"LULU"
                   ,"EVA CASSIDY & KATIE MELUA":"KATIE MELUA"
                   ,"SKRILLEX & DIPLO/JUSTIN BIEBER":"JACK U"
                   ,"MILITARY WIVES/GARETH MALONE":"PAUL MEALOR"
                   ,"GUYS AND DOLLS":"GUYS 'N DOLLS"
                   ,"MICHAEL BALL/CAPTAIN TOM MOORE":"MICHAEL BALL"
                   }

    try: 
        return lookup_artist[artist] 
    except:
        return artist
     
                   
                   
                    
def translate_track(track):

    lookup_track = {
                    "OOPS UP":"OOOPS UP"
                   ,"LET THE SUNSHINE":"LET THE SUN SHINE"
                   ,"NUFF VIBES EP":"BOOM SHACK-A-LAK"
                   ,"ABBA-ESQUE (EP)":"TAKE A CHANCE ON ME"
                   ,"BLUE MONDAY 1988":"BLUE MONDAY '88"
                   ,"CRACKERS INTERNATIONAL (EP)":"STOP!"
                   ,"DANCING ON A SATURDAY NIGHT":"DANCIN' ON A SATURDAY NIGHT"
                   ,"DANCING TIGHT FT PHIL FEARON":"DANCING TIGHT"
                   ,"ELECTRIC AVENUE":"ELECTRIC AVENNUE"
                   ,"FIVE LIVE (EP)":"SOMEBODY TO LOVE"
                   ,"FOUR BACHARACH AND DAVID SONGS (EP)":"I'LL NEVER FALL IN LOVE AGAIN"
                   ,"FOUR FROM TOYAH (EP)":"IT'S A MYSTERY"
                   ,"GROOVIN' (YOU'RE THE BEST THING/BIG BOSS GROOVE)":"YOU'RE THE BEST THING"
                   ,"I CAN'T GIVE YOU ANYTHING (BUT MY LOVE)":"CAN'T GIVE YOU ANYTHING (BUT MY LOVE)"
                   ,"I GET A LITTLE SENTIMENTAL OVER YOU FT. LYN PAUL":"I GET A LITTLE SENTIMENTAL OVER YOU"
                   ,"I LOVE YOU ANYWAY":"LOVE YOU ANYWAY"
                   ,"MASTERBLASTER (JAMMIN')":"MASTER BLASTER (JAMMIN')"
                   ,"OXYGENE PART IV":"OXYGENE, PT. 4"
                   ,"PEACE ON EARTH/LITTLE DRUMMER BOY":"PEACE ON EARTH / LITTLE DRUMMER BOY"
                   ,"READ ALL ABOUT IT PT 3":"READ ALL ABOUT IT, PT. III"
                   ,"REASONS TO BE CHEERFUL, PART 3":"REASONS TO BE CHEERFUL, PT. 3"
                   ,"RENEGADE MASTER 98":"RENEGADE MASTER"
                   ,"TOKOLOSHE MAN":"TOKOLSHE MAN"
                   ,"TOOFUNKY":"TOO FUNKY"
                   ,"WE CALL IT ACIEED FT GARY HAISMAN":"WE CALL IT ACIEEED"
                   ,"YOU HAVE BEEN LOVED EP":"YOU HAVE BEEN LOVED"
                   ,"YOU WON'T FIND ANOTHER FOOL LIKE ME FT. LYN PAUL":"YOU WON'T FIND ANOTHER FOOL LIKE ME"
                   ,"YOU'LL NEVER STOP ME FROM LOVING YOU":"YOU'LL NEVER STOP ME LOVING YOU"
                   ,"DECEMBER '63":"DECEMBER, 1963 (OH WHAT A NIGHT!)"
                   }
                
    try: 
        return lookup_track[track] 
    except:
        return track




    
if __name__ == '__main__':
    main()