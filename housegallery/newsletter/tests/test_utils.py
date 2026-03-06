from unittest.mock import MagicMock, patch

from housegallery.newsletter.utils import add_utm_params, get_base_url


class TestGetBaseUrl:
    @patch("wagtail.models.Site")
    def test_returns_site_root_url(self, mock_site_class):
        mock_site = MagicMock()
        mock_site.root_url = "https://example.com/"
        mock_site_class.objects.filter.return_value.first.return_value = mock_site
        assert get_base_url() == "https://example.com"

    @patch("wagtail.models.Site")
    def test_strips_trailing_slash(self, mock_site_class):
        mock_site = MagicMock()
        mock_site.root_url = "https://example.com/"
        mock_site_class.objects.filter.return_value.first.return_value = mock_site
        assert get_base_url() == "https://example.com"

    @patch("wagtail.models.Site")
    def test_fallback_when_no_site(self, mock_site_class):
        mock_site_class.objects.filter.return_value.first.return_value = None
        assert get_base_url() == "https://thisisahousegallery.com"

    def test_fallback_on_import_error(self):
        with patch.dict("sys.modules", {"wagtail.models": None}):
            assert get_base_url() == "https://thisisahousegallery.com"


class TestAddUtmParams:
    def test_adds_utm_to_standard_link(self):
        html = '<a href="https://example.com/page">Link</a>'
        result = add_utm_params(html, "march-2026")
        assert "utm_source=newsletter" in result
        assert "utm_medium=email" in result
        assert "utm_campaign=march-2026" in result

    def test_skips_mailto_links(self):
        html = '<a href="mailto:hello@example.com">Email</a>'
        result = add_utm_params(html, "test")
        assert result == html

    def test_skips_anchor_links(self):
        html = '<a href="#section">Jump</a>'
        result = add_utm_params(html, "test")
        assert result == html

    def test_skips_unsubscribe_links(self):
        html = '<a href="https://example.com/newsletter/unsubscribe/abc/">Unsub</a>'
        result = add_utm_params(html, "test")
        assert "utm_source" not in result

    def test_preserves_existing_query_params(self):
        html = '<a href="https://example.com/page?foo=bar">Link</a>'
        result = add_utm_params(html, "test")
        assert "foo=bar" in result
        assert "utm_source=newsletter" in result

    def test_handles_multiple_links(self):
        html = (
            '<a href="https://a.com">A</a>'
            '<a href="mailto:x@y.com">B</a>'
            '<a href="https://b.com">C</a>'
        )
        result = add_utm_params(html, "test")
        assert result.count("utm_source=newsletter") == 2

    def test_skips_non_http_scheme(self):
        html = '<a href="tel:+1234567890">Call</a>'
        result = add_utm_params(html, "test")
        assert result == html
