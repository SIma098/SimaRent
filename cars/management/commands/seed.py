"""Наполнение базы демо-данными: python manage.py seed

Справочники получают только реальные значения (коробок передач всего 4,
поэтому их 4). Основные таблицы — пользователи, офисы, модели, машины,
фотографии, бронирования — минимум по 10 записей.

Команду можно запускать повторно: существующие записи не меняются,
добавляются только недостающие.
"""

from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from cars.models import (
    BodyType, Booking, BookingStatus, Brand, Car, CarClass, CarModel, CarPhoto,
    City, Color, Feature, FuelType, Office, Role, TransmissionType, User,
)

# Пароль всех демо-пользователей (у уже существующих пароль не меняется)
DEMO_PASSWORD = 'SimaDemo-2026'

IMAGES = Path(settings.BASE_DIR) / 'cars' / 'static' / 'carrentals' / 'images'

ROLES = [
    ('admin', 'Администратор', 'Полный доступ к админке', 1),
    ('manager', 'Менеджер', 'Работает с машинами, фото и бронированиями', 2),
    ('renter', 'Арендатор', 'Клиент, бронирует автомобили на сайте', 3),
]

CITIES = [
    ('msk', 'Москва', 'Москва', 1),
    ('spb', 'Санкт-Петербург', 'Санкт-Петербург', 2),
    ('vlg', 'Волгоград', 'Волгоградская область', 3),
]

# (код города, название, адрес, телефон, часы работы)
OFFICES = [
    ('msk', 'Шереметьево, терминал B', 'Шереметьевское шоссе, 1', '+7 495 100-20-30', 'круглосуточно'),
    ('msk', 'Москва-Сити', 'Пресненская набережная, 12', '+7 495 100-20-31', '08:00 — 22:00'),
    ('msk', 'Домодедово, зал прилёта', 'аэропорт Домодедово, стойка 14', '+7 495 100-20-32', 'круглосуточно'),
    ('msk', 'Внуково, зал прилёта', 'аэропорт Внуково, терминал A', '+7 495 100-20-33', 'круглосуточно'),
    ('spb', 'Пулково, зал прилёта', 'Пулковское шоссе, 41', '+7 812 100-20-30', '07:00 — 23:00'),
    ('spb', 'Невский проспект', 'Невский проспект, 114', '+7 812 100-20-31', '09:00 — 21:00'),
    ('spb', 'Московский вокзал', 'Невский проспект, 85', '+7 812 100-20-32', '08:00 — 22:00'),
    ('vlg', 'Гумрак, аэропорт', 'аэропорт Гумрак, терминал 1', '+7 8442 50-20-30', '06:00 — 23:00'),
    ('vlg', 'Центральный', 'площадь Павших Борцов, 2', '+7 8442 50-20-31', '08:00 — 20:00'),
    ('vlg', 'Волгоград-1, вокзал', 'привокзальная площадь, 1', '+7 8442 50-20-32', '07:00 — 21:00'),
]

CLASSES = [
    ('econom', 'Эконом', 'Компактные машины с малым расходом — для поездок по городу.', 1),
    ('comfort', 'Комфорт', 'Автомат и мягкая подвеска — для спокойных и долгих поездок.', 2),
    ('business', 'Бизнес', 'Статусные автомобили для деловых поездок.', 3),
    ('sport', 'Спорт', 'Мощные купе и кабриолеты для тех, кому важна динамика.', 4),
]

BODY_TYPES = [
    ('sedan', 'Седан'), ('hatchback', 'Хэтчбек'), ('liftback', 'Лифтбек'),
    ('wagon', 'Универсал'), ('coupe', 'Купе'), ('cabrio', 'Кабриолет'),
    ('crossover', 'Кроссовер'), ('suv', 'Внедорожник'), ('minivan', 'Минивэн'),
    ('pickup', 'Пикап'),
]

TRANSMISSIONS = [
    ('manual', 'Механика'), ('auto', 'Автомат'), ('robot', 'Робот'), ('cvt', 'Вариатор'),
]

