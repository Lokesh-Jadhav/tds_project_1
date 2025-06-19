import requests
import json




MODEL = "nomic-embed-text:latest"

def load_chunks(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    return [chunk.strip() for chunk in text.split('---') if chunk.strip()]

def embed_chunk(text):
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": text
    })
    if response.status_code == 200:
        return response.json()["embedding"]
    else:
        print("❌ Failed to embed chunk:", response.text)
        return None

def embed_and_save(input_file, output_file):
    chunks = load_chunks(input_file)
    print(f"🔍 Loaded {len(chunks)} chunks from {input_file}")
    with open(output_file, "w", encoding="utf-8") as out:
        for i, chunk in enumerate(chunks, 1):
            embedding = embed_chunk(chunk)
            if embedding:
                out.write(json.dumps({
                    "id": f"chunk_{i}",
                    "text": chunk,
                    "embedding": embedding
                }) + "\n")
                print(f"✅ Embedded chunk {i}")
            else:
                print(f"⚠️ Skipped chunk {i} due to error")

# Run only for Markdown file
embed_and_save("all_markdown_chunked.txt", "all_markdown_embeddings.jsonl")
