from django.apps import AppConfig


class ExhibitionsConfig(AppConfig):
    name = 'housegallery.exhibitions'
    verbose_name = "Exhibitions"

    def ready(self):
        # Import models to ensure proper registration
        from housegallery.exhibitions.models import ExhibitionsIndexPage, ExhibitionPage, SchedulePage