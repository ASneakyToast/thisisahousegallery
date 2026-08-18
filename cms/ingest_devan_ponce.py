"""Create the upcoming Devan Ponce exhibition (Nov 13 2026 -> Jan 13 2027).

Leading with the artist as the working title (no show title yet). Idempotent:
skips if the exhibition slug already exists; creates the artist if missing.

Run from cms/:
    .venv/Scripts/python + db access via default DATABASE_URL (docker pg).
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Session, joinedload

from app.db import engine
from app.models import Artist, Exhibition

OPENING_SUMMARY = (
    "<p>A new exhibition by Devan Ponce opens <strong>November 13, 2026</strong> and runs "
    "through <strong>January 13, 2027</strong>. Show title and details to be announced — "
    "save the date for the opening.</p>"
)


def main() -> None:
    with Session(engine) as db:
        # Existing exhibition with this slug? then bail.
        existing = (
            db.query(Exhibition)
            .options(joinedload(Exhibition.artists))
            .filter(Exhibition.slug == "devan-ponce")
            .first()
        )
        if existing:
            print(f"EXISTING exhibition id={existing.id} — nothing to do")
            print(f"  title={existing.title!r} start={existing.start_date} end={existing.end_date}")
            return

        # Artist — create if missing.
        artist = db.query(Artist).filter(Artist.slug == "devan-ponce").first()
        if not artist:
            artist = Artist(name="Devan Ponce", slug="devan-ponce", bio="")
            db.add(artist)
            db.flush()
            print(f"CREATED artist id={artist.id}")

        start = datetime(2026, 11, 13)
        end = datetime(2027, 1, 13)
        ex = Exhibition(
            title="Devan Ponce",
            slug="devan-ponce",
            start_date=start,
            end_date=end,
            description="",
            body=[],
            listing_title="Devan Ponce",
            listing_summary=OPENING_SUMMARY,
            artists=[artist],
            artworks=[],
        )
        db.add(ex)
        db.flush()
        print(f"CREATED exhibition id={ex.id}")
        print(f"  title   = {ex.title!r}")
        print(f"  slug    = {ex.slug!r}")
        print(f"  dates   = {ex.start_date.date()} -> {ex.end_date.date()}")
        print(f"  artists = {[a.name for a in ex.artists]}")
        db.commit()
        print("COMMIT_OK")


if __name__ == "__main__":
    main()
