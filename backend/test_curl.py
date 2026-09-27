from curl_cffi import requests
import re
import json

session = requests.Session(impersonate="chrome124")

video_id = "T-Osaiyy8rk"
watch_url = f"https://www.youtube.com/watch?v={video_id}"
resp = session.get(watch_url)
print("Watch page status with curl-cffi chrome124:", resp.status_code)

player_match = re.search(r'ytInitialPlayerResponse\s*=\s*({.+?});', resp.text)
if player_match:
    player_data = json.loads(player_match.group(1))
    captions = player_data.get('captions', {}).get('playerCaptionsTracklistRenderer', {}).get('captionTracks', [])
    print(f"Found {len(captions)} caption tracks:")
    for track in captions:
        base_url = track.get("baseUrl")
        print("Track lang:", track.get("languageCode"))
        print("Base URL:", base_url[:80])
        # Try fetching timedtext directly with curl-cffi impersonating chrome124
        sub_resp = session.get(base_url)
        print("Timedtext status with curl-cffi chrome124:", sub_resp.status_code)
        if sub_resp.status_code == 200:
            print("SUCCESS!!!! Subtitle text length:", len(sub_resp.text))
            print("Content sample:\n", sub_resp.text[:400])
            break
        else:
            print("Failed content preview:", sub_resp.text[:200])
