#!/usr/bin/env python3
"""Lista polskich glosow z biblioteki ElevenLabs. Klucz: zmienna ELEVENLABS_API_KEY."""
import json, os, urllib.request, urllib.parse
K = os.environ["ELEVENLABS_API_KEY"]
def get(path):
    r = urllib.request.Request("https://api.elevenlabs.io" + path, headers={"xi-api-key": K})
    return json.load(urllib.request.urlopen(r, timeout=60))
seen = {}
for uc in ("narrative_story", "audiobook", "conversational", ""):
    q = {"language": "pl", "page_size": 40, "sort": "usage_character_count_1y"}
    if uc: q["use_cases"] = uc
    try:
        for v in get("/v1/shared-voices?" + urllib.parse.urlencode(q)).get("voices", []):
            seen[v["voice_id"]] = v
    except Exception as e:
        print("ERR", uc, e)
mine = get("/v1/voices?" + urllib.parse.urlencode({"search": "Piotr"})).get("voices", [])
json.dump({"shared": list(seen.values()), "mine": mine}, open("voices_raw.json", "w"), ensure_ascii=False, indent=1)
print("MOJE:", [(v["name"], v["voice_id"]) for v in mine])
for v in sorted(seen.values(), key=lambda x: -x.get("cloned_by_count", 0)):
    print(f'{v["name"][:42]:42s} {v.get("gender","?"):7s} {v.get("age","?"):12s} {v.get("use_case","?"):16s} used={v.get("cloned_by_count",0):6d} {v["voice_id"]} {v["public_owner_id"]}')
