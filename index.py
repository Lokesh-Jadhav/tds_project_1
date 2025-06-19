import requests, json, os
from datetime import datetime, timezone

# Config
BASE_URL = "https://discourse.onlinedegree.iitm.ac.in/"
CATEGORY_SLUG = "courses/tds-kb"
CATEGORY_ID = 34
START_DATE = "2025-01-01"
END_DATE = "2025-04-15"
COOKIES = {k: v for k, v in [x.strip().split("=", 1) for x in """_gcl_au=1.1.1385612938.1748417614; _ga=GA1.1.1744793271.1748417543; _fbp=fb.2.1748417617548.80591645619726440; _ga_5HTJMW67XK=GS2.1.s1749708914$o8$g1$t1749708938$j36$l0$h0; _ga_08NPRH5L4M=GS2.1.s1749726136$o30$g1$t1749726138$j58$l0$h0; _t=KgpmwTZDHr8nWVTeHUh4So1ZAQ5hPNPFLYAhCftDWhM2nACR3oELfZGEYykk9gYYPPZrjI5dJTfhreMHYI6bq5WFtKULue%2BMKTJ4L0iuuyq8dGLzQSLI73snwWAPiJOPnk2tC9%2BiEPw5d9xYBMCZ33xT8KwPxJL%2BMlH%2BwGZHSfOGG6P2PDCn0cIqOaw338I1xYpKwBNSE%2BgsiT799E87JzFUHy%2BQvBWM2MAMHXdjHWeno0EsDY3Of8At2EEXHju5B%2BYErG4F6NnSJbd7D8RlbvW%2BNTXB85rb22YmQa%2Bw9eVnEfMp49gfitt7tZg%3D--X6EiP10Sv6eyfc0A--R9CA9mFAqAT5QjhDCc1aMw%3D%3D; _forum_session=JTEt5XQnq%2FoCqJNPbVZEvpL%2FiwbIExL5ys3kM1IiRQakbh1vTlv2%2BxUgXnAW6m2BPT7l49VmDo%2FThV5r9kQ8RVMnhaK6phCz1lOahYu0%2BXntrEslxRDN1BA21ECuw6EJJGCarw%2FRh9uT8HJuqzP%2FSmEEy2OmiLmAGoyuXrkVkSZZ9B%2FmNXGiZF%2BfYcILz7raUVKjEJ2g8CoJddb9nCtptF6aceibXswKdtGVso9aS9vTctk%2FBsRThY4ngcGG6DZfussQHEWSkHfGTfWzMeSM5j5pAeT%2BwQ%3D%3D--vPLNINwxecZ1Zz4K--S4gCrOo4DNHasu0EyKCz%2Fg%3D%3D""".split(";")]}
OUTPUT_DIR = "all_topics_json"

def fetch_topics():
    start = datetime.fromisoformat(START_DATE).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(END_DATE + "T23:59:59").replace(tzinfo=timezone.utc)
    ids, page = [], 0

    while True:
        r = requests.get(f"{BASE_URL}c/{CATEGORY_SLUG}/{CATEGORY_ID}.json?page={page}", cookies=COOKIES)
        topics = r.json().get("topic_list", {}).get("topics", [])
        if not topics: break
        ids += [t["id"] for t in topics if "created_at" in t and start <= datetime.fromisoformat(t["created_at"].replace("Z", "+00:00")) <= end]
        if not r.json()["topic_list"].get("more_topics_url"): break
        page += 1

    return ids

def save_topic(topic_id):
    r = requests.get(f"{BASE_URL}t/{topic_id}.json", cookies=COOKIES)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(f"{OUTPUT_DIR}/topic_{topic_id}.json", "w") as f:
        json.dump(r.json(), f, indent=2)
    print(f"Saved topic {topic_id}")

if __name__ == "__main__":
    print("Downloading topics...")
    for tid in fetch_topics(): save_topic(tid)
    print("Done.")
