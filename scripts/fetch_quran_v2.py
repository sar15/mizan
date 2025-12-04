import requests
import json
import os
import time

# Configuration
TEST_MODE = False
OUTPUT_FILE = "data/processed/quran_skeleton.json"
TRANSLATION_ID = 20  # Sahih International

def fetch_quran():
    print("Starting Quran Harvest...")
    
    all_verses = []
    
    # Determine range of Surahs
    surah_range = range(1, 3) if TEST_MODE else range(1, 115)
    
    for surah_number in surah_range:
        print(f"Fetching Surah {surah_number}...")
        
        # Quran.com API v4 endpoint
        # We need Arabic (uthmani) and Translation
        # Pagination handling is required for larger Surahs
        
        page = 1
        while True:
            url = f"https://api.quran.com/api/v4/verses/by_chapter/{surah_number}"
            params = {
                "language": "en",
                "words": "false",
                "translations": TRANSLATION_ID,
                "fields": "text_uthmani",
                "page": page,
                "per_page": 50  # Max is usually 50
            }
            
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                verses = data.get("verses", [])
                if not verses:
                    break
                
                for v in verses:
                    # Extract translation
                    translation_text = ""
                    translator_name = "Sahih International" # Default for ID 20
                    
                    if "translations" in v and len(v["translations"]) > 0:
                        translation_text = v["translations"][0]["text"]
                        # resource_name might be available, but we know ID 20 is Sahih International
                    
                    verse_obj = {
                        "id": v["verse_key"],
                        "surah_number": surah_number,
                        "surah_name": "", # API doesn't give name in verses endpoint easily, can map later or ignore for now
                        "ayah_number": v["verse_number"],
                        "arabic": v.get("text_uthmani", ""),
                        "translation": translation_text,
                        "translator": translator_name
                    }
                    all_verses.append(verse_obj)
                
                pagination = data.get("pagination", {})
                if pagination.get("next_page") is None:
                    break
                
                page += 1
                time.sleep(0.2) # Rate limit politeness
                
            except Exception as e:
                print(f"Error fetching Surah {surah_number} page {page}: {e}")
                break
                
    # Save to file
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_verses, f, indent=2, ensure_ascii=False)
        
    print(f"Harvest Complete. Saved {len(all_verses)} verses to {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_quran()