FUELS = [
    ('petrol', 'Бензин'), ('diesel', 'Дизель'), ('hybrid', 'Гибрид'), ('electric', 'Электро'),
]

COLORS = [
    ('white', 'Белый', '#FFFFFF'), ('black', 'Чёрный', '#000000'),
    ('silver', 'Серебристый', '#C0C0C0'), ('grey', 'Серый', '#808080'),
    ('red', 'Красный', '#D32F2F'), ('blue', 'Синий', '#1E4FA3'),
    ('lightblue', 'Голубой', '#4FA3E0'), ('green', 'Зелёный', '#2E7D32'),
    ('yellow', 'Жёлтый', '#F9C80E'), ('brown', 'Коричневый', '#6D4C41'),
]

FEATURES = [
    ('conditioner', 'Кондиционер'), ('navigator', 'Навигатор'),
    ('child_seat', 'Детское кресло'), ('parktronic', 'Парктроник'),
    ('camera', 'Камера заднего вида'), ('winter_tires', 'Зимняя резина'),
    ('heated_seats', 'Подогрев сидений'), ('cruise', 'Круиз-контроль'),
    ('carplay', 'CarPlay / Android Auto'), ('panorama', 'Панорамная крыша'),
]

# (код, название, цвет метки, финальный)
BOOKING_STATUSES = [
    ('new', 'Новая', '#1976D2', False),
    ('confirmed', 'Подтверждена', '#7B1FA2', False),
    ('issued', 'Выдана', '#F57C00', False),
    ('completed', 'Завершена', '#388E3C', True),
    ('cancelled', 'Отменена', '#757575', True),
]

BRANDS = [
    ('Audi', 'Германия'), ('BMW', 'Германия'), ('Chevrolet', 'США'), ('Ford', 'США'),
    ('Hyundai', 'Южная Корея'), ('Kia', 'Южная Корея'), ('Lada', 'Россия'),
    ('Maserati', 'Италия'), ('Mercedes-Benz', 'Германия'), ('Porsche', 'Германия'),
    ('Toyota', 'Япония'), ('Volvo', 'Швеция'),
]

# (марка, модель, начало выпуска, конец выпуска)
MODELS = [
    ('Ford', 'Fiesta', 2008, 2023), ('Volvo', 'XC90', 2015, None),
    ('BMW', 'M4 Competition', 2021, None), ('Porsche', '911 Carrera', 2019, None),
    ('BMW', 'M2', 2016, None), ('BMW', '430i Coupe', 2020, None),
    ('Maserati', 'GranTurismo', 2007, 2019), ('Chevrolet', 'Camaro RS', 2016, 2024),
    ('Audi', 'RS 5', 2017, None), ('Hyundai', 'i30 N', 2017, None),
    ('Kia', 'Rio', 2017, None), ('Lada', 'Vesta', 2015, None),
    ('Toyota', 'Camry', 2017, None), ('Mercedes-Benz', 'E 200', 2016, None),
]

