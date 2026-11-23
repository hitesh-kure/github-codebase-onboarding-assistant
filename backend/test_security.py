
from app.services.security_service import get_safe_file_path

repo_path = "repos/test-repository"

print("TEST 1: Safe path")

try:
    result = get_safe_file_path(repo_path, "README.md")
    print("Allowed:", result)

except ValueError as error:
    print("Blocked:", error)


print("\nTEST 2: Unsafe path")

try:
    result = get_safe_file_path(repo_path, "../../secret.txt")
    print("Allowed:", result)

except ValueError as error:
    print("Blocked:", error)
