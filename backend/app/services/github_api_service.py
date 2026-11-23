
import httpx


GITHUB_API = "https://api.github.com"


def get_github_data(owner: str, repo: str, endpoint: str):
    """Fetch data from the GitHub REST API."""

    url = f"{GITHUB_API}/repos/{owner}/{repo}/{endpoint}"

    headers = {
        "Accept": "application/vnd.github+json"
    }

    response = httpx.get(
        url,
        headers=headers,
        params={"state": "all", "per_page": 10},
        timeout=15
    )

    response.raise_for_status()

    return response.json()


def get_repository_issues(owner: str, repo: str):
    issues = get_github_data(owner, repo, "issues")

    # GitHub's issues endpoint also returns pull requests.
    issues = [
        issue for issue in issues
        if "pull_request" not in issue
    ]

    return [
        {
            "number": item["number"],
            "title": item["title"],
            "state": item["state"],
            "user": item["user"]["login"],
            "created_at": item["created_at"],
            "url": item["html_url"]
        }
        for item in issues
    ]


def get_repository_pull_requests(owner: str, repo: str):
    pull_requests = get_github_data(owner, repo, "pulls")

    return [
        {
            "number": item["number"],
            "title": item["title"],
            "state": item["state"],
            "user": item["user"]["login"],
            "created_at": item["created_at"],
            "url": item["html_url"]
        }
        for item in pull_requests
    ]


def get_repository_commits(owner: str, repo: str):
    commits = get_github_data(owner, repo, "commits")

    return [
        {
            "sha": item["sha"][:7],
            "message": item["commit"]["message"],
            "author": (
                item["commit"]["author"]["name"]
                if item["commit"]["author"]
                else "Unknown"
            ),
            "date": item["commit"]["author"]["date"],
            "url": item["html_url"]
        }
        for item in commits
    ]
