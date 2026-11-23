
import re
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

from app.services.search_service import search_repository

from app.services.github_api_service import (
    get_repository_issues,
    get_repository_pull_requests,
    get_repository_commits
)


llm = ChatOllama(
    model="qwen2.5:1.5b",
    temperature=0
)


class AgentState(TypedDict):
    repo_id: str
    owner: str
    name: str
    question: str
    context: list
    github_data: list
    answer: str
    tool: str


# Decide which information is required
def select_tool(state: AgentState):

    question = state["question"].lower()

    # Check for GitHub issue-related questions
    if re.search(r"\b(issues?|bugs?|reported)\b", question):
        return {"tool": "issues"}

    # Check for pull request-related questions
    elif re.search(r"\bpull\s+requests?\b|\bpr\b|\bmerge\b", question):
        return {"tool": "pull_requests"}

    # Check for commit-related questions
    elif re.search(r"\bcommits?\b|\bhistory\b", question):
        return {"tool": "commits"}

    # Otherwise, search repository code
    else:
        return {"tool": "code"}


# Search repository code
def search_code(state: AgentState):

    results = search_repository(
        state["repo_id"],
        state["question"]
    )

    return {"context": results}


# Fetch GitHub information
def fetch_github_data(state: AgentState):

    owner = state["owner"]
    repo = state["name"]
    selected_tool = state["tool"]

    if selected_tool == "issues":
        data = get_repository_issues(owner, repo)

    elif selected_tool == "pull_requests":
        data = get_repository_pull_requests(owner, repo)

    else:
        data = get_repository_commits(owner, repo)

    return {"github_data": data}


# Generate final answer
def generate_answer(state: AgentState):

    if state["tool"] == "code":

        context_text = ""

        for item in state["context"]:
            context_text += (
                f"\nFile: {item['file_path']}\n"
                f"Lines: {item['start_line']}-{item['end_line']}\n"
                f"Code:\n{item['content']}\n"
            )

        if not context_text.strip():
            return {
                "answer": (
                    "I couldn't find relevant code in this repository "
                    "to answer your question. Try asking with more "
                    "specific function names or concepts."
                )
            }

    else:

        context_text = str(state["github_data"])

        if not state["github_data"]:
            return {
                "answer": "No matching GitHub records were found."
            }

    prompt = f"""
You are a GitHub codebase assistant.

Answer the user's question using only the information provided below.

Important instructions:

1. Do not invent functions, files, features, or implementation details.
2. If the provided information does not contain the answer,
   clearly explain what could not be verified.
3. For code questions, explain the actual implementation.
4. Always mention source file paths and line numbers
   when answering code questions.
5. For GitHub questions, mention issue numbers,
   pull request numbers, or commit SHA when relevant.
6. Do not confuse GitHub issues, pull requests,
   commits, and repository source code.

Repository information:

{context_text}

User question:

{state['question']}

Provide a clear and accurate answer.
"""

    response = llm.invoke(prompt)

    return {"answer": response.content}


# Build LangGraph workflow
workflow = StateGraph(AgentState)

workflow.add_node("select_tool", select_tool)
workflow.add_node("search_code", search_code)
workflow.add_node("fetch_github_data", fetch_github_data)
workflow.add_node("generate_answer", generate_answer)

workflow.set_entry_point("select_tool")


workflow.add_conditional_edges(
    "select_tool",
    lambda state: state["tool"],
    {
        "code": "search_code",
        "issues": "fetch_github_data",
        "pull_requests": "fetch_github_data",
        "commits": "fetch_github_data"
    }
)

workflow.add_edge("search_code", "generate_answer")
workflow.add_edge("fetch_github_data", "generate_answer")
workflow.add_edge("generate_answer", END)

agent = workflow.compile()


# Main function called by the API
def ask_repository(
    repo_id: str,
    owner: str,
    name: str,
    question: str
):

    result = agent.invoke({
        "repo_id": repo_id,
        "owner": owner,
        "name": name,
        "question": question,
        "context": [],
        "github_data": [],
        "answer": "",
        "tool": ""
    })

    return {
        "answer": result["answer"],
        "sources": result["context"],
        "tool": result["tool"]
    }
