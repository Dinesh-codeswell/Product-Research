import requests

instances = [
    "https://inv.tux.pizza",
    "https://invidious.projectsegfau.lt",
    "https://invidious.flokinet.to",
    "https://iv.melmac.space",
    "https://yewtu.be",
    "https://invidious.jing.rocks",
    "https://yt.drgnz.club",
    "https://invidious.einfachzocken.eu",
    "https://invidious.slipfox.xyz",
    "https://inv.vern.cc",
]

video_id = "T-Osaiyy8rk"

for inst in instances:
    try:
        url = f"{inst}/api/v1/captions/{video_id}"
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            caps = r.json().get("captions", [])
            print(f"Success on {inst}: {len(caps)} captions")
            for c in caps:
                if "en" in c.get("label", "").lower() or c.get("language_code") == "en":
                    sub_url = f"{inst}{c.get('url')}"
                    sub_r = requests.get(sub_url, timeout=3)
                    print(f"  Fetching {sub_url}: status {sub_r.status_code}, len: {len(sub_r.text)}")
                    if len(sub_r.text) > 50:
                        print("  SAMPLE:\n", sub_r.text[:200])
                        break
    except Exception as e:
        pass
