
import chromadb

from app.services.embedding_service import generate_embeddings

from chromadb.errors import NotFoundError


CHROMA_DIR = "./chroma_db"

client = chromadb.PersistentClient(path=CHROMA_DIR)


def get_collection(repo_id: str):

    return client.get_or_create_collection(
        name=f"repo_{repo_id}"
    )



def store_chunks(repo_id: str, chunks: list[dict]):

    if not chunks:
        return 0

    collection = get_collection(repo_id)

    batch_size = 64

    # Process chunks in batches of 64
    for start in range(0, len(chunks), batch_size):

        batch = chunks[start:start + batch_size]

        documents = [
            chunk["content"] for chunk in batch
        ]

        embeddings = generate_embeddings(documents)

        ids = [
            f"chunk_{index}"
            for index in range(start, start + len(batch))
        ]

        metadatas = [
            {
                "file_path": chunk["file_path"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"]
            }
            for chunk in batch
        ]

        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        print(
            f"Stored batch: {start + len(batch)} / {len(chunks)} chunks"
        )

    return len(chunks)


def delete_repository_vectors(repo_id: str):
    collection_name = f"repo_{repo_id}"

    try:
        client.delete_collection(name=collection_name)
        print("ChromaDB collection deleted:", collection_name)

    except NotFoundError:
        print("ChromaDB collection does not exist:", collection_name)