"""
Comando de Django para cargar datos históricos de tasas de cambio de forma asíncrona.

Uso:
    python manage.py load_historical --source EUR --targets USD,GBP,CHF --from 2024-01-01 --to 2024-01-31
"""
import asyncio
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from MyCurrency.services.async_historical_loader import load_historical_rates


class Command(BaseCommand):
    help = 'Carga datos históricos de tasas de cambio de forma asíncrona y eficiente.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            required=True,
            help='Código de la moneda base (ej: EUR)'
        )
        parser.add_argument(
            '--targets',
            type=str,
            required=True,
            help='Códigos de monedas destino separados por coma (ej: USD,GBP,CHF)'
        )
        parser.add_argument(
            '--from',
            dest='date_from',
            type=str,
            required=True,
            help='Fecha de inicio en formato YYYY-MM-DD'
        )
        parser.add_argument(
            '--to',
            dest='date_to',
            type=str,
            required=True,
            help='Fecha de fin en formato YYYY-MM-DD'
        )

    def handle(self, *args, **options):
        source_code = options['source'].upper()
        target_codes = [t.strip().upper() for t in options['targets'].split(',')]
        
        try:
            date_from = datetime.strptime(options['date_from'], '%Y-%m-%d').date()
            date_to = datetime.strptime(options['date_to'], '%Y-%m-%d').date()
        except ValueError:
            raise CommandError('Las fechas deben estar en formato YYYY-MM-DD')
        
        if date_from > date_to:
            raise CommandError('La fecha de inicio debe ser anterior a la de fin')
        
        self.stdout.write(self.style.NOTICE(
            f'Iniciando carga histórica: {source_code} -> {target_codes}'
        ))
        self.stdout.write(self.style.NOTICE(
            f'Período: {date_from} a {date_to}'
        ))
        
        # Ejecutar la función asíncrona
        stats = asyncio.run(load_historical_rates(
            source_code=source_code,
            target_codes=target_codes,
            date_from=date_from,
            date_to=date_to
        ))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Carga completada!'
        ))
        self.stdout.write(f"  - Peticiones totales: {stats['total_requests']}")
        self.stdout.write(f"  - Exitosas: {stats['successful']}")
        self.stdout.write(f"  - Fallidas: {stats['failed']}")
        
        if stats.get('note'):
            self.stdout.write(self.style.WARNING(f"  - Nota: {stats['note']}"))
