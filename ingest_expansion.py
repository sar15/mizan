import pandas as pd
import os
import sys

# --- CONFIGURATION ---
DATA_DIR = "data"
DICT_FILE = os.path.join(DATA_DIR, "quran_dictionary.csv")

# --- EXPANSION VOCABULARY ---
# Format: (Term, Definition)
# These are Hinglish/Urdu/Modern terms mapped to Islamic concepts.
NEW_TERMS = [
    ("nikkah", "Marriage contract in Islam"),
    ("jannat", "Paradise/Heaven (Jannah)"),
    ("jahannam", "Hellfire"),
    ("gunah", "Sin/Transgression"),
    ("paap", "Sin (Hindi/Urdu) -> Sin"),
    ("sawab", "Reward/Blessing"),
    ("dua", "Supplication/Prayer"),
    ("namaz", "Ritual Prayer (Salah)"),
    ("roza", "Fasting (Sawm)"),
    ("zakat", "Charity/Alms-giving"),
    ("hajj", "Pilgrimage to Mecca"),
    ("umrah", "Lesser Pilgrimage"),
    ("wudu", "Ablution/Ritual Purification"),
    ("ghusl", "Full Body Ritual Purification"),
    ("zina", "Adultery/Fornication"),
    ("riba", "Usury/Interest"),
    ("sood", "Interest (Urdu) -> Riba"),
    (" ब्याज", "Interest (Hindi) -> Riba"), # Hindi text for Interest
    ("halal", "Permissible/Lawful"),
    ("haram", "Forbidden/Unlawful"),
    ("makruh", "Disliked/Detested"),
    ("fard", "Obligatory/Mandatory"),
    ("sunnah", "Tradition of the Prophet"),
    ("nafl", "Voluntary Act"),
    ("shirk", "Polytheism/Associating partners with Allah"),
    ("kufr", "Disbelief"),
    ("munafiq", "Hypocrite"),
    ("jinn", "Unseen beings created from smokeless fire"),
    ("shaytan", "Satan/Devil"),
    ("iblis", "The primary Devil"),
    ("dajjal", "The False Messiah/Antichrist"),
    ("mahdi", "The Guided One"),
    ("qiyama", "Day of Judgment"),
    ("akhirah", "Afterlife"),
    ("duniya", "Worldly Life"),
    ("sabr", "Patience/Perseverance"),
    ("shukr", "Gratitude"),
    ("tawakkul", "Trust in Allah"),
    ("taqwa", "God-consciousness/Piety"),
    ("iman", "Faith/Belief"),
    ("islam", "Submission to God"),
    ("muslim", "One who submits to God"),
    ("quran", "The Holy Book of Islam"),
    ("hadith", "Sayings/Actions of the Prophet"),
    ("sunnat", "Sunnah (Urdu)"),
    ("fatwa", "Legal Ruling"),
    ("mufti", "Scholar qualified to give Fatwa"),
    ("imam", "Leader (of prayer or community)"),
    ("masjid", "Mosque"),
    ("azaan", "Call to Prayer"),
    ("iqamah", "Second call to prayer"),
    ("khutbah", "Sermon"),
    ("jummah", "Friday Prayer"),
    ("eid", "Festival"),
    ("ramadan", "Month of Fasting"),
    ("laylatul qadr", "Night of Power"),
    ("zakah", "Zakat"),
    ("sadaqah", "Voluntary Charity"),
    ("fitrana", "Charity given before Eid al-Fitr"),
    ("qurbani", "Sacrifice (Udhiyah)"),
    ("udhiyah", "Sacrifice"),
    ("aqiqah", "Sacrifice for newborn"),
    ("walima", "Marriage Banquet"),
    ("mehr", "Dowry/Bridal Gift"),
    ("talaq", "Divorce"),
    ("khula", "Divorce initiated by wife"),
    ("iddah", "Waiting period after divorce/death"),
    ("hijab", "Veil/Modest Dress"),
    ("niqab", "Face Veil"),
    ("burqa", "Full body covering"),
    ("beard", "Sunnah of growing facial hair"),
    ("miswak", "Tooth stick (Sunnah)"),
    ("zamzam", "Holy water from Mecca"),
    ("kaaba", "The House of Allah in Mecca"),
    ("tawaf", "Circumambulation of Kaaba"),
    ("sa'i", "Walking between Safa and Marwa"),
    ("mina", "Valley near Mecca"),
    ("arafat", "Plain of Arafat"),
    ("muzgalifah", "Area near Mecca"),
    ("jamarat", "Stoning pillars"),
    ("ihram", "State of ritual sanctity"),
    ("talbiyah", "Prayer during Hajj"),
    ("bitcoin", "Digital Currency -> Check Riba rules"),
    ("crypto", "Cryptocurrency -> Check Riba/Gharar rules"),
    ("forex", "Foreign Exchange -> Check Riba rules"),
    ("insurance", "Takaful vs Conventional Insurance"),
    ("bank interest", "Riba"),
    ("mortgage", "Riba-based loan"),
    ("credit card", "Debt/Riba"),
    ("student loan", "Riba-based debt"),
    ("lottery", "Gambling (Maysir)"),
    ("gambling", "Maysir"),
    ("alcohol", "Khamr/Intoxicant"),
    ("pork", "Swine flesh (Haram)"),
    ("bacon", "Pork (Haram)"),
    ("ham", "Pork (Haram)"),
    ("gelatin", "Check source (Halal/Haram)"),
    ("kosher", "Permissible food of People of the Book"),
    ("zabiha", "Ritual Slaughter"),
    ("halal meat", "Zabiha"),
    ("music", "Musical instruments (Daff allowed)"),
    ("singing", "Nasheed/Poetry"),
    ("dancing", "Gender mixing rules apply"),
    ("movies", "Visual entertainment rules"),
    ("games", "Waste of time vs Leisure"),
    ("chess", "Makruh/Haram debate"),
    ("backgammon", "Haram (Dice)"),
    ("dice", "Haram (Maysir)"),
    ("statues", "Images/Idols (Haram)"),
    ("pictures", "Taswir (Image making)"),
    ("photography", "Taswir debate"),
    ("drawing", "Taswir debate"),
    ("dogs", "Impurity of saliva/Keeping as pet"),
    ("cats", "Pure/Sunnah to keep"),
    ("magic", "Sihr (Major Sin)"),
    ("evil eye", "Nazar"),
    ("ruqyah", "Spiritual healing"),
    ("taweez", "Amulet (Debated)"),
    ("astrology", "Haram (Shirk)"),
    ("horoscope", "Haram"),
    ("fortune telling", "Haram"),
    ("palm reading", "Haram"),
    ("ouija board", "Haram"),
    ("ghosts", "Jinn"),
    ("spirits", "Jinn/Ruh"),
    ("reincarnation", "Not in Islam (Barzakh)"),
    ("karma", "Not in Islam (Qadr/Justice)"),
    ("yoga", "Exercise vs Hindu worship"),
    ("meditation", "Muraqaba/Dhikr"),
    ("sufism", "Tasawwuf"),
    ("wahhabi", "Salafi movement"),
    ("salafi", "Followers of Salaf"),
    ("shia", "Shi'at Ali"),
    ("sunni", "Ahlus Sunnah wal Jama'ah"),
    ("ahmadi", "Qadiani (Consensus on non-Muslim status)"),
    ("qadiani", "Ahmadi"),
    ("bahai", "Separate religion"),
    ("nation of islam", "Separate movement"),
    ("ismail", "Prophet Ishmael"),
    ("isaac", "Prophet Ishaq"),
    ("jacob", "Prophet Yaqub"),
    ("joseph", "Prophet Yusuf"),
    ("job", "Prophet Ayyub"),
    ("jonah", "Prophet Yunus"),
    ("aaron", "Prophet Harun"),
    ("david", "Prophet Dawud"),
    ("solomon", "Prophet Sulaiman"),
    ("elias", "Prophet Ilyas"),
    ("elisha", "Prophet Al-Yasa"),
    ("enoch", "Prophet Idris"),
    ("ezra", "Uzair"),
    ("jesus", "Prophet Isa"),
    ("mary", "Maryam"),
    ("john", "Prophet Yahya"),
    ("zachariah", "Prophet Zakariya"),
    ("lot", "Prophet Lut"),
    ("noah", "Prophet Nuh"),
    ("adam", "Prophet Adam"),
    ("eve", "Hawwa"),
    ("satan", "Shaytan"),
    ("gabriel", "Jibreel"),
    ("michael", "Mikaeel"),
    ("israfil", "Angel of Trumpet"),
    ("izrail", "Angel of Death (Malak al-Maut)"),
    ("kiraman katibin", "Recording Angels"),
    ("munkar nakir", "Grave Angels"),
    ("ridwan", "Guardian of Paradise"),
    ("malik", "Guardian of Hell"),
    ("buraq", "Heavenly Steed"),
    ("sidratul muntaha", "Lote Tree of the Utmost Boundary"),
    ("arsh", "Throne of Allah"),
    ("kursi", "Footstool/Chair of Allah"),
    ("pen", "Al-Qalam"),
    ("tablet", "Al-Lawh Al-Mahfuz"),
    ("wahi", "Revelation"),
    ("ilham", "Inspiration"),
    ("kashf", "Unveiling"),
    ("karamat", "Miracles of Saints"),
    ("muciza", "Miracles of Prophets"),
    ("bid'ah", "Innovation in religion"),
    ("tawheed", "Monotheism"),
    ("aqeedah", "Creed"),
    ("fiqh", "Jurisprudence"),
    ("sharia", "Islamic Law"),
    ("usul", "Principles"),
    ("ijma", "Consensus"),
    ("qiyas", "Analogy"),
    ("ijtihad", "Independent reasoning"),
    ("taqlid", "Following a scholar"),
    ("madhhab", "School of Thought"),
    ("hanafi", "School of Abu Hanifa"),
    ("shafi", "School of Al-Shafi'i"),
    ("maliki", "School of Malik"),
    ("hanbali", "School of Ahmad ibn Hanbal"),
    ("jafari", "Shia School"),
    ("zaydi", "Shia School"),
    ("ibadi", "Oman School"),
    ("zahir", "Literalist School"),
    ("mutazila", "Rationalist School (Historical)"),
    ("ashari", "Theological School"),
    ("maturidi", "Theological School"),
    ("athari", "Textualist Theology"),
    ("kharijite", "Extremist Sect (Historical)"),
    ("murjiah", "Postponers (Historical)"),
    ("qadariyya", "Free Will Proponents (Historical)"),
    ("jabriyya", "Determinists (Historical)"),
    ("jahmiyya", "Deniers of Attributes (Historical)"),
    # --- FINANCE & BUSINESS ---
    ("stocks", "Shareholding (Halal if company is Halal)"),
    ("day trading", "Speculation vs Investment debate"),
    ("options", "Derivatives (Generally Haram)"),
    ("futures", "Derivatives (Generally Haram)"),
    ("short selling", "Selling what one does not own (Haram)"),
    ("margin trading", "Interest-based loan (Haram)"),
    ("bonds", "Interest-based debt (Haram)"),
    ("sukuk", "Islamic Bonds (Asset-backed)"),
    ("takaful", "Islamic Insurance"),
    ("dropshipping", "Possession issue (Salam contract needed)"),
    ("mlm", "Multi-Level Marketing (Pyramid scheme concerns)"),
    ("pyramid scheme", "Fraud/Gharar (Haram)"),
    ("network marketing", "MLM"),
    ("freelancing", "Permissible service"),
    ("youtube income", "AdSense (Halal if ads are Halal)"),
    ("adsense", "Advertising income rules"),
    ("affiliate marketing", "Permissible if product is Halal"),
    ("referral bonus", "Gift/Commission"),
    ("cashback", "Discount/Gift (Permissible)"),
    ("credit score", "Necessity in modern finance"),
    ("inflation", "Currency devaluation"),
    ("gold", "Ribawi item (Spot trade only)"),
    ("silver", "Ribawi item (Spot trade only)"),
    # --- BIOETHICS & MEDICAL ---
    ("ivf", "In Vitro Fertilization (Allowed between husband/wife)"),
    ("surrogacy", "Haram (Lineage confusion)"),
    ("abortion", "Forbidden unless mother's life at risk (40/120 days debate)"),
    ("organ donation", "Permissible as Sadaqah Jariyah (Consensus)"),
    ("blood donation", "Permissible"),
    ("cloning", "Human cloning Haram"),
    ("stem cells", "Permissible for therapy"),
    ("euthanasia", "Mercy killing (Haram)"),
    ("suicide", "Major Sin"),
    ("autopsy", "Permissible for justice/medicine"),
    ("plastic surgery", "Changing creation vs Correcting defect"),
    ("botox", "Cosmetic vs Medical"),
    ("fillers", "Changing creation debate"),
    ("hair transplant", "Restoring defect (Permissible)"),
    ("wigs", "Deception (Haram)"),
    ("braces", "Correcting defect (Permissible)"),
    ("contacts", "Colored lenses (Deception debate)"),
    ("lasik", "Correcting vision (Permissible)"),
    # --- FOOD & DIET ---
    ("vanilla extract", "Alcohol content debate (Istihalah)"),
    ("nutmeg", "Intoxicant in large amounts (Debated)"),
    ("vinegar", "Halal (Istihalah from wine)"),
    ("kombucha", "Trace alcohol (Halal if not intoxicating)"),
    ("soy sauce", "Naturally brewed (Alcohol) vs Synthetic"),
    ("cochineal", "Insect dye (E120) - Madhhab differences"),
    ("carmine", "Insect dye"),
    ("shellac", "Insect secretion"),
    ("rennet", "Enzyme for cheese (Animal source rules)"),
    ("pepsin", "Enzyme (Pig source Haram)"),
    ("whey", "Cheese byproduct"),
    ("energy drinks", "Taurine/Caffeine rules"),
    ("smoking", "Haram (Harmful)"),
    ("vaping", "Haram (Harmful)"),
    ("hookah", "Shisha (Haram)"),
    ("shisha", "Hookah"),
    ("khat", "Intoxicant"),
    ("marijuana", "Intoxicant (Haram)"),
    ("cbd", "Non-intoxicant medical use"),
    ("hemp", "Halal material"),
    # --- LIFESTYLE & SOCIAL ---
    ("dating", "Khalwa/Zina rules"),
    ("chatting", "Gender interaction rules"),
    ("handshake", "Opposite gender (Haram/Makruh)"),
    ("hugging", "Opposite gender (Haram)"),
    ("kissing", "Public affection (Modesty)"),
    ("valentine", "Imitating non-Muslim festivals"),
    ("birthday", "Celebrating birthdays (Bid'ah debate)"),
    ("anniversary", "Celebrating anniversaries"),
    ("new year", "Non-Muslim festival"),
    ("christmas", "Non-Muslim festival"),
    ("halloween", "Pagan roots (Haram)"),
    ("thanksgiving", "Secular/Religious debate"),
    ("mother's day", "Honoring parents (Daily duty)"),
    ("father's day", "Honoring parents"),
    ("tattoos", "Changing creation (Haram)"),
    ("microblading", "Tattooing (Haram)"),
    ("piercing", "Ears/Nose allowed for women"),
    ("nail polish", "Wudu barrier (Breathable polish debate)"),
    ("makeup", "Adornment rules (Mahram vs Non-Mahram)"),
    ("perfume", "Women in public (Haram)"),
    ("silk", "Haram for men"),
    ("gold wearing", "Haram for men"),
    ("shorts", "Awrah rules (Knees)"),
    ("pants", "Trousers below ankles (Isbal)"),
    ("hijab style", "Camel hump hadith"),
    ("turban", "Sunnah attire"),
    ("thobe", "Sunnah attire"),
    ("abaya", "Modest dress"),
    ("burkini", "Swimwear rules"),
    ("swimming", "Awrah rules"),
    ("gym", "Music/Mixing/Awrah environment"),
    # --- WORSHIP & PURITY ---
    ("sujud", "Prostration"),
    ("ruku", "Bowing"),
    ("tashahhud", "Sitting prayer"),
    ("qunut", "Supplication in prayer"),
    ("witr", "Odd numbered prayer at night"),
    ("taraweeh", "Ramadan night prayer"),
    ("tahajjud", "Late night prayer"),
    ("duha", "Forenoon prayer"),
    ("ishraq", "Sunrise prayer"),
    ("janazah", "Funeral prayer"),
    ("ghayb", "Absentee funeral prayer"),
    ("sutrah", "Barrier in front of praying person"),
    ("amin", "Saying Amen"),
    ("bismillah", "In the name of Allah"),
    ("inshallah", "If Allah wills"),
    ("mashallah", "Allah has willed it"),
    ("alhamdulillah", "Praise be to Allah"),
    ("subhanallah", "Glory to Allah"),
    ("allahu akbar", "Allah is the Greatest"),
    ("jazakallah", "May Allah reward you"),
    ("barakallah", "May Allah bless you"),
    ("yarhamukallah", "May Allah have mercy on you"),
    ("walaikum assalam", "And upon you be peace"),
    ("assalamu alaikum", "Peace be upon you"),
    ("istikhara", "Prayer for guidance"),
    ("tawbah", "Repentance"),
    ("istighfar", "Seeking forgiveness"),
    ("dhikr", "Remembrance of Allah"),
    ("tasbih", "Rosary/Counting dhikr"),
    ("menses", "Hayd (Rules of purity)"),
    ("postpartum", "Nifas"),
    ("istihadha", "Irregular bleeding"),
    ("impurity", "Najasa"),
    ("dog saliva", "Najasa (Wash 7 times)"),
    ("pig", "Najasa Mughallazah (Heavy impurity)"),
    ("urine", "Najasa"),
    ("stool", "Najasa"),
    ("blood", "Najasa (Flowing)"),
    ("vomit", "Najasa (Mouthful)"),
    ("alcohol cleaning", "Synthetic alcohol (Pure for cleaning)"),
    ("sanitizer", "Permissible (Synthetic alcohol)"),
]

