import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def get_base_url():
    """Get the site base URL from Wagtail settings or fallback."""
    try:
        from wagtail.models import Site

        site = Site.objects.filter(is_default_site=True).first()
        if site:
            return site.root_url.rstrip("/")
    except Exception:
        pass
    return "https://thisisahousegallery.com"


def add_utm_params(html: str, campaign: str) -> str:
    """Append UTM parameters to all links in rendered newsletter HTML.

    Skips unsubscribe links, mailto: links, and anchor (#) links.
    """
    utm = {
        "utm_source": "newsletter",
        "utm_medium": "email",
        "utm_campaign": campaign,
    }

    def _replace_href(match):
        url = match.group(1)

        # Skip mailto, anchors, and unsubscribe links
        if url.startswith("mailto:") or url.startswith("#"):
            return match.group(0)
        if "/newsletter/unsubscribe/" in url:
            return match.group(0)

        parsed = urlparse(url)
        # Only process http/https URLs (or protocol-relative)
        if parsed.scheme and parsed.scheme not in ("http", "https"):
            return match.group(0)

        # Merge UTM params into existing query string
        existing_params = parse_qs(parsed.query, keep_blank_values=True)
        existing_params.update({k: [v] for k, v in utm.items()})
        new_query = urlencode(
            {k: v[0] for k, v in existing_params.items()}, doseq=False
        )
        new_url = urlunparse(parsed._replace(query=new_query))
        return f'href="{new_url}"'

    return re.sub(r'href="([^"]+)"', _replace_href, html)
