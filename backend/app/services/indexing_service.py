
import os

from app.services.file_service import filter_repository_files
from app.services.chunking_service import chunk_file
from app.services.security_service import get_safe_file_path


def index_repository_files(repo_path: str):

    files = filter_repository_files(repo_path)

    all_chunks = []

    for file_path in files:

        # Get relative file path
        relative_path = os.path.relpath(
            file_path, repo_path
        ).replace("\\", "/")

        # Validate path before reading the file
        safe_file_path = get_safe_file_path(
            repo_path,
            relative_path
        )

        # Read and create chunks only after validation
        chunks = chunk_file(safe_file_path)

        for chunk in chunks:
            chunk["file_path"] = relative_path

        all_chunks.extend(chunks)

    return {
        "files_indexed": len(files),
        "total_chunks": len(all_chunks),
        "chunks": all_chunks
    }
