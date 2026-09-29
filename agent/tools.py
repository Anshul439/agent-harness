from pathlib import Path
import subprocess

from agent.types import ToolSpec

IGNORED_DIRS = {
    ".venv",
    ".git",
    "__pycache__",
    ".pytest_cache",
}


def read_file(path: str):
    """Read the contents of a file."""
    file_path = Path(path)

    if not file_path.exists():
        return f"File not found: {path}"

    if not file_path.is_file():
        return f"Not a file: {path}"

    return file_path.read_text()


def list_files(directory: str = "."):
    """List files in a directory."""
    files = []

    for path in Path(directory).rglob("*"):
        if path.is_file() and not any(
            ignored in path.parts for ignored in IGNORED_DIRS
        ):
            files.append(str(path))

    return "\n".join(files)


def search_files(query: str):
    matches = []

    for path in Path(".").rglob("*"):
        if (
            path.is_file()
            and not any(
                ignored in path.parts
                for ignored in IGNORED_DIRS
            )
        ):
            try:
                text = path.read_text()
            except (UnicodeDecodeError, OSError):
                continue

            for line_number, line in enumerate(text.splitlines(), 1):
                if query.lower() in line.lower():
                    matches.append(
                        f"{path}:{line_number}: {line.strip()}"
                    )

    if not matches:
        return f"No matches found for: {query}"

    return "\n".join(matches[:100])


def edit_file(path: str, old_text: str, new_text: str):
    file_path = Path(path)

    if not file_path.exists():
        return f"File not found: {path}"

    if not file_path.is_file():
        return f"Not a file: {path}"

    if any(ignored in file_path.parts for ignored in IGNORED_DIRS):
        return f"Access denied: {path}"

    text = file_path.read_text()

    if old_text not in text:
        return f"Text not found in {path}"

    new_text_content = text.replace(old_text, new_text, 1)
    file_path.write_text(new_text_content)

    return f"Successfully edited {path}"


def run_tests():
    result = subprocess.run(
        ["pytest", "-q"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    output = result.stdout + result.stderr

    return output


tools = {
    "read_file": ToolSpec(
        name="read_file",
        description="Read the contents of a file.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path of the file to read."
                }
            },
            "required": ["path"]
        },
        func=read_file,
    ),

    "list_files": ToolSpec(
        name="list_files",
        description="List files in a directory.",
        parameters={
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directory to list files from. Defaults to current directory.",
                }
            },
            "required": [],
        },
        func=list_files,
    ),

    "search_files": ToolSpec(
        name="search_files",
        description="Search repository files for a text query.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text to search for.",
                }
            },
            "required": ["query"],
        },
        func=search_files,
    ),

    "edit_file": ToolSpec(
        name="edit_file",
        description="Replace the first occurrence of old_text with new_text in a file.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path of the file to edit.",
                },
                "old_text": {
                    "type": "string",
                    "description": "Existing text to replace.",
                },
                "new_text": {
                    "type": "string",
                    "description": "Replacement text.",
                },
            },
            "required": ["path", "old_text", "new_text"],
        },
        func=edit_file,
    ),

    "run_tests": ToolSpec(
        name="run_tests",
        description="Run the project's pytest test suite.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        func=run_tests,
    ),
}