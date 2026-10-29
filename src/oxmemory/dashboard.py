"""Local memory inspection app: python -m oxmemory.dashboard --project PATH."""

import argparse
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

from oxmemory.storage.memory_store import MemoryStore


class Review(BaseModel):
    model_config = ConfigDict(extra="forbid")
    commit: str = "HEAD"
    note: str = Field(min_length=1)
    content: str | None = None
    file_paths: list[str] | None = None
    claim_value: str | None = None
    claim_confidence: float | None = Field(default=None, ge=0, le=1)
    valid_from: str | None = None
    valid_to: str | None = None


class CommitRequest(BaseModel):
    commit: str = "HEAD"


class ClaimStateRequest(BaseModel):
    state: str
    note: str = Field(min_length=1)


def create_dashboard(project: Path, enable_vectors: bool = True) -> FastAPI:
    store = MemoryStore(project, enable_vectors=enable_vectors)
    @asynccontextmanager
    async def lifespan(app):
        try:
            yield
        finally:
            store.close()

    app = FastAPI(title="0xMemory inspection", lifespan=lifespan)

    @app.middleware("http")
    async def local_requests(request: Request, call_next):
        # No cross-origin mutations from arbitrary pages opened in the browser.
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            if origin and origin != str(request.base_url).rstrip("/"):
                from fastapi.responses import JSONResponse
                return JSONResponse({"detail": "Same-origin requests only"}, status_code=403)
        return await call_next(request)

    from starlette.middleware.trustedhost import TrustedHostMiddleware
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"],
    )

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return HTML

    @app.get("/api/memories")
    async def memories():
        return [m.model_dump(mode="json") for m in store.list_memories(limit=10000)]

    @app.get("/api/recall")
    async def recall(query: str, file: str = "", history: bool = False, budget: int = 1500):
        try:
            return store.recall_context(query, file_paths=[file] if file else [],
                                        include_history=history, token_budget=budget)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.post("/api/observe")
    async def observe(body: CommitRequest):
        try:
            return store.observe_commit(body.commit)
        except (ValueError, OSError) as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.post("/api/memories/{memory_id}/review")
    async def review(memory_id: str, body: Review):
        try:
            if body.content is not None:
                result = store.supersede(
                    memory_id, body.content, body.commit, body.note, body.file_paths,
                    claim_value=body.claim_value,
                    claim_confidence=body.claim_confidence,
                    valid_from=body.valid_from,
                    valid_to=body.valid_to,
                )
            else:
                result = store.verify(memory_id, body.commit, body.note,
                                      claim_confidence=body.claim_confidence,
                                      valid_from=body.valid_from, valid_to=body.valid_to)
            return result.model_dump(mode="json")
        except (ValueError, OSError) as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.post("/api/memories/{memory_id}/claim-state")
    async def claim_state(memory_id: str, body: ClaimStateRequest):
        try:
            return store.set_claim_state(memory_id, body.state, body.note,
                                         actor="dashboard-user").model_dump(mode="json")
        except (ValueError, OSError) as exc:
            raise HTTPException(400, str(exc)) from exc

    return app


HTML = Path(__file__).with_suffix(".html").read_text(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--keyword-only", action="store_true")
    args = parser.parse_args()
    if not (args.project / ".0xmemory").exists():
        parser.error("Initialize this project with 0xmemory init first")
    import uvicorn
    uvicorn.run(
        create_dashboard(args.project, not args.keyword_only), host="127.0.0.1", port=args.port,
    )


if __name__ == "__main__":
    main()
