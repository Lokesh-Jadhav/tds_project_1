import os
import re

INPUT_FILE = "all_json.txt"           # Your large text file
OUTPUT_FILE = "all_json_chunked.txt"
CHUNK_SIZE = 200                      # Words per chunk
CHUNK_OVERLAP = 20                   # Overlap between chunks

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # Collapse multiple whitespaces into one
    return text.strip()

def chunk_text_with_overlap(text, chunk_size, overlap):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i + chunk_size]
        chunks.append(' '.join(chunk))
        i += chunk_size - overlap  # Move index forward by chunk_size - overlap
    return chunks

# Read and clean the input file
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    full_text = clean_text(f.read())

# Chunk the cleaned text
chunks = chunk_text_with_overlap(full_text, CHUNK_SIZE, CHUNK_OVERLAP)

# Write chunks to the output file
with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for i, chunk in enumerate(chunks, 1):
        out.write(f"[Chunk {i}]\n{chunk}\n\n---\n\n")

print(f"✅ Chunked into {len(chunks)} sections → {OUTPUT_FILE}")
