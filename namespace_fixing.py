import json

def prefix_ids(input_file, output_file, prefix):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            record = json.loads(line)
            record['id'] = f"{prefix}_{record['id']}"
            outfile.write(json.dumps(record) + '\n')
    print(f"✅ Prefixed IDs with '{prefix}' and saved to {output_file}")

# Example usage:
prefix_ids("all_markdown_embeddings.jsonl", "all_markdown_embeddings_prefixed.jsonl", "markdown")
prefix_ids("all_json_embeddings.jsonl", "all_json_embeddings_prefixed.jsonl", "json")
