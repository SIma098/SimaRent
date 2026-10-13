from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from django.contrib.auth.models import Group
from django.db.models import Count
from django.utils.html import format_html

from .models import (
    BodyType,
    Booking,
    BookingStatus,
    Brand,
    Car,
    CarClass,
    CarModel,
    CarPhoto,
    City,
    Color,
    Feature,
    FuelType,
    Office,
    Role,
    TransmissionType,
    User,
)

# Группы Django не нужны: права выдаются через собственную таблицу ролей
admin.site.unregister(Group)

AUDIT_FIELDS = ('date_created', 'date_updated', 'user_created', 'user_updated')


class AuditAdminMixin:

    @staticmethod
    def fill_audit(obj, user, is_new):
        fields = {f.name for f in obj._meta.fields}
        if 'user_created' in fields and is_new:
            obj.user_created = user
        if 'user_updated' in fields:
            obj.user_updated = user
        if 'user_uploaded' in fields and is_new:
            obj.user_uploaded = user

    def save_model(self, request, obj, form, change):
        self.fill_audit(obj, request.user, is_new=not change)
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            self.fill_audit(obj, request.user, is_new=obj.pk is None)
            obj.save()
        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()


def photo_tag(photo, height=60):
    if not photo or not photo.file_path:
        return '—'
    return format_html(
        '<img src="{}" style="height:{}px;border-radius:4px">', photo.file_path.url, height,
    )


# Пользователи и роли

class UserInline(admin.TabularInline):
    model = User
    fields = ('email', 'first_name', 'last_name', 'blocked')
    readonly_fields = ('email', 'first_name', 'last_name', 'blocked')
    extra = 0
    can_delete = False
    show_change_link = True
    verbose_name_plural = 'Пользователи с этой ролью'

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'users_count', 'sort_order')
    list_display_links = ('name',)
    search_fields = ('name', 'code', 'description')
    inlines = [UserInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_users=Count('users'))

    @admin.display(description='Пользователей', ordering='_users')
    def users_count(self, obj):
        return obj._users


class UserCreateForm(AdminUserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'role')


class UserEditForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


class BookingOfUserInline(admin.TabularInline):
    model = Booking
    fk_name = 'user'  # у брони три ссылки на пользователя, нужна именно эта
    fields = ('booking_number', 'car', 'date_start', 'date_end', 'status', 'total_sum')
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True
    verbose_name_plural = 'Бронирования пользователя'

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(AuditAdminMixin, BaseUserAdmin):
    form = UserEditForm
    add_form = UserCreateForm

    list_display = ('email', 'full_name', 'phone', 'role', 'blocked', 'last_login', 'date_created')
    list_display_links = ('email', 'full_name')
    list_filter = ('role', 'blocked', 'date_created')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    date_hierarchy = 'date_created'
    readonly_fields = ('last_login',) + AUDIT_FIELDS
    ordering = ('last_name', 'first_name')
    filter_horizontal = ()
    inlines = [BookingOfUserInline]

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личные данные', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Доступ', {'fields': ('role', 'blocked')}),
        ('Служебная информация', {
            'classes': ('collapse',),
            'fields': ('last_login',) + AUDIT_FIELDS,
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone', 'role',
                       'usable_password', 'password1', 'password2'),
        }),
    )

    @admin.display(description='Имя и фамилия', ordering='last_name')
    def full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'



# География


class OfficeInline(admin.TabularInline):
    model = Office
    fields = ('name', 'address', 'phone', 'work_hours', 'active')
    extra = 0
    show_change_link = True


@admin.register(City)
class CityAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'code', 'region', 'offices_count', 'sort_order', 'active')
    list_display_links = ('name',)
    list_filter = ('active', 'region')
    search_fields = ('name', 'code', 'region')
    inlines = [OfficeInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_offices=Count('offices'))

    @admin.display(description='Офисов', ordering='_offices')
    def offices_count(self, obj):
        return obj._offices


