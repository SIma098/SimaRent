"""Наполнение базы случайными данными через Faker: python manage.py fake_data

Создаёт клиентов (русские имена, почта, телефон) и бронирования за последний
год и на ближайший месяц — чтобы на дашборде были графики по месяцам.
Справочники, офисы и машины берутся уже существующие (их создаёт seed).

Параметры: --users 50 --bookings 200 --exclude-ids 1 2
(--exclude-ids — машины, на которые случайные брони не создавать, например тестовые)
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from faker import Faker

from cars.models import Booking, BookingStatus, Car, Office, Role, User


class Command(BaseCommand):
    help = 'Создаёт случайных клиентов и бронирования (Faker, ru_RU)'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=50, help='сколько клиентов создать')
        parser.add_argument('--bookings', type=int, default=200, help='сколько броней создать')
        parser.add_argument('--exclude-ids', type=int, nargs='*', default=[],
                            help='ID машин, которые не трогать')

    @transaction.atomic
    def handle(self, *args, **options):
        fake = Faker('ru_RU')
        cars = list(Car.objects.filter(active=True, date_deleted__isnull=True)
                    .exclude(status__in=[Car.Status.RENTED, Car.Status.ARCHIVED])
                    .exclude(pk__in=options['exclude_ids'])
                    .select_related('home_office__city'))
        statuses = {s.code: s for s in BookingStatus.objects.all()}
        renter = Role.objects.filter(code=Role.RENTER).first()
        if not cars or not {'new', 'confirmed', 'completed', 'cancelled'} <= statuses.keys():
            raise CommandError('Сначала заполните справочники и машины: python manage.py seed')

        new_users = [self.fake_user(fake, renter) for _ in range(options['users'])]
        users = list(User.objects.filter(role=renter))  # брони — и новым, и прежним клиентам

        offices_by_city = {}
        for office in Office.objects.filter(active=True):
            offices_by_city.setdefault(office.city_id, []).append(office)

        # уже занятые даты каждой машины — новые брони с ними не пересекаются
        busy = {car.pk: list(Booking.objects.filter(car=car).exclude(status__code='cancelled')
                             .values_list('date_start', 'date_end')) for car in cars}

        now = timezone.now()
        created = 0
        for _ in range(options['bookings'] * 5):  # с запасом: часть дат будет занята
            if created == options['bookings']:
                break
            car = random.choice(cars)
            start = (now - timedelta(days=random.randint(-30, 365))).replace(
                hour=random.choice([9, 10, 12, 14, 16, 18]), minute=0, second=0, microsecond=0)
            end = start + timedelta(days=random.choices([1, 2, 3, 4, 5, 7, 10, 14],
                                                        weights=[20, 25, 20, 12, 10, 7, 4, 2])[0])
            # активные брони только в будущем: выданной машины (в аренде) Faker не создаёт
            if start <= now < end:
                continue
            if any(start < b_end and end > b_start for b_start, b_end in busy[car.pk]):
                continue
            busy[car.pk].append((start, end))

            booking = Booking(
                user=random.choice(users), car=car,
                pickup_office=car.home_office,
                return_office=random.choice(offices_by_city[car.home_office.city_id]),
                date_start=start, date_end=end, price_day=None, deposit=None,
            )
            if end < now:  # прошлое: почти все завершены, часть отменена
                code = random.choices(['completed', 'cancelled'], weights=[85, 15])[0]
            else:          # будущее: новые и подтверждённые
                code = random.choice(['new', 'confirmed'])
            booking.status = statuses[code]
            if code in ('confirmed', 'completed'):
                booking.date_confirmed = start - timedelta(days=random.randint(1, 5))
                booking.paid = code == 'completed' or random.random() < 0.6
            if code == 'completed':
                booking.date_start_fact = start
                booking.date_end_fact = end
                booking.return_office_fact = booking.return_office
            if code == 'cancelled':
                booking.date_cancelled = start - timedelta(days=random.randint(1, 3))
            booking.save()
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Готово: клиентов +{len(new_users)}, броней +{created}. '
            f'Всего: пользователей {User.objects.count()}, броней {Booking.objects.count()}.'
        ))

    @staticmethod
    def fake_user(fake, role):
        """Клиент с уникальными почтой и телефоном; пароля нет — войти на сайт он не может."""
        male = random.random() < 0.5
        while True:
            email = fake.unique.free_email()
            phone = fake.phone_number()
            if not User.objects.filter(email=email).exists() and \
                    not User.objects.filter(phone=phone).exists():
                break
        return User.objects.create_user(
            email, None,
            first_name=fake.first_name_male() if male else fake.first_name_female(),
            last_name=fake.last_name_male() if male else fake.last_name_female(),
            phone=phone, role=role,
        )
