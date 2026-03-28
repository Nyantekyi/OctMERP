from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from contact.importers import import_location_data


class Command(BaseCommand):
    help = 'Load initial country, state, and city data for the contact app.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            default=str(Path(settings.BASE_DIR) / 'testdummy' / 'data'),
            help='Directory containing countries.csv, states.csv, and cities.csv.',
        )
        parser.add_argument(
            '--country-code',
            action='append',
            dest='country_codes',
            default=['GH'],
            help='ISO2 country code to import. Repeat the flag to import multiple countries. Defaults to GH.',
        )
        parser.add_argument(
            '--prune',
            action='store_true',
            help='Delete existing location records for countries outside the selected country codes.',
        )

    def handle(self, *args, **options):
        data_dir = Path(options['data_dir']).resolve()
        if not data_dir.exists():
            raise CommandError(f'Data directory does not exist: {data_dir}')

        try:
            counts = import_location_data(
                data_dir,
                country_codes=options['country_codes'],
                prune=options['prune'],
            )
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                'Imported location data: '
                f"{counts['countries']} countries, "
                f"{counts['states']} states, "
                f"{counts['cities']} cities"
            )
        )