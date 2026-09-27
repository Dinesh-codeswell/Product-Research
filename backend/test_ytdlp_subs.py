import yt_dlp
import tempfile
import os
import glob
import json

with tempfile.TemporaryDirectory() as tmpdir:
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],
        'subtitlesformat': 'vtt/json3/srt/best',
        'outtmpl': os.path.join(tmpdir, '%(id)s.%(ext)s'),
        'quiet': False,
    }
    url = 'https://www.youtube.com/watch?v=T-Osaiyy8rk'
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    files = glob.glob(os.path.join(tmpdir, '*'))
    print("Downloaded subtitle files:", files)
    for f in files:
        size = os.path.getsize(f)
        print(f"File {f} size: {size} bytes")
        with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
            print("Content preview:\n", fp.read()[:500])
