
def chunk_file(file_path: str, chunk_size: int = 100, overlap: int = 20):

    chunks = []

    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        lines = file.readlines()

    start = 0

    while start < len(lines):

        end = min(start + chunk_size, len(lines))

        content = "".join(lines[start:end])

        chunks.append({
            "content": content,
            "file_path": file_path,
            "start_line": start + 1,
            "end_line": end
        })

        if end == len(lines):
            break

        start = end - overlap

    return chunks