# Машины. office — офис приписки; rented=True — машина сейчас у клиента
CARS = [
    dict(reg='А123ВС777', vin='WF0DXXGAKD1A23456', model=('Ford', 'Fiesta'), year=2021,
         cls='econom', body='hatchback', trans='manual', fuel='petrol', color='red',
         engine='1.0', hp=125, seats=5, doors=3, trunk=290, cons='5.2', mileage=64200,
         price=2200, deposit=10000, office=('msk', 'Шереметьево, терминал B'),
         features=['conditioner', 'navigator', 'winter_tires'], photos=['car_1.jpg']),
    dict(reg='В456КМ777', vin='YV1LFA2BCL1234567', model=('Volvo', 'XC90'), year=2022,
         cls='comfort', body='suv', trans='auto', fuel='petrol', color='white',
         engine='2.0', hp=249, seats=7, doors=5, trunk=640, cons='8.5', mileage=38100,
         price=9500, deposit=40000, office=('msk', 'Москва-Сити'), rented=True,
         features=['conditioner', 'navigator', 'child_seat', 'parktronic', 'camera',
                   'heated_seats'], photos=['car_4.jpg']),
    dict(reg='С789ЕТ197', vin='WBS33AZ09PCK12345', model=('BMW', 'M4 Competition'), year=2023,
         cls='business', body='coupe', trans='auto', fuel='petrol', color='black',
         engine='3.0', hp=510, seats=4, doors=2, trunk=440, cons='9.8', mileage=12400,
         price=14000, deposit=100000, office=('msk', 'Домодедово, зал прилёта'),
         features=['conditioner', 'navigator', 'parktronic', 'camera', 'carplay'],
         photos=['car_7.jpg']),
    dict(reg='К555РО178', vin='WP0ZZZ99ZNS123456', model=('Porsche', '911 Carrera'), year=2022,
         cls='sport', body='coupe', trans='robot', fuel='petrol', color='silver',
         engine='3.0', hp=385, seats=4, doors=2, trunk=132, cons='9.0', mileage=19600,
         price=18000, deposit=150000, office=('spb', 'Пулково, зал прилёта'),
         features=['conditioner', 'navigator', 'camera'], photos=['car_2.jpg']),
    dict(reg='М777ТХ178', vin='WBS2U910X07D12345', model=('BMW', 'M2'), year=2021,
         cls='sport', body='coupe', trans='auto', fuel='petrol', color='white',
         engine='3.0', hp=370, seats=4, doors=2, trunk=390, cons='9.5', mileage=44300,
         price=11000, deposit=80000, office=('spb', 'Невский проспект'), rented=True,
         features=['conditioner', 'navigator', 'winter_tires'], photos=['car_5.jpg']),
    dict(reg='Н888УК178', vin='WBA4W310X0FH12345', model=('BMW', '430i Coupe'), year=2020,
         cls='comfort', body='coupe', trans='auto', fuel='petrol', color='blue',
         engine='2.0', hp=252, seats=4, doors=2, trunk=445, cons='7.3', mileage=58700,
         price=7400, deposit=50000, office=('spb', 'Пулково, зал прилёта'),
         features=['conditioner', 'navigator', 'parktronic', 'winter_tires', 'cruise'],
         photos=['car_6.jpg', 'img_2.jpg']),
    dict(reg='Р100ВВ134', vin='ZAM45VLA4K0123456', model=('Maserati', 'GranTurismo'), year=2019,
         cls='sport', body='coupe', trans='auto', fuel='petrol', color='white',
         engine='4.7', hp=460, seats=4, doors=2, trunk=260, cons='14.3', mileage=31500,
         price=22000, deposit=200000, office=('vlg', 'Гумрак, аэропорт'),
         features=['conditioner', 'navigator'], photos=['car_3.jpg']),
    dict(reg='Т222СН134', vin='1G1FB1RX6M0123456', model=('Chevrolet', 'Camaro RS'), year=2021,
         cls='sport', body='cabrio', trans='auto', fuel='petrol', color='black',
         engine='3.6', hp=340, seats=4, doors=2, trunk=198, cons='11.0', mileage=25900,
         price=13000, deposit=90000, office=('vlg', 'Центральный'), status='service',
         features=['conditioner', 'navigator', 'camera'], photos=['img_3.jpg']),
    dict(reg='Е404АМ799', vin='WUAZZZF55JA901234', model=('Audi', 'RS 5'), year=2020,
         cls='business', body='liftback', trans='auto', fuel='petrol', color='lightblue',
         engine='2.9', hp=450, seats=5, doors=5, trunk=465, cons='9.5', mileage=41800,
         price=15000, deposit=120000, office=('msk', 'Внуково, зал прилёта'),
         features=['conditioner', 'navigator', 'parktronic', 'camera', 'heated_seats',
                   'panorama'], photos=['img_1.jpg']),
    dict(reg='О321ХА198', vin='TMAH381CDLJ012345', model=('Hyundai', 'i30 N'), year=2020,
         cls='sport', body='hatchback', trans='manual', fuel='petrol', color='red',
         engine='2.0', hp=275, seats=5, doors=5, trunk=381, cons='8.0', mileage=36500,
         price=8500, deposit=60000, office=('spb', 'Московский вокзал'),
         features=['conditioner', 'carplay', 'cruise'], photos=['img_4.jpg']),
    # новые машины: фотографии ещё не загружены, на главной их не показываем
    dict(reg='У150КЕ134', vin='Z94C251BBNR123456', model=('Kia', 'Rio'), year=2023,
         cls='econom', body='sedan', trans='auto', fuel='petrol', color='grey',
         engine='1.6', hp=123, seats=5, doors=4, trunk=480, cons='6.6', mileage=8700,
         price=2600, deposit=10000, office=('vlg', 'Волгоград-1, вокзал'),
         features=['conditioner', 'heated_seats', 'carplay'], photos=[]),
    dict(reg='Х909МР799', vin='XTAGFL110PY123456', model=('Lada', 'Vesta'), year=2023,
         cls='econom', body='sedan', trans='cvt', fuel='petrol', color='white',
         engine='1.8', hp=122, seats=5, doors=4, trunk=480, cons='7.5', mileage=5200,
         price=2100, deposit=10000, office=('msk', 'Москва-Сити'),
         features=['conditioner', 'heated_seats'], photos=[]),
]

