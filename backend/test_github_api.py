
from app.services.github_api_service import (
    get_repository_issues,
    get_repository_pull_requests,
    get_repository_commits
)

owner = "octocat"
repo = "Hello-World"

print("\n========== ISSUES ==========")
print(get_repository_issues(owner, repo))

print("\n========== PULL REQUESTS ==========")
print(get_repository_pull_requests(owner, repo))

print("\n========== COMMITS ==========")
print(get_repository_commits(owner, repo))
