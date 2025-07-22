from django import template

register = template.Library()

@register.filter
def dict_get(dictionary, key):
    """
    Template filter to look up a value in a dictionary.
    Usage: {{ dict|dict_get:key }}
    """
    if isinstance(dictionary, dict) and key is not None:
        return dictionary.get(key, 0)
    return 0