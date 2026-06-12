from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

STATUS_COLORS = {
    'draft': ('#64748b', '#f1f5f9'),
    'recruiting': ('#15803d', '#dcfce7'),
    'selecting': ('#b45309', '#fef3c7'),
    'submitting': ('#1d4ed8', '#dbeafe'),
    'reviewing': ('#7c3aed', '#ede9fe'),
    'expired': ('#991b1b', '#fee2e2'),
    'canceled': ('#991b1b', '#fee2e2'),
    'complete': ('#166534', '#bbf7d0'),
    'pending': ('#b45309', '#fef3c7'),
    'selected': ('#1d4ed8', '#dbeafe'),
    'accepted': ('#166534', '#bbf7d0'),
    'rejected': ('#991b1b', '#fee2e2'),
}


@register.filter
def language_name(code):
    """Convert a language code to its display name."""
    names = getattr(settings, 'LANGUAGE_DISPLAY_NAMES', {})
    return names.get(code, code)


@register.filter
def status_badge(status):
    """Render a status as a colored badge."""
    display = status.replace('_', ' ').title()
    color, bg = STATUS_COLORS.get(status, ('#64748b', '#f1f5f9'))
    return mark_safe(
        f'<span style="display:inline-block;padding:0.2rem 0.65rem;'
        f'border-radius:6px;font-size:0.75rem;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.03em;'
        f'color:{color};background:{bg};">{display}</span>'
    )


@register.filter
def status_color(status):
    """Return just the text color for a status."""
    color, _ = STATUS_COLORS.get(status, ('#64748b', '#f1f5f9'))
    return color


@register.filter
def status_bg(status):
    """Return just the background color for a status."""
    _, bg = STATUS_COLORS.get(status, ('#64748b', '#f1f5f9'))
    return bg
