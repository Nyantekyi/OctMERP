import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.db import transaction

from .models import City, Country, State


def _optional_decimal(value):
    if value in (None, ''):
        return None

    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return None


def _normalize_country_codes(country_codes):
    if not country_codes:
        return None

    return {code.strip().upper() for code in country_codes if code and code.strip()}


@transaction.atomic
def import_location_data(data_dir, country_codes=None, prune=False):
    data_path = Path(data_dir)
    countries_file = data_path / 'countries.csv'
    states_file = data_path / 'states.csv'
    cities_file = data_path / 'cities.csv'
    selected_country_codes = _normalize_country_codes(country_codes)

    missing_files = [str(path) for path in (countries_file, states_file, cities_file) if not path.exists()]
    if missing_files:
        missing = ', '.join(missing_files)
        raise FileNotFoundError(f'Missing location data file(s): {missing}')

    counts = {
        'countries': 0,
        'states': 0,
        'cities': 0,
    }
    countries_by_source_id = {}
    states_by_source_id = {}

    with countries_file.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            iso2 = (row['iso2'] or '').upper()
            if selected_country_codes and iso2 not in selected_country_codes:
                continue

            country, _ = Country.objects.update_or_create(
                numeric_code=row['numeric_code'],
                defaults={
                    'name': row['name'],
                    'iso3': row['iso3'] or None,
                    'iso2': iso2 or None,
                    'phone_code': row['phone_code'] or None,
                    'currency': row['currency'] or None,
                    'currency_name': row['currency_name'] or None,
                    'lat': _optional_decimal(row['latitude']),
                    'lon': _optional_decimal(row['longitude']),
                },
            )
            countries_by_source_id[row['id']] = country
            counts['countries'] += 1

    if prune and selected_country_codes:
        Country.objects.exclude(iso2__in=selected_country_codes).delete()

    with states_file.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            country = countries_by_source_id.get(row['country_id'])
            if country is None:
                continue

            state, _ = State.objects.update_or_create(
                country=country,
                name=row['name'],
                defaults={
                    'state_code': row['state_code'] or None,
                    'lat': _optional_decimal(row['latitude']),
                    'lon': _optional_decimal(row['longitude']),
                },
            )
            states_by_source_id[row['id']] = state
            counts['states'] += 1

    with cities_file.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            state = states_by_source_id.get(row['state_id'])
            if state is None:
                continue

            City.objects.update_or_create(
                state=state,
                name=row['name'],
                defaults={
                    'lat': _optional_decimal(row['latitude']),
                    'lon': _optional_decimal(row['longitude']),
                },
            )
            counts['cities'] += 1

    return counts