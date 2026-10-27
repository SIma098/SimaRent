"""Формы для управления данными со страниц сайта (без админки)."""

import re

from django import forms

from .models import Car, Office, User


class StyledModelForm(forms.ModelForm):
    """Добавляет полям классы Bootstrap, чтобы формы выглядели как остальной сайт."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                continue
            widget.attrs['class'] = f"{widget.attrs.get('class', '')} form-control".strip()


class CarForm(StyledModelForm):
    # Фото хранится в отдельной таблице car_photos, поэтому это поле не из модели Car
    photo = forms.ImageField(
        label='Добавить фотографию', required=False,
        help_text='Необязательно. Фото добавится к уже загруженным.',
    )

    # Группы полей — так форма выводится по разделам
    sections = (
        ('Автомобиль', ('model', 'year', 'reg_number', 'vin_number', 'color')),
        ('Классификация', ('car_class', 'body_type', 'transmission_type', 'fuel_type')),
        ('Характеристики', ('engine_volume', 'horsepower', 'fuel_consumption',
                            'seats_count', 'doors_count', 'trunk_volume', 'mileage')),
        ('Аренда', ('price_day', 'deposit', 'status', 'home_office', 'current_office',
                    'active')),
        ('Опции и фото', ('features', 'photo')),
    )

    class Meta:
        model = Car
        fields = (
            'model', 'year', 'reg_number', 'vin_number', 'color',
            'car_class', 'body_type', 'transmission_type', 'fuel_type',
            'engine_volume', 'horsepower', 'fuel_consumption',
            'seats_count', 'doors_count', 'trunk_volume', 'mileage',
            'price_day', 'deposit', 'status', 'home_office', 'current_office', 'active',
            'features',
        )
        widgets = {'features': forms.CheckboxSelectMultiple}


class OfficeForm(StyledModelForm):
    class Meta:
        model = Office
        fields = ('city', 'name', 'address', 'phone', 'work_hours', 'active')


PHONE_RE = re.compile(r'^\+?[\d\s()-]+$')


class ProfileForm(StyledModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone')
        help_texts = {'phone': 'Например, +7 999 123-45-67. Чтобы удалить номер, сотрите его и сохраните.'}
        error_messages = {'phone': {'unique': 'Этот номер уже указан у другого пользователя.'}}

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip() if self.cleaned_data['phone'] else ''
        if not phone:
            # пустой телефон храним как NULL: поле уникальное, а пустых строк
            # у разных пользователей может быть много
            return None
        if not PHONE_RE.match(phone) or len(re.sub(r'\D', '', phone)) < 10:
            raise forms.ValidationError('Введите номер телефона: цифры, не меньше 10.')
        return phone