class CarInOfficeInline(admin.TabularInline):
    model = Car
    fk_name = 'current_office'  # у машины две ссылки на офис: приписка и где сейчас
    fields = ('reg_number', 'model', 'car_class', 'status')
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True
    verbose_name_plural = 'Автомобили, которые сейчас в офисе'

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Office)
class OfficeAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'city', 'address', 'phone', 'work_hours', 'cars_now_count', 'active')
    list_display_links = ('name',)
    list_filter = ('city', 'active')
    search_fields = ('name', 'address', 'phone', 'city__name')
    date_hierarchy = 'date_created'
    readonly_fields = AUDIT_FIELDS
    list_select_related = ('city',)
    inlines = [CarInOfficeInline]

    fieldsets = (
        (None, {'fields': ('city', 'name', 'address', 'phone', 'work_hours', 'active')}),
        ('Координаты', {'fields': ('latitude', 'longitude')}),
        ('Служебная информация', {'classes': ('collapse',), 'fields': AUDIT_FIELDS}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_cars_now=Count('cars_now'))

    @admin.display(description='Машин сейчас', ordering='_cars_now')
    def cars_now_count(self, obj):
        return obj._cars_now



# Справочники автомобиля


class CarModelInline(admin.TabularInline):
    model = CarModel
    fields = ('name', 'year_start', 'year_end', 'active')
    extra = 0
    show_change_link = True


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'models_count', 'active')
    list_display_links = ('name',)
    list_filter = ('active', 'country')
    search_fields = ('name', 'country')
    inlines = [CarModelInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_models=Count('car_models'))

    @admin.display(description='Моделей', ordering='_models')
    def models_count(self, obj):
        return obj._models


@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'years', 'active')
    list_display_links = ('name',)
    list_filter = ('brand', 'active')
    search_fields = ('name', 'brand__name')
    list_select_related = ('brand',)

    # старый способ задать заголовок колонки — атрибутом short_description
    def years(self, obj):
        if obj.year_start and obj.year_end:
            return f'{obj.year_start}–{obj.year_end}'
        if obj.year_start:
            return f'с {obj.year_start}'
        return '—'
    years.short_description = 'Годы выпуска'


class DictionaryAdmin(admin.ModelAdmin):
    """Общие настройки простых справочников."""

    list_display = ('name', 'code', 'cars_count', 'sort_order', 'active')
    list_display_links = ('name',)
    list_filter = ('active',)
    search_fields = ('name', 'code')

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_cars=Count('cars'))

    @admin.display(description='Автомобилей', ordering='_cars')
    def cars_count(self, obj):
        return obj._cars


@admin.register(CarClass)
class CarClassAdmin(DictionaryAdmin):
    search_fields = ('name', 'code', 'description')


@admin.register(BodyType)
class BodyTypeAdmin(DictionaryAdmin):
    pass


@admin.register(TransmissionType)
class TransmissionTypeAdmin(DictionaryAdmin):
    pass


@admin.register(FuelType)
class FuelTypeAdmin(DictionaryAdmin):
    pass


@admin.register(Feature)
class FeatureAdmin(DictionaryAdmin):
    pass


@admin.register(Color)
class ColorAdmin(DictionaryAdmin):
    list_display = ('name', 'code', 'swatch', 'cars_count', 'sort_order', 'active')

    @admin.display(description='Цвет')
    def swatch(self, obj):
        if not obj.hex:
            return '—'
        return format_html(
            '<span style="display:inline-block;width:18px;height:18px;border-radius:3px;'
            'border:1px solid #ccc;background:{};vertical-align:middle"></span> {}',
            obj.hex, obj.hex,
        )



# Автомобили


class CarPhotoInline(admin.TabularInline):
    model = CarPhoto
    fields = ('preview', 'file_path', 'alt_text', 'sort_order')
    readonly_fields = ('preview',)
    extra = 1

    @admin.display(description='Превью')
    def preview(self, obj):
        return photo_tag(obj)


