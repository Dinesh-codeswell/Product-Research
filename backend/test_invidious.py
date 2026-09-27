import requests

instances = [
    f"https://invidious.nerdvpn.de/api/v1/captions/T-Osaiyy8rk",
    f"https://inv.nadeko.net/api/v1/captions/T-Osaiyy8rk",
    f"https://yt.artemislena.eu/api/v1/captions/T-Osaiyy8rk",
    f"https://vid.priv.au/api/v1/captions/T-Osaiyy8rk",
    f"https://invidious.privacydev.net/api/v1/captions/T-Osaiyy8rk",
]

for url in instances:
    try:
        r = requests.get(url, timeout=5)
        print(f"Testing {url}: Status {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print("Captions available:", len(data.get("captions", [])))
            for c in data.get("captions", []):
                print("  Caption:", c.get("label"), c.get("language_code"), c.get("url"))
            break
    except Exception as e:
        print(f"Error {url}: {e}")
