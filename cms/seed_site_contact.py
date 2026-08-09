"""Update site_settings.contact + socials for the About "Get in Touch" aside."""
from sqlalchemy.orm import Session

from app.db import engine
from app.models import SiteSettings

CONTACT = {"email": "thisisahousegallery@gmail.com"}
SOCIALS = [
    {"label": "@thisisahousegallery", "platform": "instagram", "url": "https://instagram.com/thisisahousegallery"},
]


def main() -> None:
    with Session(engine) as db:
        ss = db.query(SiteSettings).first()
        if ss is None:
            print("NO_SITE_SETTINGS")
            return
        ss.contact = CONTACT
        ss.socials = SOCIALS
        db.commit()
        print("CONTACT_OK email=", ss.contact.get("email"))
        print("SOCIALS_OK ->", ss.socials)


if __name__ == "__main__":
    main()