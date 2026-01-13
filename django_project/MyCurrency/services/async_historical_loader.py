"""
ASYNC HISTORICAL DATA LOADER
============================
Module for asynchronous historical exchange rate data loading.
Uses asyncio and aiohttp for concurrent fetching.
"""
import asyncio
import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

import aiohttp
from asgiref.sync import sync_to_async
from django.conf import settings

from ..models import Currency, CurrencyExchangeRate, Provider

logger = logging.getLogger(__name__)

# Límite de peticiones concurrentes (evita saturar la API)
MAX_CONCURRENT_REQUESTS = 10


async def fetch_rate_from_api(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    source_code: str,
    target_code: str,
    valuation_date: date,
    api_key: str,
    provider_name: str
) -> Optional[dict]:
    """
    Perform async HTTP request to fetch exchange rate.
    """
    async with semaphore:
        url = "https://api.currencybeacon.com/v1/historical"
        params = {
            'api_key': api_key,
            'base': source_code,
            'symbols': target_code,
            'date': valuation_date.strftime('%Y-%m-%d')
        }
        
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    data = await response.json()
                    # CurrencyBeacon structure: data['response']['rates'][symbol]
                    response_data = data.get('response', {})
                    rate = response_data.get('rates', {}).get(target_code)
                    if rate is not None:
                        return {
                            'source_code': source_code,
                            'target_code': target_code,
                            'valuation_date': valuation_date,
                            'rate_value': Decimal(str(rate)),
                            'provider': provider_name
                        }
                else:
                    logger.warning(f"API returned status {response.status} for {source_code}->{target_code} on {valuation_date}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {source_code}->{target_code} on {valuation_date}")
        except Exception as e:
            logger.exception(f"Error fetching rate: {e}")
        
        return None


async def load_historical_rates(
    source_code: str,
    target_codes: List[str],
    date_from: date,
    date_to: date,
    provider_name: str = 'currency_beacon'
) -> dict:
    """
    Asynchronously load historical exchange rates.
    """
    api_key = getattr(settings, 'CURRENCY_BEACON_API_KEY', None)
    if not api_key:
        logger.error("CURRENCY_BEACON_API_KEY not configured. Using mock data.")
        # Fallback a mock si no hay API key
        return await _load_mock_historical(source_code, target_codes, date_from, date_to)
    
    dates = []
    current = date_from
    while current <= date_to:
        dates.append(current)
        current += timedelta(days=1)
    
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    tasks = []
    
    async with aiohttp.ClientSession() as session:
        for d in dates:
            for target in target_codes:
                task = fetch_rate_from_api(
                    session, semaphore, source_code, target, d, api_key, provider_name
                )
                tasks.append(task)
        
        # Ejecutar todas las tareas concurrentemente
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filtrar resultados válidos
    valid_results = [r for r in results if isinstance(r, dict)]
    
    # Guardar en base de datos usando bulk_create para eficiencia
    await _save_rates_to_db(source_code, valid_results)
    
    stats = {
        'total_requests': len(tasks),
        'successful': len(valid_results),
        'failed': len(tasks) - len(valid_results),
        'date_range': f"{date_from} to {date_to}",
        'currencies': target_codes
    }
    logger.info(f"Historical load completed: {stats}")
    return stats


async def _load_mock_historical(
    source_code: str,
    target_codes: List[str],
    date_from: date,
    date_to: date
) -> dict:
    """Fallback: genera datos mock si no hay API key configurada."""
    import random
    
    dates = []
    current = date_from
    while current <= date_to:
        dates.append(current)
        current += timedelta(days=1)
    
    results = []
    for d in dates:
        for target in target_codes:
            results.append({
                'source_code': source_code,
                'target_code': target,
                'valuation_date': d,
                'rate_value': Decimal(str(round(random.uniform(0.5, 2.0), 6))),
                'provider': 'mock'
            })
    
    await _save_rates_to_db(source_code, results)
    
    return {
        'total_requests': len(results),
        'successful': len(results),
        'failed': 0,
        'date_range': f"{date_from} to {date_to}",
        'currencies': target_codes,
        'note': 'Using MOCK data (no API key configured)'
    }


@sync_to_async
def _save_rates_to_db(source_code: str, results: List[dict]) -> int:
    """
    Save results to database using bulk_create.
    """
    if not results:
        return 0
    
    source_currency = Currency.objects.get(code=source_code)
    
    # Preparar objetos para bulk_create
    rate_objects = []
    for r in results:
        try:
            target_currency = Currency.objects.get(code=r['target_code'])
            rate_objects.append(CurrencyExchangeRate(
                source_currency=source_currency,
                exchanged_currency=target_currency,
                valuation_date=r['valuation_date'],
                rate_value=r['rate_value'],
                provider=r['provider']
            ))
        except Currency.DoesNotExist:
            logger.warning(f"Currency {r['target_code']} not found in DB, skipping.")
    
    created = CurrencyExchangeRate.objects.bulk_create(
        rate_objects,
        ignore_conflicts=True
    )
    
    logger.info(f"Saved {len(created)} new exchange rates to database.")
    return len(created)
