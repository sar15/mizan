"""
Prepare quran_tafsir.csv by merging The Quran Dataset and Tafsir.
This creates the input file needed for ingest_semantic.py
"""

import pandas as pd
import os

DATA_DIR = "./data"
QURAN_PATH = os.path.join(DATA_DIR, "The Quran Dataset.csv")
TAFSIR_PATH = os.path.join(DATA_DIR, "Tafsir_al-Jalalayn_tafseer.csv")
OUTPUT_PATH = os.path.join(DATA_DIR, "quran_tafsir.csv")

def prepare_data():
    print("Loading datasets...")
    df_quran = pd.read_csv(QURAN_PATH)
    df_tafsir = pd.read_csv(TAFSIR_PATH)
    
    print(f"Quran: {len(df_quran)} rows")
    print(f"Tafsir: {len(df_tafsir)} rows")
    
    # Merge
    if len(df_quran) == len(df_tafsir):
        df_merged = df_quran.copy()
        df_merged['Tafseer'] = df_tafsir['Tafseer']
        
        # Save
        df_merged.to_csv(OUTPUT_PATH, index=False)
        print(f"✅ Created {OUTPUT_PATH}")
        print(f"Total rows: {len(df_merged)}")
    else:
        print("❌ Error: Row count mismatch!")

if __name__ == "__main__":
    prepare_data()
