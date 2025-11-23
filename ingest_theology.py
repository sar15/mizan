import pdfplumber
import re
import json
import os

class TheologicalParser:
    def __init__(self):
        # Regex for Q&A bullets (e.g., "Q:", "Question:", "1.", "•")
        self.qa_regex = re.compile(r"^(Q:|Question:|A:|Answer:|\d+\.|•|-)\s+(.*)", re.IGNORECASE)
        # Regex for Headers (All Caps or specific keywords)
        self.header_regex = re.compile(r"^(SURAH|CHAPTER|SECTION|TOPIC)\s+.*|^[A-Z\s]{4,}$")

    def parse_pdf(self, pdf_path):
        """
        Parses a PDF to extract theological units with layout awareness.
        """
        print(f"--- Parsing {pdf_path} ---")
        units = []
        current_header = "General"
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 1. Identify Headers
                    if self.header_regex.match(line):
                        current_header = line
                        print(f"Found Header: {current_header}")
                        continue
                    
                    # 2. Identify Q&A or Bullets
                    qa_match = self.qa_regex.match(line)
                    if qa_match:
                        marker, content = qa_match.groups()
                        unit_type = "question" if marker.lower().startswith('q') else "answer" if marker.lower().startswith('a') else "point"
                        
                        units.append({
                            "text": content.strip(),
                            "type": unit_type,
                            "parent_header": current_header,
                            "page_num": page_num,
                            "raw_marker": marker
                        })
                    else:
                        # 3. Standard Text (Evidence/Rule)
                        # If it's a continuation or a rule
                        units.append({
                            "text": line,
                            "type": "rule/evidence",
                            "parent_header": current_header,
                            "page_num": page_num
                        })
                        
        return units

    def save_units(self, units, output_path="theological_units.json"):
        with open(output_path, "w") as f:
            json.dump(units, f, indent=2)
        print(f"Saved {len(units)} units to {output_path}")

# --- Dummy PDF Generator for Testing ---
def create_dummy_pdf(path="dummy_theology.pdf"):
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(path)
    
    # Page 1: Salah
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 800, "CHAPTER 1: SALAH")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "Q: What is the ruling on missing prayer?")
    c.drawString(100, 730, "A: It is a major sin. The Prophet (SAW) said...")
    c.drawString(100, 710, "• Prayer is the pillar of religion.")
    c.drawString(100, 690, "1. Fajr")
    c.drawString(100, 670, "2. Dhuhr")
    
    c.showPage()
    
    # Page 2: Wudu
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 800, "SECTION: WUDU")
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "Wudu is a prerequisite for Salah.")
    c.drawString(100, 730, "Q: Does sleep break Wudu?")
    c.drawString(100, 710, "A: Yes, deep sleep invalidates Wudu.")
    
    c.save()
    print(f"Created dummy PDF at {path}")

if __name__ == "__main__":
    # 1. Create Dummy Data
    create_dummy_pdf()
    
    # 2. Run Parser
    parser = TheologicalParser()
    units = parser.parse_pdf("dummy_theology.pdf")
    
    # 3. Save Output
    parser.save_units(units)
