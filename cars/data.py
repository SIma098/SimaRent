"""Временные данные вместо моделей.

Ключи словарей названы так же, как поля таблиц схемы SimaRent.
Когда появятся модели, этот файл удаляется, а во views подставляются
запросы: Car.available.all(), City.objects.filter(active=True) и т. д.
"""

# таблица cities
CITIES = [
    {'code': 'msk', 'name': 'Москва'},
    {'code': 'spb', 'name': 'Санкт-Петербург'},
    {'code': 'vlg', 'name': 'Волгоград'},
]

# таблица offices (city — связь с cities)
OFFICES = [
    {'id': 1, 'name': 'Шереметьево, терминал B', 'city': 'Москва',
     'address': 'Шереметьевское шоссе, 1', 'phone': '+7 495 100-20-30',
     'work_hours': 'круглосуточно'},
    {'id': 2, 'name': 'Москва-Сити', 'city': 'Москва',
     'address': 'Пресненская набережная, 12', 'phone': '+7 495 100-20-31',
     'work_hours': '08:00 — 22:00'},
    {'id': 3, 'name': 'Домодедово, зал прилёта', 'city': 'Москва',
     'address': 'аэропорт Домодедово, стойка 14', 'phone': '+7 495 100-20-32',
     'work_hours': 'круглосуточно'},
    {'id': 4, 'name': 'Пулково, зал прилёта', 'city': 'Санкт-Петербург',
     'address': 'Пулковское шоссе, 41', 'phone': '+7 812 100-20-30',
     'work_hours': '07:00 — 23:00'},
    {'id': 5, 'name': 'Невский проспект', 'city': 'Санкт-Петербург',
     'address': 'Невский проспект, 114', 'phone': '+7 812 100-20-31',
     'work_hours': '09:00 — 21:00'},
    {'id': 6, 'name': 'Гумрак, аэропорт', 'city': 'Волгоград',
     'address': 'аэропорт Гумрак, терминал 1', 'phone': '+7 8442 50-20-30',
     'work_hours': '06:00 — 23:00'},
    {'id': 7, 'name': 'Центральный', 'city': 'Волгоград',
     'address': 'площадь Павших Борцов, 2', 'phone': '+7 8442 50-20-31',
     'work_hours': '08:00 — 20:00'},
]

# таблица classes
CAR_CLASSES = [
    {'code': 'econom', 'name': 'Эконом', 'icon': 'icon-car',
     'description': 'Компактные машины с малым расходом — для поездок по городу.'},
    {'code': 'comfort', 'name': 'Комфорт', 'icon': 'icon-users',
     'description': 'Автомат и мягкая подвеска — для спокойных и долгих поездок.'},
    {'code': 'business', 'name': 'Бизнес', 'icon': 'icon-diamond',
     'description': 'Статусные автомобили для деловых поездок.'},
    {'code': 'sport', 'name': 'Спорт', 'icon': 'icon-road',
     'description': 'Мощные купе и кабриолеты для тех, кому важна динамика.'},
]

# таблица body_types
BODY_TYPES = [
    {'code': 'hatchback', 'name': 'Хэтчбек'},
    {'code': 'sedan', 'name': 'Седан'},
    {'code': 'coupe', 'name': 'Купе'},
    {'code': 'cabrio', 'name': 'Кабриолет'},
    {'code': 'suv', 'name': 'Внедорожник'},
]

# таблица transmission_types
TRANSMISSION_TYPES = [
    {'code': 'manual', 'name': 'Механика'},
    {'code': 'auto', 'name': 'Автомат'},
]

# таблица fuel_types
FUEL_TYPES = [
    {'code': 'petrol', 'name': 'Бензин'},
    {'code': 'diesel', 'name': 'Дизель'},
]

# таблица features, связана с cars через car_features (многие-ко-многим)
FEATURES = [
    {'code': 'conditioner', 'name': 'Кондиционер', 'icon': 'icon-snowflake-o'},
    {'code': 'navigator', 'name': 'Навигатор', 'icon': 'icon-map-marker'},
    {'code': 'child_seat', 'name': 'Детское кресло', 'icon': 'icon-child'},
    {'code': 'parktronic', 'name': 'Парктроник', 'icon': 'icon-bullhorn'},
    {'code': 'camera', 'name': 'Камера заднего вида', 'icon': 'icon-camera'},
    {'code': 'winter_tires', 'name': 'Зимняя резина', 'icon': 'icon-cogs'},
]