@admin.register(Car)
class CarAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = ('photo', 'reg_number', 'title', 'car_class', 'year',
                    'price_day', 'status', 'current_office')
    list_display_links = ('photo', 'reg_number', 'title')
    list_filter = ('status', 'car_class', 'body_type', 'transmission_type',
                   'fuel_type', 'current_office__city', 'active')
    search_fields = ('reg_number', 'vin_number', 'model__name', 'model__brand__name')
    date_hierarchy = 'date_created'
    raw_id_fields = ('model',)
    filter_horizontal = ('features',)
    readonly_fields = AUDIT_FIELDS
    list_select_related = ('model__brand', 'car_class', 'current_office__city')
    inlines = [CarPhotoInline]

    fieldsets = (
        ('Автомобиль', {
            'fields': ('model', 'reg_number', 'vin_number', 'year', 'color'),
        }),
        ('Классификация', {
            'fields': ('car_class', 'body_type', 'transmission_type', 'fuel_type'),
        }),
        ('Характеристики', {
            'fields': ('engine_volume', 'horsepower', 'fuel_consumption',
                       'seats_count', 'doors_count', 'trunk_volume', 'mileage'),
        }),
        ('Опции', {'fields': ('features',)}),
        ('Аренда', {
            'fields': ('price_day', 'deposit', 'status', 'home_office',
                       'current_office', 'active', 'date_deleted'),
        }),
        ('Служебная информация', {'classes': ('collapse',), 'fields': AUDIT_FIELDS}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('photos')

    @admin.display(description='Автомобиль', ordering='model__brand__name')
    def title(self, obj):
        return str(obj.model)

    @admin.display(description='Фото')
    def photo(self, obj):
        photos = list(obj.photos.all())
        return photo_tag(photos[0] if photos else None, height=40)


@admin.register(CarPhoto)
class CarPhotoAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = ('preview', 'file_name', 'car', 'file_format', 'size_kb', 'sort_order',
                    'date_created')
    list_display_links = ('preview', 'file_name')
    list_filter = ('file_format', 'date_created')
    search_fields = ('file_name', 'alt_text', 'car__reg_number', 'car__model__name')
    date_hierarchy = 'date_created'
    raw_id_fields = ('car',)
    readonly_fields = ('preview', 'file_name', 'file_format', 'file_size',
                       'user_uploaded', 'date_created')
    list_select_related = ('car__model__brand',)

    @admin.display(description='Превью')
    def preview(self, obj):
        return photo_tag(obj)

    def size_kb(self, obj):
        return f'{obj.file_size // 1024} КБ' if obj.file_size else '—'
    size_kb.short_description = 'Размер'



# Бронирования


def status_label(status):
    return format_html(
        '<span style="padding:2px 8px;border-radius:10px;color:#fff;background:{}">{}</span>',
        status.color or '#888', status.name,
    )


@admin.register(BookingStatus)
class BookingStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'label', 'final_status', 'bookings_count', 'sort_order')
    list_display_links = ('name',)
    list_filter = ('final_status',)
    search_fields = ('name', 'code')

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_bookings=Count('bookings'))

    @admin.display(description='Как выглядит')
    def label(self, obj):
        return status_label(obj)

    @admin.display(description='Бронирований', ordering='_bookings')
    def bookings_count(self, obj):
        return obj._bookings


@admin.register(Booking)
class BookingAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = ('booking_number', 'user', 'car', 'period', 'days_count',
                    'total_sum', 'status_badge', 'paid')
    list_display_links = ('booking_number',)
    list_filter = ('status', 'paid', 'pickup_office__city', 'date_start')
    search_fields = ('booking_number', 'user__email', 'user__last_name', 'car__reg_number')
    date_hierarchy = 'date_start'
    raw_id_fields = ('user', 'car')
    readonly_fields = ('booking_number', 'days_count', 'price_day', 'total_sum',
                       'deposit') + AUDIT_FIELDS
    list_select_related = ('user', 'car__model__brand', 'status')

    fieldsets = (
        ('Бронь', {'fields': ('booking_number', 'user', 'car', 'status', 'paid')}),
        ('Даты и офисы', {
            'fields': ('date_start', 'date_end', 'pickup_office', 'return_office',
                       'return_office_fact'),
        }),
        ('Расчёт', {
            'description': 'Считается автоматически при сохранении',
            'fields': ('price_day', 'days_count', 'total_sum', 'deposit'),
        }),
        ('Фактические даты', {
            'fields': ('date_confirmed', 'date_start_fact', 'date_end_fact', 'date_cancelled'),
        }),
        ('Служебная информация', {'classes': ('collapse',), 'fields': AUDIT_FIELDS}),
    )

    def period(self, obj):
        return f'{obj.date_start:%d.%m.%Y} — {obj.date_end:%d.%m.%Y}'
    period.short_description = 'Период аренды'
    period.admin_order_field = 'date_start'

    @admin.display(description='Статус', ordering='status__sort_order')
    def status_badge(self, obj):
        return status_label(obj.status)
