import math
import os
import uuid
from decimal import Decimal

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

# Сообщения для проверок числовых полей
MUST_BE_POSITIVE = 'Значение должно быть больше 0.'
MUST_NOT_BE_NEGATIVE = 'Значение не может быть отрицательным.'

# Пользователи и роли

class Role(models.Model):
    ADMIN = 'admin'
    MANAGER = 'manager'
    RENTER = 'renter'

    role_id = models.AutoField('ID роли', primary_key=True)
    code = models.CharField('Код', max_length=30, unique=True)
    name = models.CharField('Название', max_length=100)
    description = models.TextField('Описание', blank=True)
    sort_order = models.PositiveSmallIntegerField('Порядок сортировки', default=0)

    class Meta:
        db_table = 'roles'
        ordering = ['sort_order', 'name']
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    """Создание пользователей. Вход в систему — по email, а не по логину."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Укажите электронную почту')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        role_model = self.model._meta.get_field('role').related_model
        admin_role, _ = role_model.objects.get_or_create(
            code=Role.ADMIN, defaults={'name': 'Администратор', 'sort_order': 1},
        )
        extra_fields.setdefault('role', admin_role)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser):

    MANAGER_MODELS = {'car', 'carphoto', 'booking'}

    user_id = models.AutoField('ID пользователя', primary_key=True)
    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, null=True, blank=True,
        related_name='users', verbose_name='Роль',
    )
    email = models.EmailField('Электронная почта', unique=True)
    phone = models.CharField('Телефон', max_length=20, unique=True, null=True, blank=True)
    first_name = models.CharField('Имя', max_length=100)
    last_name = models.CharField('Фамилия', max_length=100)
    blocked = models.BooleanField('Заблокирован', default=False)
    # Django сам обновляет last_login при входе; в базе это столбец date_last_login
    last_login = models.DateTimeField(
        'Дата последнего входа', null=True, blank=True, db_column='date_last_login',
    )
    date_created = models.DateTimeField('Дата создания', auto_now_add=True)
    date_updated = models.DateTimeField('Дата изменения', auto_now=True)
    user_created = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', db_column='user_created', verbose_name='Кто создал',
    )
    user_updated = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', db_column='user_updated', verbose_name='Кто изменил',
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        ordering = ['last_name', 'first_name']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.email


    @property
    def is_active(self):
        return not self.blocked

    @property
    def is_staff(self):
        return self.role_id is not None and self.role.code in (Role.ADMIN, Role.MANAGER)

    @property
    def is_superuser(self):
        return self.role_id is not None and self.role.code == Role.ADMIN

    def has_perm(self, perm, obj=None):
        if not (self.is_active and self.is_staff):
            return False
        if self.is_superuser:
            return True
        app_label, _, codename = perm.partition('.')
        action, _, model_name = codename.partition('_')
        if app_label != 'cars':
            return False
        return model_name in self.MANAGER_MODELS or action == 'view'

    def has_perms(self, perm_list, obj=None):
        return all(self.has_perm(perm, obj) for perm in perm_list)

    def has_module_perms(self, app_label):
        if not (self.is_active and self.is_staff):
            return False
        return self.is_superuser or app_label == 'cars'


class AuditModel(models.Model):
    """Служебные поля: когда и кем запись создана и изменена.

    Даты проставляются автоматически, пользователей заполняет админка
    в момент сохранения.
    """

    date_created = models.DateTimeField('Дата создания', auto_now_add=True)
    date_updated = models.DateTimeField('Дата изменения', auto_now=True)
    user_created = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', db_column='user_created', verbose_name='Кто создал',
    )
    user_updated = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', db_column='user_updated', verbose_name='Кто изменил',
    )

    class Meta:
        abstract = True


# География

class City(models.Model):
    city_id = models.AutoField('ID города', primary_key=True)
    code = models.CharField('Код', max_length=30, unique=True)
    name = models.CharField('Название', max_length=100)
    region = models.CharField('Регион', max_length=100, blank=True)
    sort_order = models.PositiveSmallIntegerField('Порядок сортировки', default=0)
    active = models.BooleanField('Активен', default=True)

    class Meta:
        db_table = 'cities'
        ordering = ['sort_order', 'name']
        verbose_name = 'Город'
        verbose_name_plural = 'Города'

    def __str__(self):
        return self.name


class Office(AuditModel):
    office_id = models.AutoField('ID офиса', primary_key=True)
    city = models.ForeignKey(
        City, on_delete=models.PROTECT, related_name='offices', verbose_name='Город',
    )
    name = models.CharField('Название', max_length=120)
    address = models.CharField('Адрес', max_length=300)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    latitude = models.DecimalField(
        'Широта', max_digits=9, decimal_places=6, null=True, blank=True,
    )
    longitude = models.DecimalField(
        'Долгота', max_digits=9, decimal_places=6, null=True, blank=True,
    )
    work_hours = models.CharField('Часы работы', max_length=100, blank=True)
    active = models.BooleanField('Активен', default=True)

    class Meta:
        db_table = 'offices'
        ordering = ['city__sort_order', 'name']
        verbose_name = 'Офис'
        verbose_name_plural = 'Офисы'

    def __str__(self):
        return f'{self.city}, {self.name}'


# Справочники автомобиля

class Brand(models.Model):
    brand_id = models.AutoField('ID марки', primary_key=True)
    name = models.CharField('Название', max_length=100, unique=True)
    country = models.CharField('Страна', max_length=100, blank=True)
    active = models.BooleanField('Активна', default=True)

    class Meta:
        db_table = 'brands'
        ordering = ['name']
        verbose_name = 'Марка'
        verbose_name_plural = 'Марки'

    def __str__(self):
        return self.name


class CarModel(models.Model):
    model_id = models.AutoField('ID модели', primary_key=True)
    brand = models.ForeignKey(
        Brand, on_delete=models.PROTECT, related_name='car_models', verbose_name='Марка',
    )
    name = models.CharField('Название', max_length=100)
    year_start = models.PositiveSmallIntegerField('Год начала выпуска', null=True, blank=True)
    year_end = models.PositiveSmallIntegerField('Год окончания выпуска', null=True, blank=True)
    active = models.BooleanField('Активна', default=True)

    class Meta:
        db_table = 'models'
        ordering = ['brand__name', 'name']
        verbose_name = 'Модель'
        verbose_name_plural = 'Модели'
        constraints = [
            models.UniqueConstraint(fields=['brand', 'name'], name='unique_model_per_brand'),
            models.CheckConstraint(
                condition=Q(year_end__isnull=True) | Q(year_end__gte=F('year_start')),
                name='model_years_valid',
                violation_error_message='Год окончания выпуска не может быть раньше начала.',
            ),
        ]

    def __str__(self):
        return f'{self.brand} {self.name}'


class DictionaryModel(models.Model):
    """Общие поля простых справочников: код, название, порядок, активность."""

    code = models.CharField('Код', max_length=30, unique=True)
    name = models.CharField('Название', max_length=100)
    sort_order = models.PositiveSmallIntegerField('Порядок сортировки', default=0)
    active = models.BooleanField('Активен', default=True)

    class Meta:
        abstract = True
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class CarClass(DictionaryModel):
    class_id = models.AutoField('ID класса', primary_key=True)
    description = models.TextField('Описание', blank=True)

    class Meta(DictionaryModel.Meta):
        db_table = 'classes'
        verbose_name = 'Класс автомобиля'
        verbose_name_plural = 'Классы автомобилей'


class BodyType(DictionaryModel):
    body_type_id = models.AutoField('ID типа кузова', primary_key=True)

    class Meta(DictionaryModel.Meta):
        db_table = 'body_types'
        verbose_name = 'Тип кузова'
        verbose_name_plural = 'Типы кузова'


class TransmissionType(DictionaryModel):
    transmission_type_id = models.AutoField('ID типа коробки', primary_key=True)

    class Meta(DictionaryModel.Meta):
        db_table = 'transmission_types'
        verbose_name = 'Тип коробки передач'
        verbose_name_plural = 'Типы коробки передач'


class FuelType(DictionaryModel):
    fuel_type_id = models.AutoField('ID типа топлива', primary_key=True)

    class Meta(DictionaryModel.Meta):
        db_table = 'fuel_types'
        verbose_name = 'Тип топлива'
        verbose_name_plural = 'Типы топлива'


class Color(DictionaryModel):
    color_id = models.AutoField('ID цвета', primary_key=True)
    hex = models.CharField('Код цвета HEX', max_length=7, blank=True, help_text='Например, #FF0000')

    class Meta(DictionaryModel.Meta):
        db_table = 'colors'
        verbose_name = 'Цвет'
        verbose_name_plural = 'Цвета'


class Feature(DictionaryModel):
    feature_id = models.AutoField('ID опции', primary_key=True)

    class Meta(DictionaryModel.Meta):
        db_table = 'features'
        verbose_name = 'Опция'
        verbose_name_plural = 'Опции'



# Автомобили

class PositiveCountField(models.PositiveSmallIntegerField):
    """Целое число строго больше нуля: мощность, места, двери, багажник.

    Обычное поле разрешает 0 и в форме пишет «больше либо равно 0»;
    здесь форма сразу требует минимум 1 и пишет понятное сообщение.
    """

    def formfield(self, **kwargs):
        kwargs.setdefault('min_value', 1)
        kwargs.setdefault('error_messages', {'min_value': MUST_BE_POSITIVE})
        return super().formfield(**kwargs)


class AvailableCarManager(models.Manager):
    """Машины, которые можно показать в каталоге: свободны, активны, не удалены."""

    def get_queryset(self):
        return super().get_queryset().filter(
            status=Car.Status.AVAILABLE, active=True, date_deleted__isnull=True,
        )


class Car(AuditModel):
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Свободна'
        RENTED = 'rented', 'В аренде'
        SERVICE = 'service', 'На обслуживании'
        ARCHIVED = 'archived', 'В архиве'

    car_id = models.AutoField('ID автомобиля', primary_key=True)
    model = models.ForeignKey(
        CarModel, on_delete=models.PROTECT, related_name='cars', verbose_name='Модель',
    )
    car_class = models.ForeignKey(
        CarClass, on_delete=models.PROTECT, related_name='cars',
        db_column='class_id', verbose_name='Класс',
    )
    body_type = models.ForeignKey(
        BodyType, on_delete=models.PROTECT, related_name='cars', verbose_name='Тип кузова',
    )
    transmission_type = models.ForeignKey(
        TransmissionType, on_delete=models.PROTECT, related_name='cars',
        verbose_name='Коробка передач',
    )
    fuel_type = models.ForeignKey(
        FuelType, on_delete=models.PROTECT, related_name='cars', verbose_name='Тип топлива',
    )
    color = models.ForeignKey(
        Color, on_delete=models.PROTECT, related_name='cars', verbose_name='Цвет',
    )
    home_office = models.ForeignKey(
        Office, on_delete=models.PROTECT, related_name='cars_home',
        verbose_name='Офис приписки',
    )
    current_office = models.ForeignKey(
        Office, on_delete=models.PROTECT, related_name='cars_now', null=True, blank=True,
        verbose_name='Офис, где машина сейчас',
        help_text='Пусто, пока машина в аренде',
    )
    # Связь многие-ко-многим. Промежуточная таблица car_features создаётся сама.
    features = models.ManyToManyField(
        Feature, related_name='cars', blank=True, db_table='car_features',
        verbose_name='Опции',
    )
    reg_number = models.CharField('Госномер', max_length=15, unique=True)
    vin_number = models.CharField('VIN', max_length=17, unique=True)
    year = models.PositiveSmallIntegerField('Год выпуска')
    engine_volume = models.DecimalField(
        'Объём двигателя, л', max_digits=3, decimal_places=1,
        validators=[MinValueValidator(Decimal('0.1'), MUST_BE_POSITIVE)],
    )
    horsepower = PositiveCountField(
        'Мощность, л.с.', validators=[MinValueValidator(1, MUST_BE_POSITIVE)],
    )
    seats_count = PositiveCountField(
        'Количество мест', validators=[MinValueValidator(1, MUST_BE_POSITIVE)],
    )
    doors_count = PositiveCountField(
        'Количество дверей', validators=[MinValueValidator(1, MUST_BE_POSITIVE)],
    )
    trunk_volume = PositiveCountField(
        'Объём багажника, л', validators=[MinValueValidator(1, MUST_BE_POSITIVE)],
    )
    fuel_consumption = models.DecimalField(
        'Расход топлива, л/100 км', max_digits=4, decimal_places=1,
        validators=[MinValueValidator(Decimal('0.1'), MUST_BE_POSITIVE)],
    )
    mileage = models.PositiveIntegerField('Пробег, км', default=0)  # может быть 0 — новая машина
    price_day = models.DecimalField(
        'Цена за сутки, ₽', max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'), MUST_BE_POSITIVE)],
    )
    deposit = models.DecimalField(
        'Залог, ₽', max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0, MUST_NOT_BE_NEGATIVE)],
        help_text='Может быть 0 — без залога',
    )
    status = models.CharField(
        'Статус', max_length=20, choices=Status.choices, default=Status.AVAILABLE,
    )
    active = models.BooleanField('Активен', default=True)
    date_deleted = models.DateTimeField('Дата удаления', null=True, blank=True)

    objects = models.Manager()
    available = AvailableCarManager()

    class Meta:
        db_table = 'cars'
        ordering = ['model__brand__name', 'model__name']
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'
        constraints = [
            # машина в аренде — не в офисе; в любом другом статусе — в офисе
            models.CheckConstraint(
                condition=(
                    Q(status='rented', current_office__isnull=True)
                    | (~Q(status='rented') & Q(current_office__isnull=False))
                ),
                name='car_rented_has_no_office',
                violation_error_message=(
                    'У машины в аренде офис должен быть пустым, '
                    'а в остальных статусах — заполнен.'
                ),
            ),
        ]

    def __str__(self):
        return f'{self.model} {self.reg_number}'

    def clean(self):
        super().clean()
        # год выпуска машины должен попадать в годы, когда выпускалась модель
        if not (self.model_id and self.year):
            return
        start, end = self.model.year_start, self.model.year_end
        if (start and self.year < start) or (end and self.year > end):
            period = f'{start or "?"}–{end}' if end else f'с {start}'
            raise ValidationError({
                'year': f'Модель {self.model} выпускалась {period} г. '
                        f'Год выпуска машины должен попадать в эти годы.',
            })


def car_photo_path(instance, filename):
    return f'cars/{instance.car_id}/{filename}'


class CarPhoto(models.Model):
    photo_id = models.AutoField('ID фотографии', primary_key=True)
    car = models.ForeignKey(
        Car, on_delete=models.CASCADE, related_name='photos', verbose_name='Автомобиль',
    )
    # В базе хранится путь к файлу, сам файл лежит в папке media/
    file_path = models.ImageField('Файл', upload_to=car_photo_path, max_length=255)
    file_name = models.CharField('Исходное имя файла', max_length=255, blank=True)
    file_format = models.CharField('Формат', max_length=10, blank=True)
    file_size = models.PositiveIntegerField('Размер, байт', null=True, blank=True)
    alt_text = models.CharField('Подпись', max_length=255, blank=True)
    sort_order = models.PositiveSmallIntegerField('Порядок', default=0)
    user_uploaded = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', db_column='user_uploaded', verbose_name='Кто загрузил',
    )
    date_created = models.DateTimeField('Дата загрузки', auto_now_add=True)

    class Meta:
        db_table = 'car_photos'
        ordering = ['car', 'sort_order']
        verbose_name = 'Фотография автомобиля'
        verbose_name_plural = 'Фотографии автомобилей'

    def __str__(self):
        return self.file_name or f'Фото {self.photo_id}'

    def save(self, *args, **kwargs):
        # имя, формат и размер берутся из загруженного файла, руками не вводятся
        if self.file_path and not self.file_name:
            name = os.path.basename(self.file_path.name)
            self.file_name = name
            self.file_format = os.path.splitext(name)[1].lstrip('.').lower()
            self.file_size = self.file_path.size
        super().save(*args, **kwargs)


# Бронирования

class BookingStatus(models.Model):
    status_id = models.AutoField('ID статуса', primary_key=True)
    code = models.CharField('Код', max_length=30, unique=True)
    name = models.CharField('Название', max_length=100)
    color = models.CharField('Цвет метки HEX', max_length=7, blank=True)
    final_status = models.BooleanField(
        'Финальный статус', default=False,
        help_text='После него бронь больше не меняется',
    )
    sort_order = models.PositiveSmallIntegerField('Порядок сортировки', default=0)

    class Meta:
        db_table = 'booking_statuses'
        ordering = ['sort_order']
        verbose_name = 'Статус бронирования'
        verbose_name_plural = 'Статусы бронирования'

    def __str__(self):
        return self.name


class Booking(AuditModel):
    booking_id = models.AutoField('ID бронирования', primary_key=True)
    booking_number = models.CharField('Номер брони', max_length=20, unique=True, blank=True)
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='bookings', verbose_name='Арендатор',
    )
    car = models.ForeignKey(
        Car, on_delete=models.PROTECT, related_name='bookings', verbose_name='Автомобиль',
    )
    pickup_office = models.ForeignKey(
        Office, on_delete=models.PROTECT, related_name='pickups',
        verbose_name='Офис получения',
    )
    return_office = models.ForeignKey(
        Office, on_delete=models.PROTECT, related_name='returns_planned',
        verbose_name='Офис возврата по плану',
    )
    return_office_fact = models.ForeignKey(
        Office, on_delete=models.PROTECT, related_name='returns_fact',
        null=True, blank=True, verbose_name='Офис возврата по факту',
    )
    date_start = models.DateTimeField('Начало аренды')
    date_end = models.DateTimeField('Окончание аренды')
    days_count = models.PositiveSmallIntegerField('Количество суток')
    # снимок цены и залога на момент брони: если тариф машины поменяют,
    # уже оформленная бронь не изменится
    price_day = models.DecimalField('Цена за сутки, ₽', max_digits=10, decimal_places=2)
    total_sum = models.DecimalField('Стоимость аренды, ₽', max_digits=12, decimal_places=2)
    deposit = models.DecimalField('Залог, ₽', max_digits=10, decimal_places=2)
    paid = models.BooleanField('Оплачено', default=False)
    status = models.ForeignKey(
        BookingStatus, on_delete=models.PROTECT, related_name='bookings',
        verbose_name='Статус',
    )
    date_confirmed = models.DateTimeField('Дата подтверждения', null=True, blank=True)
    date_start_fact = models.DateTimeField('Фактическая выдача', null=True, blank=True)
    date_end_fact = models.DateTimeField('Фактический возврат', null=True, blank=True)
    date_cancelled = models.DateTimeField('Дата отмены', null=True, blank=True)

    class Meta:
        db_table = 'bookings'
        ordering = ['-date_start']
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        indexes = [
            # для проверки занятости машины на даты
            models.Index(fields=['car', 'date_start', 'date_end'], name='booking_car_dates_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(date_end__gt=F('date_start')),
                name='booking_dates_valid',
                violation_error_message='Окончание аренды должно быть позже начала.',
            ),
        ]

    def __str__(self):
        return self.booking_number or f'Бронь {self.booking_id}'

    def save(self, *args, **kwargs):
        # номер, количество суток и стоимость считаются сами
        if not self.booking_number:
            self.booking_number = f'SR-{uuid.uuid4().hex[:8].upper()}'
        if self.price_day is None:
            self.price_day = self.car.price_day
        if self.deposit is None:
            self.deposit = self.car.deposit
        seconds = (self.date_end - self.date_start).total_seconds()
        self.days_count = max(math.ceil(seconds / 86400), 1)
        self.total_sum = self.price_day * self.days_count
        super().save(*args, **kwargs)
