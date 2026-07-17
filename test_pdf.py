import fitz

def test_parse():
    doc = fitz.open('ct200_manual.pdf')
    font_sizes = {}
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" in b:
                for l in b["lines"]:
                    for s in l["spans"]:
                        size = round(s["size"], 1)
                        font_sizes[size] = font_sizes.get(size, 0) + len(s["text"])
    
    print("Font sizes by character count:", font_sizes)
    
    # Let's print the first few lines to see their sizes
    lines = []
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" in b:
                for l in b["lines"]:
                    text = "".join([s["text"] for s in l["spans"]]).strip()
                    if not text: continue
                    size = round(l["spans"][0]["size"], 1)
                    lines.append((size, text))
    for size, text in lines[:20]:
        print(f"Size {size}: {text}")

if __name__ == "__main__":
    test_parse()
