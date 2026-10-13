from agent.tools import read_file, edit_file, create_file, search_files

def test_read_file_blocks_traversal():
    result = read_file("../../.ssh/id_rsa")
    assert result.startswith("Error: access denied")

def test_read_file_blocks_absolute_path():
    result = read_file("/etc/passwd")
    assert result.startswith("Error: access denied")

def test_read_file_allows_project_file():
    result = read_file("example.py")
    assert "def login" in result

def test_edit_file_blocks_traversal():
    result = edit_file("../../some_file.py", "old", "new")
    assert result.startswith("Error: access denied")

def test_edit_file_rejects_noop():
    result = edit_file("example.py", "login failed", "login failed")
    assert "identical" in result

def test_read_file_truncates_large_files(tmp_path, monkeypatch):
    # Point ROOT at tmp_path so our test file is inside the boundary.
    monkeypatch.setattr("agent.tools.ROOT", tmp_path)

    big_file = tmp_path / "big.py"
    big_file.write_text("\n".join(f"line {i}" for i in range(300)))

    result = read_file("big.py")
    assert "file truncated" in result
    assert "300 total lines" in result

def test_read_file_does_not_truncate_small_files(tmp_path, monkeypatch):
    monkeypatch.setattr("agent.tools.ROOT", tmp_path)

    small_file = tmp_path / "small.py"
    small_file.write_text("line 1\nline 2\nline 3")

    result = read_file("small.py")
    assert "truncated" not in result
    assert "line 3" in result

def test_create_file_creates_new_file(tmp_path, monkeypatch):
    monkeypatch.setattr("agent.tools.ROOT", tmp_path)

    result = create_file("new_module.py", "x = 1\n")
    assert result == "Created new_module.py"
    assert (tmp_path / "new_module.py").read_text() == "x = 1\n"

def test_create_file_fails_if_exists(tmp_path, monkeypatch):
    monkeypatch.setattr("agent.tools.ROOT", tmp_path)

    (tmp_path / "existing.py").write_text("old content")
    result = create_file("existing.py", "new content")
    assert result.startswith("Error")
    assert (tmp_path / "existing.py").read_text() == "old content"  # unchanged

def test_create_file_blocks_traversal():
    result = create_file("../../evil.py", "malicious")
    assert result.startswith("Error: access denied")

def test_create_file_creates_missing_parent_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr("agent.tools.ROOT", tmp_path)

    result = create_file("src/utils/helpers.py", "# helpers\n")
    assert result == "Created src/utils/helpers.py"
    assert (tmp_path / "src" / "utils" / "helpers.py").exists()

def test_search_files_shows_context_lines(tmp_path, monkeypatch):
    monkeypatch.setattr("agent.tools.ROOT", tmp_path)

    (tmp_path / "auth.py").write_text("def setup():\n    pass\n\ndef login(user):\n    return True\n")
    result = search_files("def login")

    assert "→" in result
    assert "def setup" in result or "pass" in result


def test_search_files_merges_overlapping_blocks(tmp_path, monkeypatch):
    monkeypatch.setattr("agent.tools.ROOT", tmp_path)

    (tmp_path / "f.py").write_text("login_start\nsome code\nlogin_end\n")
    result = search_files("login")

    assert result.count("f.py:1") == 1
    assert result.count("f.py:3") == 1
    assert "\n\n" not in result


def test_search_files_extension_filter(tmp_path, monkeypatch):
    monkeypatch.setattr("agent.tools.ROOT", tmp_path)

    (tmp_path / "code.py").write_text("def greet(): pass\n")
    (tmp_path / "notes.md").write_text("greet the user\n")

    py_result = search_files("greet", extension=".py")
    md_result = search_files("greet", extension=".md")

    assert "code.py" in py_result
    assert "notes.md" not in py_result
    assert "notes.md" in md_result
    assert "code.py" not in md_result


def test_search_files_no_match_message(tmp_path, monkeypatch):
    monkeypatch.setattr("agent.tools.ROOT", tmp_path)

    (tmp_path / "empty.py").write_text("x = 1\n")
    result = search_files("nonexistent_query_xyz")
    assert "No matches found" in result
