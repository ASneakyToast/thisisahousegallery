from wagtail import hooks

from .viewsets import NewsletterSnippetViewSet, SubscriberSnippetViewSet


@hooks.register("register_admin_viewset")
def register_subscriber_snippet_viewset():
    return SubscriberSnippetViewSet()


@hooks.register("register_admin_viewset")
def register_newsletter_snippet_viewset():
    return NewsletterSnippetViewSet()
