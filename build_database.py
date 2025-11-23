import sqlite3
import pandas as pd
import json
import os
import sys

DB_PATH = "data/mizan_core.db"
QURAN_CSV = "data/The Quran Dataset.csv"
YUSUFALI_CSV = "data/Abdullah_Yusuf_Ali_translation.csv"
TAFSIR_CSV = "data/Tafsir_al-Jalalayn_tafseer.csv"

def create_connection():
    """Create a database connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        print(f"Connected to {DB_PATH}")
    except sqlite3.Error as e:
        print(e)
        sys.exit(1)
    return conn

def create_tables(conn):
    """Create the necessary tables."""
    cursor = conn.cursor()
    
    # Table quran_text
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quran_text (
        id TEXT PRIMARY KEY,
        surah_number INTEGER,
        ayah_number INTEGER,
        arabic_text TEXT,
        translation_sahih TEXT,
        translation_yusufali TEXT,
        theme_tags TEXT
    );
    """)
    
    # Table tafsir_text
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tafsir_text (
        id TEXT PRIMARY KEY,
        verse_id TEXT,
        scholar_name TEXT,
        text TEXT,
        FOREIGN KEY (verse_id) REFERENCES quran_text (id)
    );
    """)
    
    # Table ontology
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ontology (
        concept_key TEXT PRIMARY KEY,
        display_name TEXT,
        primary_verses TEXT,
        description TEXT
    );
    """)
    
    conn.commit()
    print("Tables created successfully.")

