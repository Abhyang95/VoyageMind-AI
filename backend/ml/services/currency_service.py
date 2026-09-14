# ============================================================
# VoyageMind AI — Universal Currency Service
# ============================================================

from __future__ import annotations

import json
import time
from decimal import Decimal, ROUND_HALF_UP
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# ============================================================
# CONFIGURATION
# ============================================================

BASE_CURRENCY = "USD"

FRANKFURTER_URL = "https://api.frankfurter.dev/v2/rates?base=USD"

CACHE_TTL_SECONDS = 3600


# ============================================================
# FALLBACK RATES
#
# These are ONLY used if the exchange-rate API is temporarily
# unavailable.
#
# Production requests normally use the latest API rates.
# ============================================================

FALLBACK_USD_RATES = {
    "USD": Decimal("1"),

    "INR": Decimal("95.06"),
    "EUR": Decimal("0.85876"),
    "GBP": Decimal("0.73704"),
    "JPY": Decimal("153.65"),

    "AED": Decimal("3.6725"),
    "SGD": Decimal("1.29"),
    "CAD": Decimal("1.38"),
    "AUD": Decimal("1.52"),
}


# ============================================================
# CACHE
# ============================================================

_rates_cache = {
    "timestamp": 0.0,
    "rates": {},
    "date": None,
    "source": "fallback",
}

_cache_lock = Lock()


# ============================================================
# HELPERS
# ============================================================

def normalize_currency(currency: str) -> str:
    """
    Normalize an ISO currency code.

    Example:
        inr -> INR
        usd -> USD
    """

    if not currency:
        return BASE_CURRENCY

    return str(currency).strip().upper()


def money(value: Decimal) -> Decimal:
    """
    Round monetary values to two decimal places.
    """

    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


# ============================================================
# FETCH LIVE RATES
# ============================================================

def _fetch_live_rates() -> tuple[dict[str, Decimal], str | None]:
    """
    Fetch latest USD-based exchange rates.

    Frankfurter v2 returns rows like:

        {
            "date": "...",
            "base": "USD",
            "quote": "EUR",
            "rate": 0.85
        }

    The service supports currencies dynamically.
    """

    request = Request(
        FRANKFURTER_URL,
        headers={
            "User-Agent": "VoyageMind-AI/1.0",
            "Accept": "application/json",
        },
    )

    with urlopen(
        request,
        timeout=8,
    ) as response:

        raw_data = response.read().decode(
            "utf-8"
        )

    data = json.loads(
        raw_data,
        parse_float=Decimal,
    )

    rates: dict[str, Decimal] = {
        BASE_CURRENCY: Decimal("1")
    }

    rate_date = None

    for row in data:

        quote = normalize_currency(
            row.get("quote")
        )

        rate = row.get("rate")

        if not quote or rate is None:
            continue

        rates[quote] = Decimal(
            str(rate)
        )

        if row.get("date"):
            rate_date = row["date"]

    if len(rates) <= 1:
        raise ValueError(
            "Exchange-rate API returned no usable currencies."
        )

    return rates, rate_date


# ============================================================
# GET RATES
# ============================================================

def get_usd_rates() -> tuple[
    dict[str, Decimal],
    str | None,
    str,
]:
    """
    Return USD -> currency rates.

    Uses a one-hour cache to avoid repeatedly calling the
    exchange-rate API while a user is interacting with the app.
    """

    now = time.time()

    with _cache_lock:

        if (
            _rates_cache["rates"]
            and
            now - _rates_cache["timestamp"]
            < CACHE_TTL_SECONDS
        ):

            return (
                _rates_cache["rates"],
                _rates_cache["date"],
                _rates_cache["source"],
            )

        try:

            rates, rate_date = (
                _fetch_live_rates()
            )

            _rates_cache["timestamp"] = now
            _rates_cache["rates"] = rates
            _rates_cache["date"] = rate_date
            _rates_cache["source"] = (
                "frankfurter"
            )

            return (
                rates,
                rate_date,
                "frankfurter",
            )

        except (
            HTTPError,
            URLError,
            TimeoutError,
            ValueError,
            OSError,
        ):

            # ------------------------------------------------
            # API unavailable → use fallback
            # ------------------------------------------------

            fallback = dict(
                FALLBACK_USD_RATES
            )

            _rates_cache["timestamp"] = now
            _rates_cache["rates"] = fallback
            _rates_cache["date"] = None
            _rates_cache["source"] = (
                "fallback"
            )

            return (
                fallback,
                None,
                "fallback",
            )


# ============================================================
# VALIDATE CURRENCY
# ============================================================

def validate_currency(
    currency: str,
) -> str:

    normalized = normalize_currency(
        currency
    )

    rates, _, _ = get_usd_rates()

    if normalized not in rates:

        raise ValueError(
            f"Unsupported currency: {normalized}"
        )

    return normalized


# ============================================================
# CONVERT USER CURRENCY → USD
# ============================================================

def convert_to_usd(
    amount: float | Decimal,
    currency: str,
) -> Decimal:

    normalized_currency = validate_currency(
        currency
    )

    amount_decimal = Decimal(
        str(amount)
    )

    if amount_decimal <= 0:
        raise ValueError(
            "Amount must be greater than zero."
        )

    rates, _, _ = get_usd_rates()

    usd_rate = rates[
        normalized_currency
    ]

    if usd_rate <= 0:
        raise ValueError(
            f"Invalid exchange rate for "
            f"{normalized_currency}."
        )

    # --------------------------------------------------------
    # If:
    #
    # 1 USD = 95 INR
    #
    # Then:
    #
    # 150000 INR / 95 = 1578.94 USD
    # --------------------------------------------------------

    converted = (
        amount_decimal / usd_rate
    )

    return money(converted)


# ============================================================
# CONVERT USD → USER CURRENCY
# ============================================================

def convert_from_usd(
    amount: float | Decimal,
    currency: str,
) -> Decimal:

    normalized_currency = validate_currency(
        currency
    )

    amount_decimal = Decimal(
        str(amount)
    )

    rates, _, _ = get_usd_rates()

    target_rate = rates[
        normalized_currency
    ]

    converted = (
        amount_decimal * target_rate
    )

    return money(converted)


# ============================================================
# CONVERT ANY CURRENCY → ANY CURRENCY
#
# Useful for future VoyageMind features.
# ============================================================

def convert_currency(
    amount: float | Decimal,
    from_currency: str,
    to_currency: str,
) -> Decimal:

    source = normalize_currency(
        from_currency
    )

    target = normalize_currency(
        to_currency
    )

    if source == target:
        return money(
            Decimal(str(amount))
        )

    usd_amount = convert_to_usd(
        amount,
        source,
    )

    return convert_from_usd(
        usd_amount,
        target,
    )


# ============================================================
# RATE INFORMATION
# ============================================================

def get_currency_metadata(
    currency: str,
) -> dict:

    normalized = validate_currency(
        currency
    )

    rates, rate_date, source = (
        get_usd_rates()
    )

    return {
        "currency": normalized,
        "base_currency": BASE_CURRENCY,
        "usd_to_currency_rate": float(
            rates[normalized]
        ),
        "rate_date": rate_date,
        "rate_source": source,
    }