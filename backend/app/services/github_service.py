
import os
import asyncio
import shutil

from datetime import datetime

from git import Repo
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.repository import Repository

from app.services.indexing_service import index_repository_files
from app.services.vector_service import store_chunks


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

REPOS_DIR = os.path.join(BASE_DIR, "repos")
os.makedirs(REPOS_DIR, exist_ok=True)


async def clone_repository(repo_url: str, repo_id: str):

    repo_path = os.path.join(REPOS_DIR, repo_id)

    try:
        print("\nSTEP 1: Starting repository clone")

        # Update repository status
        async with AsyncSessionLocal() as db:

            result = await db.execute(
                select(Repository).where(Repository.id == repo_id)
            )

            repository = result.scalar_one_or_none()

            if repository:
                repository.status = "cloning"
                await db.commit()

        # Clone GitHub repository
        cloned_repo = await asyncio.to_thread(
            Repo.clone_from,
            repo_url,
            repo_path,
            depth=1
        )

        print("STEP 2: Repository cloned successfully")

        # Save branch and commit information
        async with AsyncSessionLocal() as db:

            result = await db.execute(
                select(Repository).where(Repository.id == repo_id)
            )

            repository = result.scalar_one_or_none()

            if repository:
                repository.default_branch = cloned_repo.active_branch.name
                repository.commit_sha = cloned_repo.head.commit.hexsha
                repository.status = "indexing"

                await db.commit()

        print("STEP 3: Starting file indexing")

        # Filter files and create chunks
        indexing_result = await asyncio.to_thread(
            index_repository_files,
            repo_path
        )

        print(
            "STEP 4: File indexing completed:",
            indexing_result["files_indexed"],
            "files,",
            indexing_result["total_chunks"],
            "chunks"
        )

        # Generate embeddings and store in ChromaDB
        print("STEP 5: Starting ChromaDB storage")

        stored_chunks = await asyncio.to_thread(
            store_chunks,
            repo_id,
            indexing_result["chunks"]
        )

        print("STEP 6: ChromaDB storage completed:", stored_chunks)

        # Update final repository status
        async with AsyncSessionLocal() as db:

            result = await db.execute(
                select(Repository).where(Repository.id == repo_id)
            )

            repository = result.scalar_one_or_none()

            if repository:
                repository.files_indexed = indexing_result["files_indexed"]
                repository.chunks = stored_chunks
                repository.status = "ready"
                repository.indexed_at = datetime.utcnow()

                await db.commit()

        print("STEP 7: Repository indexing finished successfully\n")

    except Exception as error:

        print("\nINDEXING ERROR:", repr(error))

        # Remove partially cloned repository
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, ignore_errors=True)

        # Update failed status
        async with AsyncSessionLocal() as db:

            result = await db.execute(
                select(Repository).where(Repository.id == repo_id)
            )

            repository = result.scalar_one_or_none()

            if repository:
                repository.status = "failed"
                repository.error = str(error)[:1000]

                await db.commit()