# таблица cars; photos — таблица car_photos, features — связка car_features
CARS = [
    {
        'id': 1, 'brand': 'Ford', 'model': 'Fiesta', 'year': 2021,
        'reg_number': 'А123ВС777', 'vin_number': 'WF0DXXGAKD1A23456',
        'class_name': 'Эконом', 'body_type': 'Хэтчбек',
        'transmission_type': 'Механика', 'fuel_type': 'Бензин', 'color': 'Красный',
        'seats_count': 5, 'doors_count': 3, 'trunk_volume': 290,
        'engine_volume': '1.0', 'horsepower': 125, 'fuel_consumption': '5.2',
        'mileage': 64200, 'price_day': 2200, 'deposit': 10000,
        'office': 'Шереметьево, терминал B', 'city': 'Москва',
        'photos': ['carrentals/images/car_1.jpg'], 'status': 'available',
        'features': ['Кондиционер', 'Навигатор', 'Зимняя резина'],
        'description': 'Самый доступный автомобиль автопарка. '
                       'Лёгкий в управлении, экономит топливо в пробках.',
    },
    {
        'id': 2, 'brand': 'Volvo', 'model': 'XC90', 'year': 2022,
        'reg_number': 'В456КМ777', 'vin_number': 'YV1LFA2BCL1234567',
        'class_name': 'Комфорт', 'body_type': 'Внедорожник',
        'transmission_type': 'Автомат', 'fuel_type': 'Бензин', 'color': 'Белый',
        'seats_count': 7, 'doors_count': 5, 'trunk_volume': 640,
        'engine_volume': '2.0', 'horsepower': 249, 'fuel_consumption': '8.5',
        'mileage': 38100, 'price_day': 9500, 'deposit': 40000,
        'office': 'Москва-Сити', 'city': 'Москва',
        'photos': ['carrentals/images/car_4.jpg'], 'status': 'available',
        'features': ['Кондиционер', 'Навигатор', 'Детское кресло',
                     'Парктроник', 'Камера заднего вида', 'Зимняя резина'],
        'description': 'Семь мест и большой багажник. '
                       'Берут для поездок большой компанией и за город.',
    },
    {
        'id': 3, 'brand': 'BMW', 'model': 'M4 Competition', 'year': 2023,
        'reg_number': 'С789ЕТ197', 'vin_number': 'WBS33AZ09PCK12345',
        'class_name': 'Бизнес', 'body_type': 'Купе',
        'transmission_type': 'Автомат', 'fuel_type': 'Бензин', 'color': 'Чёрный',
        'seats_count': 4, 'doors_count': 2, 'trunk_volume': 440,
        'engine_volume': '3.0', 'horsepower': 510, 'fuel_consumption': '9.8',
        'mileage': 12400, 'price_day': 14000, 'deposit': 100000,
        'office': 'Домодедово, зал прилёта', 'city': 'Москва',
        'photos': ['carrentals/images/car_7.jpg'], 'status': 'available',
        'features': ['Кондиционер', 'Навигатор', 'Парктроник', 'Камера заднего вида'],
        'description': 'Строгий чёрный кузов и 510 сил. '
                       'Подходит и для деловой встречи, и для трассы.',
    },
    {
        'id': 4, 'brand': 'Porsche', 'model': '911 Carrera', 'year': 2022,
        'reg_number': 'К555РО178', 'vin_number': 'WP0ZZZ99ZNS123456',
        'class_name': 'Спорт', 'body_type': 'Купе',
        'transmission_type': 'Автомат', 'fuel_type': 'Бензин', 'color': 'Серебристый',
        'seats_count': 4, 'doors_count': 2, 'trunk_volume': 132,
        'engine_volume': '3.0', 'horsepower': 385, 'fuel_consumption': '9.0',
        'mileage': 19600, 'price_day': 18000, 'deposit': 150000,
        'office': 'Пулково, зал прилёта', 'city': 'Санкт-Петербург',
        'photos': ['carrentals/images/car_2.jpg'], 'status': 'available',
        'features': ['Кондиционер', 'Навигатор', 'Камера заднего вида'],
        'description': 'Классическое спортивное купе. '
                       'Небольшой багажник — рассчитывайте на ручную кладь.',
    },
    {
        'id': 5, 'brand': 'BMW', 'model': 'M2', 'year': 2021,
        'reg_number': 'М777ТХ178', 'vin_number': 'WBS2U910X07D12345',
        'class_name': 'Спорт', 'body_type': 'Купе',
        'transmission_type': 'Автомат', 'fuel_type': 'Бензин', 'color': 'Белый',
        'seats_count': 4, 'doors_count': 2, 'trunk_volume': 390,
        'engine_volume': '3.0', 'horsepower': 370, 'fuel_consumption': '9.5',
        'mileage': 44300, 'price_day': 11000, 'deposit': 80000,
        'office': 'Невский проспект', 'city': 'Санкт-Петербург',
        'photos': ['carrentals/images/car_5.jpg'], 'status': 'available',
        'features': ['Кондиционер', 'Навигатор', 'Зимняя резина'],
        'description': 'Компактное заднеприводное купе. '
                       'Самый доступный спорткар в автопарке.',
    },
    {
        'id': 6, 'brand': 'BMW', 'model': '430i Coupe', 'year': 2020,
        'reg_number': 'Н888УК178', 'vin_number': 'WBA4W310X0FH12345',
        'class_name': 'Комфорт', 'body_type': 'Купе',
        'transmission_type': 'Автомат', 'fuel_type': 'Бензин', 'color': 'Синий',
        'seats_count': 4, 'doors_count': 2, 'trunk_volume': 445,
        'engine_volume': '2.0', 'horsepower': 252, 'fuel_consumption': '7.3',
        'mileage': 58700, 'price_day': 7400, 'deposit': 50000,
        'office': 'Пулково, зал прилёта', 'city': 'Санкт-Петербург',
        # у этой машины две фотографии — так работает таблица car_photos
        'photos': ['carrentals/images/car_6.jpg', 'carrentals/images/img_2.jpg'],
        'status': 'available',
        'features': ['Кондиционер', 'Навигатор', 'Парктроник', 'Зимняя резина'],
        'description': 'Купе с комфортной подвеской и умеренным расходом. '
                       'Компромисс между спортом и повседневной ездой.',
    },
    {
        'id': 7, 'brand': 'Maserati', 'model': 'GranTurismo', 'year': 2020,
        'reg_number': 'Р100ВВ134', 'vin_number': 'ZAM45VLA4L0123456',
        'class_name': 'Спорт', 'body_type': 'Купе',
        'transmission_type': 'Автомат', 'fuel_type': 'Бензин', 'color': 'Белый',
        'seats_count': 4, 'doors_count': 2, 'trunk_volume': 260,
        'engine_volume': '4.7', 'horsepower': 460, 'fuel_consumption': '14.3',
        'mileage': 31500, 'price_day': 22000, 'deposit': 200000,
        'office': 'Гумрак, аэропорт', 'city': 'Волгоград',
        'photos': ['carrentals/images/car_3.jpg'], 'status': 'available',
        'features': ['Кондиционер', 'Навигатор'],
        'description': 'Самый дорогой автомобиль автопарка. '
                       'Атмосферный V8 и высокий расход топлива.',
    },
    {
        'id': 8, 'brand': 'Chevrolet', 'model': 'Camaro RS', 'year': 2021,
        'reg_number': 'Т222СН134', 'vin_number': '1G1FB1RX6M0123456',
        'class_name': 'Спорт', 'body_type': 'Кабриолет',
        'transmission_type': 'Автомат', 'fuel_type': 'Бензин', 'color': 'Чёрный',
        'seats_count': 4, 'doors_count': 2, 'trunk_volume': 198,
        'engine_volume': '3.6', 'horsepower': 340, 'fuel_consumption': '11.0',
        'mileage': 25900, 'price_day': 13000, 'deposit': 90000,
        'office': 'Центральный', 'city': 'Волгоград',
        'photos': ['carrentals/images/img_3.jpg'], 'status': 'available',
        'features': ['Кондиционер', 'Навигатор', 'Камера заднего вида'],
        'description': 'Кабриолет с откидным верхом. '
                       'Берут для фотосессий и поездок в тёплое время года.',
    },
]

# таблица booking_statuses — путь брони от создания до завершения
BOOKING_STEPS = [
    {'code': 'new', 'name': 'Выберите автомобиль',
     'description': 'Укажите город, офис и даты — покажем машины, свободные на эти дни.'},
    {'code': 'confirmed', 'name': 'Подтвердите бронь',
     'description': 'Менеджер проверит заявку и закрепит автомобиль за вами.'},
    {'code': 'issued', 'name': 'Заберите в офисе',
     'description': 'Приезжайте с правами и паспортом — машина уже ждёт.'},
    {'code': 'completed', 'name': 'Верните в любой офис',
     'description': 'Сдайте автомобиль там, где удобно: сеть офисов в трёх городах.'},
]
