from datetime import timedelta

from django.db.models import Avg, Count, Max, Min, Prefetch, Q, Sum
from django.shortcuts import render
from django.utils import timezone

from .models import Booking, Car, CarClass, City, Feature, Office

# Иконки классов и опций — оформление сайта, а не данные, поэтому не в базе
CLASS_ICONS = {
    'econom': 'icon-car', 'comfort': 'icon-users',
    'business': 'icon-diamond', 'sport': 'icon-road',
}
FEATURE_ICONS = {
    'conditioner': 'icon-snowflake-o', 'navigator': 'icon-map-marker',
    'child_seat': 'icon-child', 'parktronic': 'icon-bullhorn',
    'camera': 'icon-camera', 'winter_tires': 'icon-cogs',
    'heated_seats': 'icon-fire', 'cruise': 'icon-tachometer',
    'carplay': 'icon-mobile', 'panorama': 'icon-sun-o',
}

BOOKING_STEPS = [
    ('Выберите автомобиль',
     'Укажите город, офис и даты — покажем машины, свободные на эти дни.'),
    ('Подтвердите бронь', 'Менеджер проверит заявку и закрепит автомобиль за вами.'),
    ('Заберите в офисе', 'Приезжайте с правами и паспортом — машина уже ждёт.'),
    ('Верните в любой офис', 'Сдайте автомобиль там, где удобно: в любом офисе сети.'),
]


def car_cards():
    """Машины со всем, что нужно карточке: связанные таблицы одним запросом плюс фото."""
    return (
        Car.objects
        .select_related('model__brand', 'car_class', 'body_type', 'transmission_type',
                        'fuel_type', 'current_office__city')
        .prefetch_related('photos')
    )


def active_cities():
    """Города вместе с их офисами (форма подбора, «О компании», контакты)."""
    offices = Office.objects.filter(active=True)
    return City.objects.filter(active=True).prefetch_related(Prefetch('offices', queryset=offices))


def add_icons(items, icons, default):
    for item in items:
        item.icon = icons.get(item.code, default)
    return items


def home(request):
    now = timezone.now()

    # Виджет 1. «Свободные автомобили»: filter + exclude + distinct + order_by + срез
    free_cars = (
        car_cards()
        .filter(status=Car.Status.AVAILABLE, active=True, date_deleted__isnull=True)
        .exclude(photos__isnull=True)  # машины без фото на главную не выводим
        .distinct()
        .order_by('price_day')[:6]
    )

    # Виджет 2. «Классы автомобилей»: annotate — у каждого класса число машин и цена «от»
    car_classes = add_icons(
        CarClass.objects.filter(active=True)
        .annotate(
            cars_count=Count('cars', filter=Q(cars__active=True)),
            price_from=Min('cars__price_day', filter=Q(cars__active=True)),
        )
        .filter(cars_count__gt=0),
        CLASS_ICONS, 'icon-car',
    )

    # Виджет 3. «SimaRent в цифрах»: aggregate — итог по всей таблице одним словарём
    fleet = Car.objects.filter(active=True, date_deleted__isnull=True).aggregate(
        total=Count('car_id'),
        free=Count('car_id', filter=Q(status=Car.Status.AVAILABLE)),
        rented=Count('car_id', filter=Q(status=Car.Status.RENTED)),
        price_min=Min('price_day'),
        price_avg=Avg('price_day'),
        horsepower_max=Max('horsepower'),
    )
    trips = Booking.objects.filter(status__code='completed').aggregate(
        count=Count('booking_id'), days=Sum('days_count'),
    )

    # Офисы для карусели; annotate — сколько машин стоит в офисе прямо сейчас
    offices = (
        Office.objects.filter(active=True)
        .select_related('city')
        .annotate(cars_now_count=Count('cars_now', filter=Q(cars_now__active=True)))
        .order_by('city__sort_order', '-cars_now_count', 'name')
    )

    features = add_icons(
        Feature.objects.filter(active=True).annotate(cars_count=Count('cars')),
        FEATURE_ICONS, 'icon-check',
    )

    context = {
        'cities': active_cities(),
        'cities_total': City.objects.filter(active=True).count(),
        'offices_total': len(offices),
        'free_cars': free_cars,
        'car_classes': car_classes,
        'fleet': fleet,
        'trips': trips,
        'offices': offices,
        'features': features,
        'booking_steps': BOOKING_STEPS,
    }

    # Блоки по правам пользователя
    user = request.user
    if user.is_authenticated:
        # любой вошедший — свои бронирования
        context['my_bookings'] = (
            Booking.objects.filter(user=user)
            .select_related('car__model__brand', 'status', 'pickup_office')
            .order_by('-date_start')[:5]
        )
    if user.has_perm('cars.view_booking'):
        # менеджер и админ (есть право смотреть брони) — выдачи на ближайшую неделю
        context['upcoming'] = (
            Booking.objects
            .filter(status__final_status=False, date_start__range=(now, now + timedelta(days=7)))
            .exclude(status__code='issued')
            .select_related('user', 'car__model__brand', 'pickup_office', 'status')
            .order_by('date_start')
        )
    if user.is_superuser:
        # только суперюзер — выручка и разбивка броней по статусам
        context['revenue'] = Booking.objects.filter(paid=True).aggregate(
            total=Sum('total_sum'), average=Avg('total_sum'), count=Count('booking_id'),
        )
        context['by_status'] = (
            Booking.objects.values('status__name', 'status__color')
            .annotate(count=Count('booking_id'), total=Sum('total_sum'))
            .order_by('status__sort_order')
        )

    return render(request, 'cars/home.html', context)


def listing(request):
    cars = (
        car_cards()
        .filter(active=True, date_deleted__isnull=True)
        .exclude(status=Car.Status.ARCHIVED)
    )
    return render(request, 'cars/listing.html', {'cars': cars, 'cars_total': cars.count()})


def about(request):
    context = {
        'cities': active_cities(),
        'car_classes': add_icons(CarClass.objects.filter(active=True), CLASS_ICONS, 'icon-car'),
        'cars_total': Car.objects.filter(active=True, date_deleted__isnull=True).count(),
        'offices_total': Office.objects.filter(active=True).count(),
        'cities_total': City.objects.filter(active=True).count(),
    }
    return render(request, 'cars/about.html', context)


def contact(request):
    return render(request, 'cars/contact.html', {'cities': active_cities()})
