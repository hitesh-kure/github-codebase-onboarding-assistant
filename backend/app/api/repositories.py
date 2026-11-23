
import stat

import asyncio
from urllib.parse import urlparse

import traceback

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.repository import Repository
from app.services.github_service import clone_repository, REPOS_DIR
from app.agents.repository_agent import ask_repository

import os
import shutil

from app.services.vector_service import delete_repository_vectors

import json

from fastapi.responses import StreamingResponse


router = APIRouter(
    prefix="/api/repos",
    tags=["Repositories"]
)


class RepositoryCreate(BaseModel):
    url: HttpUrl


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=10)


@router.post("")
async def create_repository(
    repo_data: RepositoryCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    repo_url = str(repo_data.url)
    parsed_url = urlparse(repo_url)

    if parsed_url.hostname != "github.com":
        raise HTTPException(
            status_code=400,
            detail="Only GitHub repository URLs are allowed"
        )

    parts = parsed_url.path.strip("/").removesuffix(".git").split("/")

    if len(parts) != 2 or not all(parts):
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub repository URL"
        )

    owner, name = parts

    repository = Repository(
        url=repo_url,
        owner=owner,
        name=name,
        status="pending"
    )

    db.add(repository)
    await db.commit()
    await db.refresh(repository)

    background_tasks.add_task(
        clone_repository,
        repository.url,
        repository.id
    )

    return {
        "message": "Repository registered. Cloning started.",
        "id": repository.id,
        "url": repository.url,
        "owner": repository.owner,
        "name": repository.name,
        "status": repository.status
    }


@router.get("")
async def list_repositories(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Repository)
    )

    repositories = result.scalars().all()

    return repositories


@router.get("/{repo_id}")
async def get_repository(
    repo_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id)
    )

    repository = result.scalar_one_or_none()

    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found"
        )

    return repository



@router.post("/{repo_id}/chat")
async def chat_with_repository(
    repo_id: str,
    chat_data: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id)
    )

    repository = result.scalar_one_or_none()

    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found"
        )

    if repository.status != "ready":
        raise HTTPException(
            status_code=400,
            detail="Repository is not ready for questions yet"
        )

    try:
        agent_result = await asyncio.to_thread(
            ask_repository,
            repo_id,
            repository.owner,
            repository.name,
            chat_data.question
        )

        return {
            "repository": repository.name,
            "question": chat_data.question,
            "tool_used": agent_result["tool"],
            "answer": agent_result["answer"],
            "sources": agent_result["sources"]
        }

    except Exception as error:
        print("CHAT AGENT ERROR:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to generate repository answer"
        )


@router.post("/{repo_id}/chat/stream")
async def chat_with_repository_stream(
    repo_id: str,
    chat_data: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id)
    )

    repository = result.scalar_one_or_none()

    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found"
        )

    if repository.status != "ready":
        raise HTTPException(
            status_code=400,
            detail="Repository is not ready for questions yet"
        )

    async def event_stream():

        try:
            yield f"data: {json.dumps({'status': 'Searching repository...'})}\n\n"

            agent_result = await asyncio.to_thread(
                ask_repository,
                repo_id,
                repository.owner,
                repository.name,
                chat_data.question
            )

            if agent_result["tool"] == "code":
                yield f"data: {json.dumps({'status': 'Code search completed'})}\n\n"
            else:
                yield f"data: {json.dumps({'status': 'GitHub data fetched'})}\n\n"

            yield f"data: {json.dumps({'status': 'Generating answer...'})}\n\n"

            response_data = {
                "status": "completed",
                "tool_used": agent_result["tool"],
                "answer": agent_result["answer"],
                "sources": agent_result["sources"]
            }

            yield f"data: {json.dumps(response_data)}\n\n"

        except Exception as error:
            print("STREAM ERROR:", repr(error))

            error_data = {
                "status": "error",
                "message": "Unable to generate repository answer"
            }

            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

def handle_remove_readonly(func, path, error):
    os.chmod(path, stat.S_IWRITE)
    func(path)



@router.delete("/{repo_id}")
async def delete_repository(
    repo_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id)
    )

    repository = result.scalar_one_or_none()

    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found"
        )

    repo_path = os.path.join(REPOS_DIR, repo_id)

    try:
        # Delete cloned repository folder
        if os.path.exists(repo_path):
            shutil.rmtree(
                repo_path,
                onexc=handle_remove_readonly
            )

        # Delete ChromaDB collection
        await asyncio.to_thread(
            delete_repository_vectors,
            repo_id
        )

        # Delete SQLite record
        await db.delete(repository)
        await db.commit()

        return {
            "message": "Repository and its data deleted successfully",
            "id": repo_id
        }

    except Exception as error:
        await db.rollback()

        print("DELETE ERROR:", repr(error))
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail="Unable to delete repository completely"
        )

