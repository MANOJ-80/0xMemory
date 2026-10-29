"""Read Git evidence without executing hooks or changing the repository."""

import shutil
import subprocess
import ast
import hashlib
import copy
from pathlib import Path


def _semantic_hash(node: ast.AST) -> str:
    """Hash Python structure while ignoring source positions and leading docstrings."""
    normalized = copy.deepcopy(node)
    for item in ast.walk(normalized):
        if isinstance(item, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(item, "body", None)
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                body.pop(0)
                if not body:
                    body.append(ast.Pass())
    payload = ast.dump(normalized, include_attributes=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class Repository:
    def __init__(self, project_dir: Path):
        self.path = project_dir.resolve()
        self.executable = shutil.which("git")
        if not self.executable:
            windows_git = Path("C:/Program Files/Git/cmd/git.exe")
            if windows_git.exists():
                self.executable = str(windows_git)
        if not self.executable:
            raise ValueError("Git is required for commit evidence")
        root = Path(self.run("rev-parse", "--show-toplevel").strip()).resolve()
        if root != self.path:
            raise ValueError("Initialize the memory store at the Git repository root")

    def run(self, *args: str) -> str:
        result = subprocess.run(
            [self.executable, "-C", str(self.path), *args],
            capture_output=True, encoding="utf-8", errors="replace", timeout=30,
        )
        if result.returncode:
            raise ValueError(result.stderr.strip() or "Git operation failed")
        return result.stdout

    def resolve(self, ref: str) -> str:
        return self.run("rev-parse", "--verify", "--end-of-options", ref + "^{commit}").strip()

    def validate_evidence(self, commit: str, paths: list[str]) -> str:
        sha = self.resolve(commit)
        for path in paths:
            name = Path(path).name.lower()
            if (name == ".env" or name.startswith(".env.") or name.endswith((".pem", ".key"))
                    or any(word in name for word in ("credential", "secret", "id_rsa"))):
                raise ValueError(f"Sensitive-looking files cannot be used as evidence: {path}")
            if self.run("cat-file", "-t", sha + ":" + path).strip() != "blob":
                raise ValueError(f"Evidence is not a file at {sha}: {path}")
        return sha

    def capture_evidence(self, commit: str, paths: list[str], symbols: list[str] | None = None) -> list[dict]:
        """Record immutable file and Python symbol anchors at a reviewed commit."""
        sha = self.resolve(commit)
        refs = []
        for path in paths:
            blob = self.run("rev-parse", "--verify", f"{sha}:{path}").strip()
            refs.append({"kind": "file", "path": path, "revision": sha, "blob": blob})
            if not symbols or Path(path).suffix != ".py":
                continue
            source = self.run("show", f"{sha}:{path}")
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            wanted = set(symbols)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in wanted:
                    segment = ast.get_source_segment(source, node) or ""
                    refs.append({"kind": "symbol", "path": path, "symbol": node.name,
                                 "start_line": node.lineno, "end_line": node.end_lineno,
                                 "revision": sha,
                                 "content_hash": hashlib.sha256(segment.encode()).hexdigest(),
                                 "semantic_hash": _semantic_hash(node)})
        return refs

    def changed_paths(self, target: str, base: str | None = None) -> set[str]:
        if base:
            output = self.run("diff", "--name-only", "--no-renames", "-z", base, target, "--")
        else:
            output = self.run(
                "diff-tree", "--root", "--no-commit-id", "-r", "-m",
                "--name-only", "--no-renames", "-z", target, "--",
            )
        return set(filter(None, output.split("\0")))

    def is_ancestor(self, older: str, newer: str) -> bool:
        return self.run("merge-base", older, newer).strip() == older

    def _rename_map(self, *diff_args: str) -> dict[str, str]:
        output = self.run("diff", "--find-renames", "--name-status", "-z", *diff_args, "--")
        fields = output.split("\0")
        renames = {}
        index = 0
        while index < len(fields):
            status = fields[index]
            if not status:
                index += 1
                continue
            if status.startswith("R") and index + 2 < len(fields):
                renames[fields[index + 1]] = fields[index + 2]
                index += 3
            elif status.startswith("C") and index + 2 < len(fields):
                index += 3
            else:
                index += 2
        return renames

    def current_context(self) -> dict:
        """Return the current Git branch, revision, and changed worktree paths."""
        branch = self.run("branch", "--show-current").strip() or None
        head = self.resolve("HEAD")
        changed = set(filter(None, self.run("diff", "--name-only", "-z", "HEAD", "--").split("\0")))
        staged = self.run("diff", "--cached", "--name-only", "-z", "HEAD", "--")
        changed.update(filter(None, staged.split("\0")))
        untracked = self.run("ls-files", "--others", "--exclude-standard", "-z")
        changed.update(filter(None, untracked.split("\0")))
        return {"branch": branch, "head": head, "changed_paths": sorted(changed),
                "repository": str(self.path)}

    def assess_evidence(
        self, commit: str | None, branch: str | None, paths: list[str],
        context: dict | None = None, evidence_refs: list[dict] | None = None,
    ) -> dict:
        """Conservatively qualify evidence against current committed and uncommitted code."""
        current = context or self.current_context()
        if not paths or not commit:
            return {"state": "unknown", "reason": "No linked commit and file evidence to validate."}
        try:
            baseline = self.resolve(commit)
            if branch and branch != current["branch"]:
                return {
                    "state": "unknown",
                    "reason": f"Evidence was reviewed on branch {branch}; current branch is "
                    f"{current['branch'] or 'detached HEAD'}.",
                }
            if not self.is_ancestor(baseline, current["head"]):
                return {"state": "unknown", "reason": "Evidence commit is not an ancestor of current HEAD."}
            committed_changes = self.changed_paths(current["head"], baseline)
            changed = committed_changes | set(current["changed_paths"])
            renamed = self._rename_map(baseline, current["head"])
            renamed.update(self._rename_map("HEAD"))
            refs = evidence_refs or []
            symbol_refs: dict[str, list[dict]] = {}
            for ref in refs:
                if ref.get("kind") == "symbol" and ref.get("path"):
                    symbol_refs.setdefault(ref["path"], []).append(ref)
            unresolved = []
            for path in paths:
                active_path = renamed.get(path, path)
                if path not in changed and active_path not in changed:
                    continue
                dirty_path = active_path in current["changed_paths"] or path in current["changed_paths"]
                if dirty_path:
                    candidate = (self.path / active_path).resolve()
                    if self.path not in candidate.parents:
                        return {"state": "unknown", "reason": "Evidence path escaped the repository root."}
                    if not candidate.is_file():
                        return {"state": "evidence_missing",
                                "reason": f"Linked evidence file is missing from the worktree: {active_path}."}
                else:
                    try:
                        self.run("cat-file", "-e", f"{current['head']}:{active_path}")
                    except ValueError:
                        return {"state": "evidence_missing",
                                "reason": f"Linked evidence file no longer exists at HEAD: {active_path}."}
                anchors = symbol_refs.get(path)
                if not anchors:
                    unresolved.append(path)
                    continue
                # A symbol anchor can survive unrelated edits in the containing file.
                # For a dirty or staged path, inspect the actual worktree content.
                if active_path in current["changed_paths"] or path in current["changed_paths"]:
                    candidate = (self.path / active_path).resolve()
                    if self.path not in candidate.parents:
                        return {"state": "unknown", "reason": "Evidence path escaped the repository root."}
                    try:
                        source = candidate.read_text(encoding="utf-8")
                    except (OSError, UnicodeDecodeError):
                        return {"state": "evidence_missing",
                                "reason": f"Linked evidence file is missing or unreadable: {active_path}."}
                else:
                    try:
                        source = self.run("show", f"{current['head']}:{active_path}")
                    except ValueError:
                        return {"state": "evidence_missing",
                                "reason": f"Linked evidence file no longer exists at HEAD: {active_path}."}
                try:
                    tree = ast.parse(source)
                except SyntaxError:
                    return {"state": "unknown", "reason": f"Could not parse changed symbol evidence in {active_path}."}
                for ref in anchors:
                    symbol = ref.get("symbol")
                    expected = ref.get("semantic_hash") or ref.get("content_hash")
                    definitions = [
                        node for node in ast.walk(tree)
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                        and node.name == symbol
                    ]
                    if not definitions:
                        return {"state": "evidence_missing", "reason": f"Anchored symbol {active_path}:{symbol} no longer exists after edits/rename."}
                    matches = [_semantic_hash(node) if ref.get("semantic_hash") else
                               hashlib.sha256((ast.get_source_segment(source, node) or "").encode()).hexdigest()
                               for node in definitions]
                    if expected not in matches:
                        return {"state": "unknown", "reason": f"Anchored symbol {active_path}:{symbol} changed since review."}
            if unresolved:
                return {
                    "state": "unknown",
                    "reason": "Linked evidence changed after review: " + ", ".join(sorted(unresolved)),
                }
            for ref in refs:
                if ref.get("kind") != "symbol":
                    continue
                path, symbol = ref.get("path"), ref.get("symbol")
                expected = ref.get("content_hash")
                semantic = ref.get("semantic_hash")
                expected = semantic or expected
                if not path or not symbol or not expected:
                    continue
                if path in changed or renamed.get(path, path) in changed:
                    continue  # Already compared against changed worktree/HEAD content above.
                try:
                    source = self.run("show", f"{current['head']}:{path}")
                    tree = ast.parse(source)
                except (ValueError, SyntaxError, UnicodeDecodeError):
                    return {"state": "unknown", "reason": f"Could not parse symbol evidence {path}:{symbol}."}
                definitions = [
                    node for node in ast.walk(tree)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                    and node.name == symbol
                ]
                if not definitions:
                    return {"state": "evidence_missing", "reason": f"Anchored symbol {path}:{symbol} no longer exists."}
                actuals = [_semantic_hash(node) if semantic else hashlib.sha256(
                    (ast.get_source_segment(source, node) or "").encode()
                ).hexdigest() for node in definitions]
                if expected not in actuals:
                    return {"state": "unknown", "reason": f"Anchored symbol {path}:{symbol} changed since review."}
            return {"state": "supported", "reason": "All linked file and symbol anchors resolve at the current repository state."}
        except ValueError as exc:
            return {"state": "unknown", "reason": f"Could not resolve Git evidence: {exc}"}
