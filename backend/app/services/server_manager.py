from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Server
from app.schemas import ServerUpsert


def upsert_server(db: Session, server_in: ServerUpsert) -> Server:
    existing = db.scalar(select(Server).where(Server.hostname == server_in.hostname))
    now = datetime.now(timezone.utc)
    if existing:
        existing.os = server_in.os
        existing.tags = server_in.tags
        existing.last_seen_at = now
        db.add(existing)
        db.flush()
        return existing

    server = Server(
        hostname=server_in.hostname,
        os=server_in.os,
        tags=server_in.tags,
        last_seen_at=now,
    )
    db.add(server)
    db.flush()
    return server