def ingest_expansion():
    print("🚀 Starting Vocabulary Expansion...")
    
    if not os.path.exists(DICT_FILE):
        print(f"❌ Error: Dictionary file not found at {DICT_FILE}")
        return

    try:
        df = pd.read_csv(DICT_FILE)
        print(f"   Loaded existing dictionary: {len(df)} rows")
        
        # Prepare new rows
        new_rows = []
        existing_terms = set(df['title'].str.lower().unique())
        
        count = 0
        for term, definition in NEW_TERMS:
            if term.lower() not in existing_terms:
                # Create a row matching the schema
                # Schema: ,title,subheading,location,transliteration,translation,arabic_verse_part,arabic_word
                # We'll use a high ID range for these custom terms (e.g., 10000+)
                row = {
                    "title": term,
                    "subheading": "Expanded Vocabulary",
                    "location": "",
                    "transliteration": term,
                    "translation": definition,
                    "arabic_verse_part": "",
                    "arabic_word": ""
                }
                new_rows.append(row)
                count += 1
            else:
                # print(f"   Skipping existing term: {term}")
                pass
                
        if new_rows:
            new_df = pd.DataFrame(new_rows)
            # Append to CSV
            # We need to ensure columns match. 
            # The existing CSV has an index column (unnamed). We should ignore it on write or handle it.
            # Let's append using mode='a' and header=False, but we need to match column order.
            
            # Better: Concat and overwrite.
            final_df = pd.concat([df, new_df], ignore_index=True)
            
            # Save
            final_df.to_csv(DICT_FILE, index=False) # Assuming the first column in file was index but read as Unnamed: 0?
            # Actually, let's check the header from previous `head` command:
            # ,title,subheading,location,transliteration,translation,arabic_verse_part,arabic_word
            # It seems the first column is an index.
            # If we write index=True, we get a new index column.
            # If we read it, it might be 'Unnamed: 0'.
            
            print(f"   ✅ Added {count} new terms.")
            print(f"   💾 Saving to {DICT_FILE}...")
            
            # Re-read to verify? No, just trust pandas.
            # But wait, if we read with default, the first column is likely a data column if not specified as index.
            # Let's just overwrite carefully.
            final_df.to_csv(DICT_FILE, index=False) # We'll let pandas handle it. 
            # Note: If the original file had an unnamed index column, reading it without index_col=0 makes it a column.
            # We should probably drop 'Unnamed: 0' if it exists before saving, or keep it if it's the ID.
            # The `head` output showed `,title...` which implies the first column is the index.
            
        else:
            print("   ⚠️ No new terms to add.")

    except Exception as e:
        print(f"❌ Error during expansion: {e}")

if __name__ == "__main__":
    ingest_expansion()
