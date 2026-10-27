from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.db.models import Avg, Count, Max, Min, Prefetch, ProtectedError, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import CarForm, OfficeForm, ProfileForm
from .models import Booking, Car, CarClass, CarPhoto, City, Feature, Office, User

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


def active_cities(with_hidden=False):
    """Города вместе с их офисами. with_hidden — показать и скрытые офисы (для админа)."""
    offices = Office.objects.all() if with_hidden else Office.objects.filter(active=True)
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


def visible_cars(user):
    """Клиент видит только действующие машины, сотрудник с правом правки — все."""
    cars = car_cards()
    if user.has_perm('cars.change_car'):
        return cars
    return cars.filter(active=True, date_deleted__isnull=True).exclude(status=Car.Status.ARCHIVED)


def listing(request):
    cars = visible_cars(request.user)
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
    with_hidden = request.user.has_perm('cars.change_office')
    return render(request, 'cars/contact.html', {'cities': active_cities(with_hidden)})


# CRUD автомобилей (каталог): просмотр — всем, остальное — по правам

def car_detail(request, pk):
    """Read: страница одного автомобиля."""
    car = get_object_or_404(visible_cars(request.user).prefetch_related('features'), pk=pk)
    return render(request, 'cars/car_detail.html', {'car': car})


def save_car(request, form, is_new):
    """Общее для создания и изменения: аудит, сохранение, новое фото."""
    car = form.save(commit=False)
    if is_new:
        car.user_created = request.user
    car.user_updated = request.user
    car.save()
    form.save_m2m()  # опции (многие-ко-многим) сохраняются после самой машины
    photo = form.cleaned_data.get('photo')
    if photo:
        CarPhoto.objects.create(
            car=car, file_path=photo, alt_text=str(car.model),
            sort_order=car.photos.count(), user_uploaded=request.user,
        )
    return car


@login_required
@permission_required('cars.add_car', raise_exception=True)
def car_create(request):
    """Create: новый автомобиль."""
    form = CarForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        car = save_car(request, form, is_new=True)
        messages.success(request, f'Автомобиль {car} добавлен.')
        return redirect('cars:car_detail', pk=car.pk)
    return render(request, 'cars/object_form.html', {
        'form': form, 'title': 'Новый автомобиль', 'cancel_url': reverse('cars:listing'),
    })


@login_required
@permission_required('cars.change_car', raise_exception=True)
def car_update(request, pk):
    """Update: изменение автомобиля. Форма открывается уже заполненной (instance=car)."""
    car = get_object_or_404(Car, pk=pk)
    form = CarForm(request.POST or None, request.FILES or None, instance=car)
    if request.method == 'POST' and form.is_valid():
        save_car(request, form, is_new=False)
        messages.success(request, f'Изменения сохранены: {car}.')
        return redirect('cars:car_detail', pk=car.pk)
    return render(request, 'cars/object_form.html', {
        'form': form, 'title': f'Изменить: {car}', 'cancel_url': car.get_absolute_url(),
    })


@login_required
@permission_required('cars.delete_car', raise_exception=True)
def car_delete(request, pk):
    """Delete: GET — страница подтверждения, POST — удаление.

    Машину с историей бронирований удалить нельзя (брони ссылаются на неё),
    поэтому такая машина уходит в архив: на сайте её больше не видно.
    """
    car = get_object_or_404(Car, pk=pk)
    has_bookings = car.bookings.exists()
    if request.method == 'POST':
        if car.status == Car.Status.RENTED:
            messages.error(request, 'Машина сейчас в аренде — удалить её нельзя.')
            return redirect('cars:car_detail', pk=car.pk)
        if has_bookings:
            car.status = Car.Status.ARCHIVED
            car.active = False
            car.date_deleted = timezone.now()
            car.user_updated = request.user
            car.save()
            messages.success(request, f'{car}: есть брони, поэтому машина перенесена в архив.')
        else:
            for photo in car.photos.all():
                photo.file_path.delete(save=False)  # файл фото с диска
            name = str(car)
            car.delete()
            messages.success(request, f'Автомобиль {name} удалён.')
        return redirect('cars:listing')
    return render(request, 'cars/confirm_delete.html', {
        'object': car, 'title': f'Удалить {car}?',
        'warning': 'У машины есть бронирования — она будет перенесена в архив.'
                   if has_bookings else 'Машина и её фотографии будут удалены навсегда.',
        'cancel_url': car.get_absolute_url(),
    })


# CRUD офисов (страница «Контакты»)

@login_required
@permission_required('cars.add_office', raise_exception=True)
def office_create(request):
    form = OfficeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        office = form.save(commit=False)
        office.user_created = office.user_updated = request.user
        office.save()
        messages.success(request, f'Офис «{office.name}» добавлен.')
        return redirect('cars:contact')
    return render(request, 'cars/object_form.html', {
        'form': form, 'title': 'Новый офис', 'cancel_url': reverse('cars:contact'),
    })


@login_required
@permission_required('cars.change_office', raise_exception=True)
def office_update(request, pk):
    office = get_object_or_404(Office, pk=pk)
    form = OfficeForm(request.POST or None, instance=office)
    if request.method == 'POST' and form.is_valid():
        office = form.save(commit=False)
        office.user_updated = request.user
        office.save()
        messages.success(request, f'Офис «{office.name}» сохранён.')
        return redirect('cars:contact')
    return render(request, 'cars/object_form.html', {
        'form': form, 'title': f'Изменить офис: {office.name}',
        'cancel_url': reverse('cars:contact'),
    })


