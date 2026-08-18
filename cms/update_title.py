"""Update Devan Ponce exhibition title to 'Coming Soon'."""
from app.db import engine
from app.models import Exhibition
from sqlalchemy.orm import Session

with Session(engine) as db:
    ex = db.query(Exhibition).filter(Exhibition.slug == "devan-ponce").first()
    if ex:
        old = ex.title
        ex.title = "Coming Soon"
        ex.listing_title = "Coming Soon"
        db.commit()
        print(f"UPDATED: {old!r} -> {ex.title!r}")
    else:
        print("NOT FOUND: devan-ponce exhibition")