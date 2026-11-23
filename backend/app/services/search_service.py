
from app.services.vector_service import get_collection
from app.services.embedding_service import generate_embedding


def search_repository(repo_id: str, question: str, limit: int = 10):

    collection = get_collection(repo_id)

    question_embedding = generate_embedding(question)

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=limit
    )

    search_results = []

    if results["documents"] and results["documents"][0]:

        for index, document in enumerate(results["documents"][0]):

            metadata = results["metadatas"][0][index]
            file_path = metadata["file_path"]

            search_results.append({
                "content": document,
                "file_path": file_path,
                "start_line": metadata["start_line"],
                "end_line": metadata["end_line"],
                "distance": results["distances"][0][index]
            })

    # Prioritize implementation files over test files
    search_results.sort(
        key=lambda item: (
            "test" in item["file_path"].lower(),
            item["distance"]
        )
    )

    return search_results