def ingest_quran(conn):
    """Ingest Quran text and translations."""
    print("Ingesting Quran text...")
    
    # Read CSVs
    try:
        df_quran = pd.read_csv(QURAN_CSV)
        df_yusufali = pd.read_csv(YUSUFALI_CSV)
    except Exception as e:
        print(f"Error reading CSVs: {e}")
        sys.exit(1)

    # Verify row counts
    if len(df_quran) != 6236:
        print(f"Error: {QURAN_CSV} has {len(df_quran)} rows, expected 6236.")
        sys.exit(1)
    
    # Yusuf Ali might have a different count if it includes Bismillahs or has different structure, 
    # but usually it should align or we need to align it. 
    # Let's check alignment by assuming sequential order if counts match roughly or exactly.
    # The user directive said: "Ensure The Quran Dataset.csv and Tafsir_al-Jalalayn_tafseer.csv both have exactly 6236 rows"
    # It didn't explicitly say Yusuf Ali must be 6236, but we need to merge it.
    
    # Prepare data for insertion
    quran_data = []
    
    # Iterate through the main dataset
    # Columns: surah_no, ayah_no_surah, ayah_ar, ayah_en
    for index, row in df_quran.iterrows():
        surah_num = int(row['surah_no'])
        ayah_num = int(row['ayah_no_surah'])
        verse_id = f"{surah_num}:{ayah_num}"
        arabic = row['ayah_ar']
        sahih = row['ayah_en']
        
        # Get Yusuf Ali translation
        # Assuming Yusuf Ali CSV has 'Surah', 'Ayat', 'Verse'
        # We try to find the matching row. 
        # Optimization: If sorted, we could zip, but let's be safe with lookup or just index matching if strictly parallel.
        # Let's assume strict parallel for now based on typical Quran CSVs, but let's try to match by Surah/Ayah if possible.
        
        yusufali_text = ""
        # Filter df_yusufali
        match = df_yusufali[(df_yusufali['Surah'] == surah_num) & (df_yusufali['Ayat'] == ayah_num)]
        if not match.empty:
            yusufali_text = match.iloc[0]['Verse']
        else:
            # Fallback or log warning? For now, empty string.
            # print(f"Warning: No Yusuf Ali translation for {verse_id}")
            pass

        quran_data.append((
            verse_id,
            surah_num,
            ayah_num,
            arabic,
            sahih,
            yusufali_text,
            None # theme_tags
        ))
        
    cursor = conn.cursor()
    cursor.executemany("""
    INSERT OR REPLACE INTO quran_text (id, surah_number, ayah_number, arabic_text, translation_sahih, translation_yusufali, theme_tags)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, quran_data)
    conn.commit()
    print(f"Inserted {len(quran_data)} rows into quran_text.")

def ingest_tafsir(conn):
    """Ingest Tafsir data."""
    print("Ingesting Tafsir...")
    
    try:
        df_tafsir = pd.read_csv(TAFSIR_CSV)
    except Exception as e:
        print(f"Error reading Tafsir CSV: {e}")
        sys.exit(1)
        
    if len(df_tafsir) != 6236:
        print(f"Error: {TAFSIR_CSV} has {len(df_tafsir)} rows, expected 6236.")
        sys.exit(1)
        
    # Get all verse IDs from quran_text to ensure alignment
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM quran_text ORDER BY surah_number, ayah_number")
    verse_ids = [row[0] for row in cursor.fetchall()]
    
    if len(verse_ids) != 6236:
        print(f"Error: quran_text table has {len(verse_ids)} rows, expected 6236. Cannot map Tafsir sequentially.")
        sys.exit(1)
        
    tafsir_data = []
    scholar = "Al-Jalalayn"
    
    for i, row in df_tafsir.iterrows():
        verse_id = verse_ids[i]
        tafsir_id = f"{verse_id}:{scholar}"
        text = row['Tafseer']
        
        tafsir_data.append((
            tafsir_id,
            verse_id,
            scholar,
            text
        ))
        
    cursor.executemany("""
    INSERT OR REPLACE INTO tafsir_text (id, verse_id, scholar_name, text)
    VALUES (?, ?, ?, ?)
    """, tafsir_data)
    conn.commit()
    print(f"Inserted {len(tafsir_data)} rows into tafsir_text.")

def seed_ontology(conn):
    """Seed the ontology table with golden records."""
    print("Seeding Ontology...")
    
    concepts = [
        ("big_bang", "The Big Bang", json.dumps(["21:30", "41:11", "51:47"]), "Verses referencing the expansion of the universe and the separation of heavens and earth."),
        ("slander_women", "Accusation against Chaste Women (Qadhf)", json.dumps(["24:4", "24:11", "24:23", "49:6"]), "Legal ruling regarding false accusations against chaste women."),
        ("backbiting", "Backbiting (Ghibah)", json.dumps(["49:12", "104:1"]), "Prohibition of speaking ill of others behind their backs."),
        ("wudu_steps", "Steps of Wudu (Ablution)", json.dumps(["5:6"]), "The obligatory steps for performing ablution before prayer."),
        ("interest_riba", "Usury/Interest (Riba)", json.dumps(["2:275", "2:276", "2:278", "3:130"]), "Prohibition of usury and interest in financial transactions.")
    ]
    
    cursor = conn.cursor()
    cursor.executemany("""
    INSERT OR REPLACE INTO ontology (concept_key, display_name, primary_verses, description)
    VALUES (?, ?, ?, ?)
    """, concepts)
    conn.commit()
    print(f"Seeded {len(concepts)} ontology concepts.")

def verify_db(conn):
    """Run verification queries."""
    print("\n--- Verification ---")
    cursor = conn.cursor()
    
    # Verify Arabic text for 24:11
    print("Querying Arabic text for 24:11...")
    cursor.execute("SELECT arabic_text FROM quran_text WHERE id = '24:11'")
    result = cursor.fetchone()
    if result:
        print(f"24:11 Arabic: {result[0][:50]}...") # Print first 50 chars
    else:
        print("Error: 24:11 not found.")
        
    # Verify Ontology for big_bang
    print("Querying Ontology for 'big_bang'...")
    cursor.execute("SELECT display_name, primary_verses FROM ontology WHERE concept_key = 'big_bang'")
    result = cursor.fetchone()
    if result:
        print(f"Big Bang: {result[0]} -> {result[1]}")
    else:
        print("Error: 'big_bang' concept not found.")

def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH) # Start fresh
        
    conn = create_connection()
    create_tables(conn)
    ingest_quran(conn)
    ingest_tafsir(conn)
    seed_ontology(conn)
    verify_db(conn)
    conn.close()
    print("Database built successfully.")

if __name__ == "__main__":
    main()
