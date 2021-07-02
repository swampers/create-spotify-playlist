import argparse
import datetime
import os
import spotipy
import string
import base64
import random
from spotipy.oauth2 import SpotifyOAuth
import logging
from config import *
from PIL import Image, ImageFont, ImageDraw, ImageFilter


#logger = logging.getLogger('update_spotify_playlist_pic')
#logging.basicConfig(level='DEBUG')


def get_args():
    parser = argparse.ArgumentParser(description='Creates a playlist cover for a given Spotify playlist and uploads it')
    parser.add_argument('-a','--textA', required=False, default='', help='Upper text')
    parser.add_argument('-b','--textB', required=False, default='', help='Lower text')
    parser.add_argument('-p','--playlistID', required=True, default='', help="PlaylistID (from Spotify) to upload")
    return parser.parse_args()


def main():
    
    args = get_args()
    random_pic(args.playlistID, args.textA, args.textB)


def random_pic(playlistID, textA, textB):

    DIR = 'raw/jpegs'
    filecount = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR,name))])
    #print(filecount)
    
    randint = str(random.randrange(1, filecount,1))
    #print(randint)
    my_image = Image.open("raw/jpegs/" + randint.zfill(2) + ".jpg")
    
    image_blurred = my_image.filter(ImageFilter.BoxBlur(25))
    image_blurred.save("tmp.jpeg")
    
    image_blurred = Image.open("tmp.jpeg")
    image_editable = ImageDraw.Draw(image_blurred)

    if textA != '':
        title_font = ImageFont.truetype('raw/fonts/DMSans-Bold.ttf', 300)
        title_text = textA
        image_editable.text((1005,795), title_text, (0,0,0), font=title_font, anchor="ms")
        image_editable.text((1000,800), title_text, (256,256,256), font=title_font, anchor="ms")
        
    if textB != '':
        title_font = ImageFont.truetype('raw/fonts/DMSans-Bold.ttf', (500,300)[textB=="Timewarp" or "-" in textB])
        title_text = textB
        image_editable.text((1005,1295), title_text, (0,0,0), font=title_font, anchor="ms")
        image_editable.text((1000,1300), title_text, (256,256,256), font=title_font, anchor="ms")
            
    image_blurred.save("tmp.jpeg")
    
    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, 
                            client_secret=client_secret,
                            redirect_uri=redirect_uri,
                            scope=scope,
                            username=username))
    with open("tmp.jpeg","rb") as img:
        image_b64 = base64.b64encode(img.read()).decode('utf-8')

    spotify.playlist_upload_cover_image(playlistID, image_b64)
    


    
if __name__ == '__main__':
    main()