# (email, имя, фамилия, телефон, код роли)
USERS = [
    ('manager.msk@simarent.ru', 'Ольга', 'Морозова', '+7 916 200-10-01', 'manager'),
    ('manager.spb@simarent.ru', 'Дмитрий', 'Лебедев', '+7 921 200-10-02', 'manager'),
    ('ivan.petrov@mail.ru', 'Иван', 'Петров', '+7 903 111-22-01', 'renter'),
    ('anna.smirnova@yandex.ru', 'Анна', 'Смирнова', '+7 905 111-22-02', 'renter'),
    ('sergey.kuznetsov@gmail.com', 'Сергей', 'Кузнецов', '+7 906 111-22-03', 'renter'),
    ('maria.popova@mail.ru', 'Мария', 'Попова', '+7 909 111-22-04', 'renter'),
    ('alexey.volkov@yandex.ru', 'Алексей', 'Волков', '+7 911 111-22-05', 'renter'),
    ('elena.sokolova@gmail.com', 'Елена', 'Соколова', '+7 912 111-22-06', 'renter'),
    ('pavel.novikov@mail.ru', 'Павел', 'Новиков', '+7 915 111-22-07', 'renter'),
    ('olga.fedorova@yandex.ru', 'Ольга', 'Фёдорова', '+7 917 111-22-08', 'renter'),
]

# Учебные аккаунты для проверки сайта: пароль совпадает с почтой
# (email, имя, фамилия, код роли)
ACCOUNTS = [
    ('user@mail.ru', 'Обычный', 'Пользователь', 'renter'),
    ('sima@mail.ru', 'Сима', 'Администратор', 'admin'),
]

