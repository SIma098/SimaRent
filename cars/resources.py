from import_export import fields, resources
from import_export.widgets import DateTimeWidget, DecimalWidget, IntegerWidget

from .models import Booking, Car

# виджеты отдают в Excel настоящие числа и даты, а не текст
DATETIME = DateTimeWidget(format='%d.%m.%Y %H:%M')
MONEY = DecimalWidget()
INT = IntegerWidget()


def yes_no(value):
    return 'Да' if value else 'Нет'


class CarResource(resources.ModelResource):
    reg_number = fields.Field(attribute='reg_number', column_name='Госномер')
    vin_number = fields.Field(attribute='vin_number', column_name='VIN')
    brand = fields.Field(attribute='model__brand__name', column_name='Марка')
    model = fields.Field(attribute='model__name', column_name='Модель')
    year = fields.Field(attribute='year', column_name='Год выпуска', widget=INT)
    car_class = fields.Field(attribute='car_class__name', column_name='Класс')
    body_type = fields.Field(attribute='body_type__name', column_name='Кузов')
    transmission_type = fields.Field(attribute='transmission_type__name', column_name='КПП')
    fuel_type = fields.Field(attribute='fuel_type__name', column_name='Топливо')
    color = fields.Field(attribute='color__name', column_name='Цвет')
    mileage = fields.Field(attribute='mileage', column_name='Пробег, км', widget=INT)
    price_day = fields.Field(attribute='price_day', column_name='Цена за сутки, ₽', widget=MONEY)
    deposit = fields.Field(attribute='deposit', column_name='Залог, ₽', widget=MONEY)
    status = fields.Field(column_name='Статус')
    home_office = fields.Field(attribute='home_office__name', column_name='Офис приписки')
    current_office = fields.Field(attribute='current_office__name', column_name='Где сейчас')
    active = fields.Field(column_name='Активен')

    class Meta:
        model = Car
        fields = ('reg_number', 'vin_number', 'brand', 'model', 'year', 'car_class',
                  'body_type', 'transmission_type', 'fuel_type', 'color', 'mileage',
                  'price_day', 'deposit', 'status', 'home_office', 'current_office', 'active')
        export_order = fields

    def dehydrate_status(self, car):
        return car.get_status_display()

    def dehydrate_active(self, car):
        return yes_no(car.active)


class BookingResource(resources.ModelResource):
    booking_number = fields.Field(attribute='booking_number', column_name='Номер брони')
    client = fields.Field(attribute='user', column_name='Арендатор')
    email = fields.Field(attribute='user__email', column_name='Email')
    phone = fields.Field(attribute='user__phone', column_name='Телефон')
    car = fields.Field(attribute='car__model', column_name='Автомобиль')
    reg_number = fields.Field(attribute='car__reg_number', column_name='Госномер')
    pickup_office = fields.Field(attribute='pickup_office__name', column_name='Офис получения')
    return_office = fields.Field(attribute='return_office__name', column_name='Офис возврата')
    date_start = fields.Field(attribute='date_start', column_name='Начало', widget=DATETIME)
    date_end = fields.Field(attribute='date_end', column_name='Окончание', widget=DATETIME)
    days_count = fields.Field(attribute='days_count', column_name='Суток', widget=INT)
    price_day = fields.Field(attribute='price_day', column_name='Цена за сутки, ₽', widget=MONEY)
    total_sum = fields.Field(attribute='total_sum', column_name='Стоимость, ₽', widget=MONEY)
    deposit = fields.Field(attribute='deposit', column_name='Залог, ₽', widget=MONEY)
    status = fields.Field(attribute='status__name', column_name='Статус')
    paid = fields.Field(column_name='Оплачено')
    date_created = fields.Field(attribute='date_created', column_name='Создана',
                                widget=DATETIME)

    class Meta:
        model = Booking
        fields = ('booking_number', 'client', 'email', 'phone', 'car', 'reg_number',
                  'pickup_office', 'return_office', 'date_start', 'date_end', 'days_count',
                  'price_day', 'total_sum', 'deposit', 'status', 'paid', 'date_created')
        export_order = fields

    def dehydrate_paid(self, booking):
        return yes_no(booking.paid)
