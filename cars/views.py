from django.shortcuts import render

from .data import BOOKING_STEPS, CAR_CLASSES, CARS, CITIES, FEATURES, OFFICES


def home(request):
    context = {
        'cities': CITIES,
        'offices': OFFICES,
        'car_classes': CAR_CLASSES,
        'cars': CARS[:6],
        'features': FEATURES,
        'booking_steps': BOOKING_STEPS,
        'cars_total': len(CARS),
        'offices_total': len(OFFICES),
        'cities_total': len(CITIES),
    }
    return render(request, 'cars/home.html', context)


def listing(request):
    return render(request, 'cars/listing.html', {'cars': CARS, 'cars_total': len(CARS)})


def about(request):
    context = {
        'cities': CITIES,
        'offices': OFFICES,
        'car_classes': CAR_CLASSES,
        'cars_total': len(CARS),
        'offices_total': len(OFFICES),
        'cities_total': len(CITIES),
    }
    return render(request, 'cars/about.html', context)


def contact(request):
    return render(request, 'cars/contact.html', {'offices': OFFICES, 'cities': CITIES})
