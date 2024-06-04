from flask import Flask, redirect, request, render_template, send_file
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from youtubesearchpython import VideosSearch
from pytube import YouTube

app = Flask(__name__)

# Spotify API settings
SPOTIFY_CLIENT_ID = 'b8c62d7f719844ab922838826e949b70'
SPOTIFY_CLIENT_SECRET = '1034811201c54426b4dec84b1a05cf48'
SPOTIFY_REDIRECT_URI = 'http://localhost:5000/callback'

# YouTube Data API settings
YOUTUBE_API_KEY = 'AIzaSyCMM1br-jLz_roZk_MI4QhGqiU-TDOCYxs'

# Directory to save MP3 files
DOWNLOAD_DIR = 'downloads'

# Spotify authentication
scope = "user-library-read"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                                               client_secret=SPOTIFY_CLIENT_SECRET,
                                               redirect_uri=SPOTIFY_REDIRECT_URI,
                                               scope=scope))

# Function to get liked tracks from Spotify
def get_liked_tracks():
    results = sp.current_user_saved_tracks()
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks

# Function to search YouTube for a track
def search_youtube(query):
    videos_search = VideosSearch(query, limit=1)
    result = videos_search.result()
    if result['result']:
        return result['result'][0]['link']
    return None

def download_youtube_mp3(url, download_dir):
    yt = YouTube(url)
    stream = yt.streams.filter(only_audio=True).first()
    out_file = stream.download(output_path=download_dir)
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    if os.path.exists(new_file):
        # Append a number to the filename if it already exists
        i = 1
        while os.path.exists(f"{base}_{i}.mp3"):
            i += 1
        new_file = f"{base}_{i}.mp3"
    os.rename(out_file, new_file)
    return new_file


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    auth_url = sp.auth_manager.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    sp.auth_manager.get_access_token(code)
    return redirect('/liked')

@app.route('/liked')
def liked():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    liked_tracks = get_liked_tracks()

    for item in liked_tracks:
        track = item['track']
        track_title = f"{track['name']} {track['artists'][0]['name']}"
        youtube_url = search_youtube(track_title)

        if youtube_url:
            mp3_file = download_youtube_mp3(youtube_url, DOWNLOAD_DIR)
            item['mp3_file'] = mp3_file

    return render_template('liked.html', liked_tracks=liked_tracks)

@app.route('/download/<path:filename>')
def download(filename):
    return send_file(os.path.join(DOWNLOAD_DIR, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
