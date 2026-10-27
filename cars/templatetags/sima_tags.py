"""Свои фильтры и теги шаблонов. Подключение в шаблоне: {% load sima_tags %}"""

from django import template

register = template.Library()


@register.filter
def ru_plural(number, forms):
    """Русские окончания: {{ 5|ru_plural:"машина,машины,машин" }} → «5 машин»."""
    one, few, many = forms.split(',')
    n = abs(int(number or 0))
    if n % 10 == 1 and n % 100 != 11:
        word = one
    elif 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        word = few
    else:
        word = many
    return f'{number} {word}'


@register.inclusion_tag('cars/includes/stat_card.html')
def stat_card(title, value, icon, color='primary'):
    """Плитка с числом: {% stat_card "Брони" 216 "bi-calendar-check" %}"""
    return {'title': title, 'value': value, 'icon': icon, 'color': color}
