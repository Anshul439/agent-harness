from pathlib import Path
import subprocess

from agent.types import ToolSpec

# Absolute path to the project root. Every file operation is restricted to this tree.
ROOT = Path(".").resolve()

MAX_LINES = 200

IGNORED_DIRS = {
    ".venv",
    ".git",
    "__pycache__",
    ".pytest_cache",
}


def _safe_path(path: str) -> Path | str:
    """Resolve a path inside ROOT."""
    resolved = (ROOT / path).resolve()
    if not resolved.is_relative_to(ROOT):
        return f"Error: access denied — '{path}' is outside the project root"
    return resolved


def read_file(path: str):
    """Read the contents of a file."""
    file_path = _safe_path(path)
    if isinstance(file_path, str):
        return file_path

    if not file_path.exists():
        return f"File not found: {path}"

    if not file_path.is_file():
        return f"Not a file: {path}"

    lines = file_path.read_text().splitlines()
    if len(lines) > MAX_LINES:
        preview = "\n".join(lines[:MAX_LINES])
        return f"{preview}\n\n[file truncated — {len(lines)} total lines, showing first {MAX_LINES}]"
    return "\n".join(lines)


def list_files(directory: str = "."):
    """List files in a directory."""
    files = []

    for path in Path(directory).rglob("*"):
        if path.is_file() and not any(
            ignored in path.parts for ignored in IGNORED_DIRS
        ):
            files.append(str(path))

    return "\n".join(files)


def search_files(query: str, extension: str = ""):
    """Search file contents and include nearby context."""
    context = 2
    max_matches = 50

    blocks = []

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(ignored in path.parts for ignored in IGNORED_DIRS):
            continue
        if extension and path.suffix != extension:
            continue

        try:
            lines = path.read_text().splitlines()
        except (UnicodeDecodeError, OSError):
            continue

        rel = path.relative_to(ROOT)

        # Collect all matching line numbers first, then build non-overlapping blocks.
        hit_lines = [
            i for i, line in enumerate(lines, 1)
            if query.lower() in line.lower()
        ]

        # Merge hits whose context windows overlap into a single block.
        merged_ranges = []
        for hit in hit_lines:
            start = max(0, hit - 1 - context)
            end = min(len(lines), hit + context)
            if merged_ranges and start <= merged_ranges[-1][1]:
                merged_ranges[-1] = (merged_ranges[-1][0], end, merged_ranges[-1][2] + [hit])
            else:
                merged_ranges.append((start, end, [hit]))

        for start, end, hits in merged_ranges:
            context_lines = []
            for i, ctx_line in enumerate(lines[start:end], start + 1):
                prefix = "→ " if i in hits else "  "
                context_lines.append(f"{rel}:{i}:{prefix}{ctx_line}")
            blocks.append("\n".join(context_lines))

            if len(blocks) >= max_matches:
                break

        if len(blocks) >= max_matches:
            break

    if not blocks:
        hint = f" with extension '{extension}'" if extension else ""
        return f"No matches found for: {query}{hint}"

    output = "\n\n".join(blocks)
    if len(blocks) == max_matches:
        output += f"\n\n[results truncated — showing {max_matches} matches. Try a more specific query or filter by extension.]"
    return output


def edit_file(path: str, old_text: str, new_text: str):
    file_path = _safe_path(path)
    if isinstance(file_path, str):
        return file_path

    if not file_path.exists():
        return f"File not found: {path}"

    if not file_path.is_file():
        return f"Not a file: {path}"

    if old_text == new_text:
        return f"Error: old_text and new_text are identical — no change would be made"

    text = file_path.read_text()

    if old_text not in text:
        return f"Text not found in {path}"

    new_text_content = text.replace(old_text, new_text, 1)
    file_path.write_text(new_text_content)

    return f"Successfully edited {path}"


def create_file(path: str, content: str):
    file_path = _safe_path(path)
    if isinstance(file_path, str):
        return file_path

    if file_path.exists():
        return f"Error: '{path}' already exists. Use edit_file to modify existing files."

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    return f"Created {path}"


def run_tests():
    result = subprocess.run(
        ["pytest", "-q"],
        cwd=ROOT,
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
        description=(
            "Search repository files for a text query. "
            "Returns matching lines with 2 lines of context above and below. "
            "Optionally filter by file extension (e.g. '.py', '.md')."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text to search for.",
                },
                "extension": {
                    "type": "string",
                    "description": "Only search files with this extension, e.g. '.py'. Omit to search all files.",
                },
            },
            "required": ["query"],
        },
        func=search_files,
    ),

    "create_file": ToolSpec(
        name="create_file",
        description="Create a new file with the given content. Fails if the file already exists.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path of the file to create.",
                },
                "content": {
                    "type": "string",
                    "description": "Full content to write into the new file.",
                },
            },
            "required": ["path", "content"],
        },
        func=create_file,
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