@login_required
@permission_required('cars.delete_office', raise_exception=True)
def office_delete(request, pk):
    """К офису привязаны машины и брони (PROTECT), такой офис только скрываем."""
    office = get_object_or_404(Office, pk=pk)
    if request.method == 'POST':
        try:
            office.delete()
            messages.success(request, f'Офис «{office.name}» удалён.')
        except ProtectedError:
            office.active = False
            office.user_updated = request.user
            office.save()
            messages.warning(
                request, f'К офису «{office.name}» привязаны машины или брони, '
                         f'поэтому он не удалён, а скрыт с сайта.',
            )
        return redirect('cars:contact')
    return render(request, 'cars/confirm_delete.html', {
        'object': office, 'title': f'Удалить офис «{office.name}»?',
        'warning': 'Если к офису привязаны машины или брони, он будет скрыт, а не удалён.',
        'cancel_url': reverse('cars:contact'),
    })


# Личный кабинет: пользователь меняет свои данные

@login_required
def profile(request):
    """Read + Update своего профиля: имя, фамилия, телефон.

    Чтобы удалить телефон, достаточно стереть поле и сохранить —
    форма запишет в базу пустое значение (NULL).
    """
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Данные сохранены.')
        return redirect('cars:profile')
    bookings = (
        Booking.objects.filter(user=request.user)
        .select_related('car__model__brand', 'status', 'pickup_office')
        .order_by('-date_start')
    )
    return render(request, 'cars/profile.html', {'form': form, 'bookings': bookings})


# Дашборд: статистика и графики — только для администратора

MONTHS = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']


def month_starts(count):
    """Первые числа последних count месяцев, от старого к новому."""
    first = timezone.localtime().date().replace(day=1)
    months = []
    for _ in range(count):
        months.append(first)
        first = (first - timedelta(days=1)).replace(day=1)
    return months[::-1]


@login_required
@user_passes_test(lambda user: user.is_superuser)
def dashboard(request):
    paid = Q(paid=True)

    # Плитки сверху: aggregate по всем броням
    totals = Booking.objects.aggregate(
        count=Count('booking_id'),
        revenue=Sum('total_sum', filter=paid),
        average=Avg('total_sum', filter=paid),
        days=Avg('days_count'),
        cancelled=Count('booking_id', filter=Q(status__code='cancelled')),
    )
    clients = User.objects.filter(bookings__isnull=False).distinct().count()

    # График 1. Брони и выручка по месяцам: TruncMonth + values + annotate = GROUP BY месяц
    months = month_starts(12)
    by_month = {
        row['month'].date() if hasattr(row['month'], 'date') else row['month']: row
        for row in Booking.objects.filter(date_start__date__gte=months[0])
        .annotate(month=TruncMonth('date_start'))
        .values('month')
        .annotate(count=Count('booking_id'), revenue=Sum('total_sum', filter=paid))
    }
    monthly = {
        'labels': [f'{MONTHS[m.month - 1]} {m:%y}' for m in months],
        'count': [by_month.get(m, {}).get('count', 0) for m in months],
        'revenue': [float(by_month.get(m, {}).get('revenue') or 0) for m in months],
    }

    # График 2. Машины по статусам (круговая)
    status_names = dict(Car.Status.choices)
    status_colors = {'available': '#28a745', 'rented': '#ffc107',
                     'service': '#fd7e14', 'archived': '#6c757d'}
    by_status = Car.objects.values('status').annotate(n=Count('car_id')).order_by('status')
    cars_chart = {
        'labels': [status_names[row['status']] for row in by_status],
        'data': [row['n'] for row in by_status],
        'colors': [status_colors[row['status']] for row in by_status],
    }

    # График 3. Выручка по классам автомобилей (гистограмма)
    by_class = (
        Booking.objects.filter(paid)
        .values('car__car_class__name')
        .annotate(revenue=Sum('total_sum'), count=Count('booking_id'))
        .order_by('-revenue')
    )
    class_chart = {
        'labels': [row['car__car_class__name'] for row in by_class],
        'data': [float(row['revenue']) for row in by_class],
    }

    # Загрузка офисов — прогресс-бары: сколько выдач в каждом офисе
    offices = (
        Office.objects.select_related('city')
        .annotate(pickups_count=Count('pickups'))
        .order_by('-pickups_count')
    )
    max_pickups = max((office.pickups_count for office in offices), default=0)

    # Топ клиентов по сумме оплаченных броней
    top_clients = (
        User.objects.annotate(
            spent=Sum('bookings__total_sum', filter=Q(bookings__paid=True)),
            trips=Count('bookings'),
        )
        .filter(spent__isnull=False)
        .order_by('-spent')[:5]
    )

    # Последние брони — в шаблоне группируются по статусу тегом {% regroup %}
    recent = (
        Booking.objects.select_related('user', 'car__model__brand', 'status', 'pickup_office')
        .order_by('-date_created')[:12]
    )
    recent = sorted(recent, key=lambda b: (b.status.sort_order, -b.date_created.timestamp()))

    return render(request, 'cars/dashboard.html', {
        'totals': totals,
        'clients': clients,
        'cars_total': Car.objects.count(),
        'monthly': monthly,
        'cars_chart': cars_chart,
        'class_chart': class_chart,
        'by_class': by_class,
        'offices': offices,
        'max_pickups': max_pickups,
        'top_clients': top_clients,
        'recent': recent,
    })
