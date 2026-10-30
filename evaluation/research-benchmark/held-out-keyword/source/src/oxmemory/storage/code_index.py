"""Bounded, read-only source definition index for retrieval-time code evidence."""

import ast
import hashlib
import re
from pathlib import Path

from oxmemory.storage.security import contains_obvious_secret


EXCLUDED_DIRS = {".git", ".0xmemory", ".venv", "venv", "node_modules", "__pycache__", "dist", "build"}
SENSITIVE_NAMES = (".env", "secret", "credential", "id_rsa", ".pem", ".key")
SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".cs"}
LANGUAGE_BY_SUFFIX = {
    ".py": "python", ".js": "javascript", ".jsx": "jsx", ".ts": "typescript",
    ".tsx": "tsx", ".go": "go", ".rs": "rust", ".java": "java", ".cs": "csharp",
}

# These are deliberately conservative declaration patterns. Python uses its AST;
# the other languages use line-oriented patterns and never execute project code.
DECLARATIONS = {
    ".js": re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(?:function|class)\s+([A-Za-z_$][\w$]*)\b"),
    ".jsx": re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(?:function|class)\s+([A-Za-z_$][\w$]*)\b"),
    ".ts": re.compile(r"^\s*(?:export\s+)?(?:declare\s+)?(?:abstract\s+)?(?:async\s+)?(?:function|class|interface|type|enum)\s+([A-Za-z_$][\w$]*)\b"),
    ".tsx": re.compile(r"^\s*(?:export\s+)?(?:declare\s+)?(?:abstract\s+)?(?:async\s+)?(?:function|class|interface|type|enum)\s+([A-Za-z_$][\w$]*)\b"),
    ".go": re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)\b|^\s*type\s+([A-Za-z_]\w*)\s+(?:struct|interface)\b"),
    ".rs": re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?(?:fn|struct|enum|trait|type)\s+([A-Za-z_]\w*)\b"),
    ".java": re.compile(r"^\s*(?:(?:public|protected|private|static|final|abstract)\s+)*(?:class|interface|enum|record)\s+([A-Za-z_$][\w$]*)\b"),
    ".cs": re.compile(r"^\s*(?:(?:public|internal|private|protected|static|abstract|sealed|partial)\s+)*(?:class|interface|enum|struct|record)\s+([A-Za-z_]\w*)\b"),
}


def search_code_definitions(
    project_dir: Path,
    symbols: list[str] | None = None,
    file_paths: list[str] | None = None,
    query: str = "",
    limit: int = 5,
    max_files: int = 2500,
) -> list[dict]:
    """Find source definitions and exact identifier references.

    This index is intentionally separate from memories: results are source-code
    evidence, never project decisions or memory claims. Files are parsed, never
    imported or executed.
    """
    root = Path(project_dir).resolve()
    wanted_symbols = set(symbols or [])
    wanted_paths = {Path(value).as_posix() for value in (file_paths or [])}
    terms = {term.casefold() for term in re.findall(r"[A-Za-z_][A-Za-z0-9_]+", query)}
    matches = []
    visited = 0
    try:
        paths = (path for path in root.rglob("*") if path.suffix.casefold() in SOURCE_SUFFIXES)
        for path in paths:
            if any(part in EXCLUDED_DIRS or part.startswith(".") for part in path.relative_to(root).parts[:-1]):
                continue
            relative = path.relative_to(root).as_posix()
            if any(secret in part.casefold() for part in path.relative_to(root).parts
                   for secret in SENSITIVE_NAMES):
                continue
            try:
                resolved = path.resolve(strict=True)
                if root not in resolved.parents or path.is_symlink():
                    continue
                if resolved.stat().st_size > 500_000:
                    continue
                source = resolved.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            visited += 1
            if visited > max_files:
                break
            declarations = []
            suffix = path.suffix.casefold()
            if suffix == ".py":
                try:
                    tree = ast.parse(source, filename=relative)
                except SyntaxError:
                    continue
                declarations = [
                    (node.name, "class" if isinstance(node, ast.ClassDef) else "function",
                     node.lineno, getattr(node, "end_lineno", node.lineno))
                    for node in ast.walk(tree)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                ]
            else:
                declaration_pattern = DECLARATIONS.get(suffix)
                for line_number, line in enumerate(source.splitlines(), 1):
                    match = declaration_pattern.match(line) if declaration_pattern else None
                    if match:
                        name = next((group for group in match.groups() if group), "")
                        keyword = re.search(
                            r"\b(function|class|interface|type|enum|struct|trait|fn|func|record)\b",
                            line,
                        )
                        kind = keyword.group(1) if keyword else "definition"
                        if kind in {"fn", "func"}:
                            kind = "function"
                        elif kind in {"interface", "struct", "trait", "record"}:
                            kind = "type"
                        declarations.append((name, kind, line_number, line_number))
            lines = source.splitlines()
            for symbol, kind, line_number, end_line in declarations:
                exact_symbol = symbol in wanted_symbols
                exact_path = relative in wanted_paths
                node_terms = set(re.findall(r"[a-z0-9_]+", symbol.casefold()))
                path_terms = set(re.findall(r"[a-z0-9_]+", relative.casefold()))
                start = max(0, line_number - 1)
                end = min(len(lines), end_line, start + 30)
                snippet = "\n".join(lines[start:end])[:4000]
                content_terms = set(re.findall(r"[a-z0-9_]+", snippet.casefold()))
                overlap = len(terms & (node_terms | path_terms | content_terms))
                if not (exact_symbol or exact_path or overlap):
                    continue
                score = (4.0 if exact_symbol else 0.0) + (2.0 if exact_path else 0.0) + overlap
                if contains_obvious_secret(snippet):
                    continue
                matches.append({
                    "path": relative,
                    "symbol": symbol,
                    "kind": kind,
                    "start_line": line_number,
                    "end_line": end_line,
                    "score": score,
                    "snippet": snippet,
                    "file_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
                    "language": LANGUAGE_BY_SUFFIX.get(suffix, "text"),
                    "source_type": "repository_code",
                })
            # Add exact call/reference sites, including in files that also have
            # declarations. Declaration records remain the higher-scoring hits.
            if wanted_symbols:
                for requested in wanted_symbols:
                    for line_number, line in enumerate(lines, 1):
                        if re.search(rf"(?<![\w$]){re.escape(requested)}(?![\w$])", line):
                            if any(name == requested and start_line == line_number
                                   for name, _kind, start_line, _end_line in declarations):
                                continue
                            if contains_obvious_secret(line):
                                continue
                            matches.append({
                                "path": relative, "symbol": requested, "kind": "reference",
                                "start_line": line_number, "end_line": line_number,
                                "score": 1.0, "snippet": line[:4000],
                                "file_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
                                "language": LANGUAGE_BY_SUFFIX.get(suffix, "text"),
                                "source_type": "repository_code",
                            })
    except OSError:
        return []
    references_by_symbol: dict[str, list[dict]] = {}
    for item in matches:
        if item["kind"] == "reference":
            references_by_symbol.setdefault(item["symbol"], []).append(
                {"path": item["path"], "line": item["start_line"]}
            )
    for item in matches:
        if item["kind"] != "reference":
            item["references"] = [
                ref for ref in references_by_symbol.get(item["symbol"], [])
                if ref["path"] != item["path"]
            ][:10]
    matches.sort(key=lambda item: (-item["score"], item["path"], item["start_line"], item["symbol"]))
    return matches[:max(0, limit)]


def search_python_definitions(*args, **kwargs) -> list[dict]:
    """Backward-compatible name for the former Python-only lookup."""
    return search_code_definitions(*args, **kwargs)
