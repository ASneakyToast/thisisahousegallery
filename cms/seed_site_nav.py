"""Populate site_settings.nav (+ leave socials empty) from the live site's nav.

The live header shows exactly three top-level links:
  Exhibitions  /exhibitions/   (CTA)
  Schedule     /schedule/      (CTA)
  About us     /about/         (menu)

We store these in SiteSettings.nav as [{label, url, cta}] so the Astro header
can be driven from the CMS (editable via admin) instead of hardcoded.
Socials are left empty — the live site footer exposes none.
"""

from sqlalchemy.orm import Session

from app.db import engine
from app.models import SiteSettings

NAV = [
    {"label": "Exhibitions", "url": "/exhibitions/", "cta": True},
    {"label": "Schedule", "url": "/schedule/", "cta": True},
    {"label": "About us", "url": "/about/", "cta": False},
]


def main() -> None:
    with Session(engine) as db:
        ss = db.query(SiteSettings).first()
        if ss is None:
            print("NO_SITE_SETTINGS")
            return
        ss.nav = NAV
        db.commit()
        print("NAV_OK ->", ss.nav)
        print("socials  ->", ss.socials)


if __name__ == "__main__":
    main()