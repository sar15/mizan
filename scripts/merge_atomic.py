import json
import os
import re

# Configuration
SKELETON_FILE = "data/processed/quran_skeleton.json"
TAFSIR_DIR = "data/kaggle-quran-tafsir/data/quran"
OUTPUT_FILE = "data/processed/master_quran_atomic.json"

def clean_html(raw_html):
    if not raw_html:
        return ""
    # Remove HTML tags
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    # Replace HTML entities if any (basic ones)
    cleantext = cleantext.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"')
    return cleantext.strip()

def merge_atomic():
    print("Starting Atomic Merger...")
    
    # Load Skeleton
    if not os.path.exists(SKELETON_FILE):
        print(f"Error: Skeleton file {SKELETON_FILE} not found.")
        return
        
    with open(SKELETON_FILE, "r", encoding="utf-8") as f:
        skeleton = json.load(f)
        
    print(f"Loaded {len(skeleton)} verses from skeleton.")
    
    # Cache for Tafsir data: surah_number -> {verse_key -> tafsir_text}
    tafsir_cache = {}
    
    merged_data = []
    
    for verse in skeleton:
        surah_num = verse["surah_number"]
        verse_key = verse["id"]
        
        # Load Tafsir file if not in cache
        if surah_num not in tafsir_cache:
            tafsir_filename = f"surah_{surah_num:03}.jsonl"
            tafsir_path = os.path.join(TAFSIR_DIR, tafsir_filename)
            
            surah_tafsir_map = {}
            if os.path.exists(tafsir_path):
                print(f"Loading Tafsir: {tafsir_filename}")
                with open(tafsir_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            t_obj = json.loads(line)
                            # Map by verse_key "1:1"
                            v_key = t_obj.get("verse_key")
                            # Prefer text_html and clean it, or fallback to text_plain
                            raw_text = t_obj.get("text_html", "")
                            cleaned_text = clean_html(raw_text)
                            if not cleaned_text:
                                cleaned_text = t_obj.get("text_plain", "")
                            
                            if v_key:
                                surah_tafsir_map[v_key] = cleaned_text
                        except json.JSONDecodeError:
                            continue
            else:
                print(f"Warning: Tafsir file not found for Surah {surah_num}")
            
            tafsir_cache[surah_num] = surah_tafsir_map
            
        # Merge
        tafsir_text = tafsir_cache[surah_num].get(verse_key, "Context Not Available")
        
        verse["tafsir"] = tafsir_text
        verse["tafsir_source"] = "Ibn Kathir (Kaggle Dataset)"
        
        merged_data.append(verse)
        
    # Save Master File
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)
        
    print(f"Merger Complete. Saved {len(merged_data)} atomic chunks to {OUTPUT_FILE}")

if __name__ == "__main__":
    merge_atomic()