# (номер, email клиента, госномер, статус, начало — дней от сегодня, суток,
#  офис получения, офис возврата)
BOOKINGS = [
    ('SR-3F9A21C4', 'ivan.petrov@mail.ru', 'А123ВС777', 'completed', -60, 3,
     ('msk', 'Шереметьево, терминал B'), ('msk', 'Москва-Сити')),
    ('SR-7B2E90D1', 'anna.smirnova@yandex.ru', 'К555РО178', 'completed', -45, 2,
     ('spb', 'Пулково, зал прилёта'), ('spb', 'Пулково, зал прилёта')),
    ('SR-C04D5E66', 'sergey.kuznetsov@gmail.com', 'С789ЕТ197', 'completed', -30, 4,
     ('msk', 'Домодедово, зал прилёта'), ('msk', 'Домодедово, зал прилёта')),
    ('SR-1AA8F3B7', 'maria.popova@mail.ru', 'Р100ВВ134', 'completed', -21, 1,
     ('vlg', 'Гумрак, аэропорт'), ('vlg', 'Центральный')),
    ('SR-5E61C2A9', 'ivan.petrov@mail.ru', 'Н888УК178', 'completed', -14, 5,
     ('spb', 'Пулково, зал прилёта'), ('spb', 'Невский проспект')),
    ('SR-9D3B7740', 'alexey.volkov@yandex.ru', 'Т222СН134', 'cancelled', -7, 2,
     ('vlg', 'Центральный'), ('vlg', 'Центральный')),
    ('SR-2C8E14F5', 'elena.sokolova@gmail.com', 'В456КМ777', 'issued', -2, 6,
     ('msk', 'Москва-Сити'), ('msk', 'Москва-Сити')),
    ('SR-6F0A93BE', 'pavel.novikov@mail.ru', 'М777ТХ178', 'issued', -1, 3,
     ('spb', 'Невский проспект'), ('spb', 'Пулково, зал прилёта')),
    ('SR-8A47D2C3', 'anna.smirnova@yandex.ru', 'Е404АМ799', 'confirmed', 2, 3,
     ('msk', 'Внуково, зал прилёта'), ('msk', 'Шереметьево, терминал B')),
    ('SR-4B95E01F', 'olga.fedorova@yandex.ru', 'О321ХА198', 'confirmed', 4, 2,
     ('spb', 'Московский вокзал'), ('spb', 'Московский вокзал')),
    ('SR-D17C6A28', 'sergey.kuznetsov@gmail.com', 'Р100ВВ134', 'new', 7, 2,
     ('vlg', 'Гумрак, аэропорт'), ('vlg', 'Гумрак, аэропорт')),
    ('SR-E3B05F94', 'maria.popova@mail.ru', 'А123ВС777', 'new', 10, 4,
     ('msk', 'Шереметьево, терминал B'), ('msk', 'Шереметьево, терминал B')),
    ('SR-0A6C3E7D', 'user@mail.ru', 'Х909МР799', 'completed', -10, 2,
     ('msk', 'Москва-Сити'), ('msk', 'Москва-Сити')),
    ('SR-B58F2D61', 'user@mail.ru', 'У150КЕ134', 'confirmed', 3, 3,
     ('vlg', 'Волгоград-1, вокзал'), ('vlg', 'Волгоград-1, вокзал')),
]


def by_code_or_name(model, code, name, **defaults):
    """Справочник: ищем по коду или названию, чтобы не задвоить записи из админки."""
    obj = model.objects.filter(code=code).first() or model.objects.filter(name=name).first()
    if obj:
        return obj
    return model.objects.create(code=code, name=name, **defaults)


