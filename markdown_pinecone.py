from pinecone import Pinecone, ServerlessSpec

import json

pc = Pinecone(api_key="pcsk_2vkjf_MWMZSQJDdCnFAFhuKpAq9NA8aKfZneDocPfYncuVhmTX8Gww7Nn4VnemDMEVzVu")  # Replace with your key
index = pc.Index("pcdata")    # Make sure the index exists

def upload_jsonl_to_pinecone(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        vectors = []
        for line in f:
            record = json.loads(line)
            vectors.append((
                record['id'],
                record['embedding'],
                {'text': record['text']}  # metadata
            ))
        index.upsert(vectors=vectors)
        print(f"✅ Uploaded {len(vectors)} vectors to Pinecone")

upload_jsonl_to_pinecone("all_markdown_embeddings_prefixed.jsonl")
