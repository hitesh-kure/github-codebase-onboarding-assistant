
import os


ALLOWED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".cpp", ".c", ".cs",
    ".go", ".rs", ".php", ".rb",
    ".html", ".css", ".scss",
    ".json", ".yaml", ".yml",
    ".md", ".sql", ".sh"
}

ALLOWED_FILENAMES = {
    "README",
    "LICENSE",
    "DOCKERFILE",
    "MAKEFILE"
}

IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    "coverage"
}


def filter_repository_files(repo_path: str):

    filtered_files = []

    for root, directories, files in os.walk(repo_path):

        directories[:] = [
            directory for directory in directories
            if directory not in IGNORED_DIRECTORIES
        ]

        for file in files:

            extension = os.path.splitext(file)[1].lower()

            if (
                extension in ALLOWED_EXTENSIONS
                or file.upper() in ALLOWED_FILENAMES
            ):
                file_path = os.path.join(root, file)
                filtered_files.append(file_path)

    return filtered_files
