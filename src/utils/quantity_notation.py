"""Quantity-name display inspired by GUM Workbench manual sections 6.4/6.5."""
import html
import re

GREEK = dict(zip(
    'alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega'.split(),
    'αβγδεζηϑικλµνξοπρστυϕχψω'))
GREEK.update({name.capitalize(): char for name,char in zip(
    list(GREEK), 'ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ')})
GREEK.update(theta1='θ', sigma1='ς', phi1='φ')
IDENTIFIER = r'[^\W\d]\w*'


def decode_greek(text):
    """Decode paired backslash codes; unknown codes remain parser errors."""
    return re.sub(r'\\([A-Za-z][A-Za-z0-9]*)\\',
                  lambda match: GREEK.get(match[1],match[0]), str(text))


def format_quantity_name(name, notation='legacy'):
    name = decode_greek(name)
    if notation == 'legacy':
        base, sep, suffix = name.partition('_')
        if sep and suffix:
            return html.escape(base)+'<sub>'+html.escape(suffix)+'</sub>'
        return html.escape(name)
    parts = name.split('_')
    return ''.join(('<sub>'+html.escape(part)+'</sub>') if index % 2 else html.escape(part)
                   for index,part in enumerate(parts) if part)


def format_names_in_text(text, notation='legacy'):
    return re.sub(IDENTIFIER, lambda match: format_quantity_name(match[0],notation), decode_greek(text))
