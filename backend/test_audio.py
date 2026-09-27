import yt_dlp
import tempfile
import os

with tempfile.TemporaryDirectory() as tmpdir:
    ydl_opts = {
        'format': 'ba[ext=m4a]/ba/b',
        'outtmpl': os.path.join(tmpdir, 'test_audio.%(ext)s'),
        'max_filesize': 15 * 1024 * 1024,
        'quiet': False,
    }
    url = 'https://www.youtube.com/watch?v=T-Osaiyy8rk'
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        files = os.listdir(tmpdir)
        print("Downloaded files:", files)
        for f in files:
            p = os.path.join(tmpdir, f)
            print(f"File {f} size: {os.path.getsize(p)} bytes")
    except Exception as e:
        print("Error downloading audio:", e)