class Command(BaseCommand):
    help = 'Наполняет базу демо-данными (справочники, офисы, машины, пользователи, брони)'

    @transaction.atomic
    def handle(self, *args, **options):
        roles = {code: by_code_or_name(Role, code, name, description=desc, sort_order=order)
                 for code, name, desc, order in ROLES}
        cities = {code: by_code_or_name(City, code, name, region=region, sort_order=order)
                  for code, name, region, order in CITIES}

        offices = {}
        for city_code, name, address, phone, hours in OFFICES:
            offices[(city_code, name)], _ = Office.objects.get_or_create(
                city=cities[city_code], name=name,
                defaults={'address': address, 'phone': phone, 'work_hours': hours},
            )

        classes = {}
        for code, name, desc, order in CLASSES:
            car_class = by_code_or_name(CarClass, code, name, description=desc, sort_order=order)
            if not car_class.description:  # класс заведён в админке без описания
                car_class.description = desc
                car_class.save(update_fields=['description'])
            classes[code] = car_class
        bodies = self.dictionary(BodyType, BODY_TYPES)
        transmissions = self.dictionary(TransmissionType, TRANSMISSIONS)
        fuels = self.dictionary(FuelType, FUELS)
        features = self.dictionary(Feature, FEATURES)
        colors = {code: by_code_or_name(Color, code, name, hex=hex_code, sort_order=i)
                  for i, (code, name, hex_code) in enumerate(COLORS, start=1)}
        statuses = {code: by_code_or_name(BookingStatus, code, name, color=color,
                                          final_status=final, sort_order=i)
                    for i, (code, name, color, final) in enumerate(BOOKING_STATUSES, start=1)}

        brands = {name: Brand.objects.get_or_create(name=name, defaults={'country': country})[0]
                  for name, country in BRANDS}
        models = {}
        for brand, name, start, end in MODELS:
            models[(brand, name)], _ = CarModel.objects.get_or_create(
                brand=brands[brand], name=name, defaults={'year_start': start, 'year_end': end},
            )

        cars = {}
        for c in CARS:
            home = offices[c['office']]
            rented = c.get('rented', False)
            car, created = Car.objects.get_or_create(reg_number=c['reg'], defaults=dict(
                vin_number=c['vin'], model=models[c['model']], year=c['year'],
                car_class=classes[c['cls']], body_type=bodies[c['body']],
                transmission_type=transmissions[c['trans']], fuel_type=fuels[c['fuel']],
                color=colors[c['color']], engine_volume=Decimal(c['engine']),
                horsepower=c['hp'], seats_count=c['seats'], doors_count=c['doors'],
                trunk_volume=c['trunk'], fuel_consumption=Decimal(c['cons']),
                mileage=c['mileage'], price_day=c['price'], deposit=c['deposit'],
                home_office=home, current_office=None if rented else home,
                status='rented' if rented else c.get('status', 'available'),
            ))
            if created:
                car.features.set(features[code] for code in c['features'])
                for order, image in enumerate(c['photos']):
                    self.add_photo(car, image, order)
            cars[c['reg']] = car

        users = {}
        for email, first, last, phone, role in USERS:
            user = User.objects.filter(email=email).first()
            if not user:
                user = User.objects.create_user(
                    email, DEMO_PASSWORD, first_name=first, last_name=last,
                    phone=phone, role=roles[role],
                )
            users[email] = user

        for email, first, last, role in ACCOUNTS:
            user = User.objects.filter(email=email).first()
            if not user:
                user = User.objects.create_user(
                    email, email, first_name=first, last_name=last, role=roles[role],
                )
            users[email] = user

        now = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        for number, email, reg, status, start, days, pickup, ret in BOOKINGS:
            if Booking.objects.filter(booking_number=number).exists():
                continue
            date_start = now + timedelta(days=start)
            date_end = date_start + timedelta(days=days)
            booking = Booking(
                booking_number=number, user=users[email], car=cars[reg],
                pickup_office=offices[pickup], return_office=offices[ret],
                date_start=date_start, date_end=date_end, status=statuses[status],
                price_day=None, deposit=None,
            )
            if status in ('confirmed', 'issued', 'completed'):
                booking.date_confirmed = date_start - timedelta(days=1)
                booking.paid = True
            if status in ('issued', 'completed'):
                booking.date_start_fact = date_start
            if status == 'completed':
                booking.date_end_fact = date_end
                booking.return_office_fact = offices[ret]
            if status == 'cancelled':
                booking.date_cancelled = date_start - timedelta(days=2)
            booking.save()

        self.stdout.write(self.style.SUCCESS('Готово. Записей в таблицах:'))
        for model in (User, City, Office, Brand, CarModel, Car, CarPhoto, Booking,
                      CarClass, BodyType, TransmissionType, FuelType, Color, Feature,
                      BookingStatus, Role):
            self.stdout.write(f'  {model._meta.verbose_name_plural}: {model.objects.count()}')

    @staticmethod
    def dictionary(model, rows):
        return {code: by_code_or_name(model, code, name, sort_order=i)
                for i, (code, name) in enumerate(rows, start=1)}

    @staticmethod
    def add_photo(car, image, order):
        photo = CarPhoto(car=car, alt_text=str(car.model), sort_order=order)
        with open(IMAGES / image, 'rb') as f:
            photo.file_path.save(image, File(f), save=False)
        photo.save()
