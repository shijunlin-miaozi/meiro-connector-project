from typing import List, Dict, Optional, Any
from email_validator import validate_email, EmailNotValidError
from dateutil import parser as dateparser
from datetime import timezone

# --- Helpers ---------------------------------------------------------------

def _clean_str(v: Any) -> Optional[str]:
    """Coerce to str, trim whitespace; return None if empty."""
    if v is None:
        return None
    if not isinstance(v, str):
        v = str(v)
    return v.strip() or None


def _parse_date_iso(v: Any) -> Optional[str]:
    """
    Parse a date-like value and return an ISO-8601 string in UTC.
    - If the parsed datetime is naive (no tzinfo), assume UTC.
    - If it's timezone-aware, convert to UTC.
    """
    if not v:
        return None
    try:
        dt = dateparser.parse(str(v))
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat()
    except Exception:
        return None


def _valid_email(v: Any) -> Optional[str]:
    """
    Validate email and return canonical lowercase (local@domain).
    Uses email_validator (deliverability checks disabled).
    """
    s = _clean_str(v)
    if not s:
        return None
    try:
        r = validate_email(s, check_deliverability=False)
        # Project policy: lowercase BOTH local-part and domain.
        return f"{r.local_part.lower()}@{r.domain.lower()}"
    except EmailNotValidError:
        return None


def _normalize_person_name(v: Any) -> Optional[str]:
    """
    Title-case person names: first letter upper, rest lower (per word).
    Examples: 'KHAN' -> 'Khan', "O'NEIL" -> "O'Neil", 'mARIA-ANNE' -> 'Maria-Anne'.
    """
    s = _clean_str(v)
    if not s:
        return None
    return s.title()


# Common country-name -> ISO-3166-1 alpha-2 mapping (lowercased keys).
# Not exhaustive, but covers typical Random User outputs & common countries.
_COUNTRY_TO_ISO2 = {
    "united states": "US",
    "usa": "US",
    "u.s.a.": "US",
    "u.s.": "US",
    "united kingdom": "GB",
    "great britain": "GB",
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "northern ireland": "GB",
    "czech republic": "CZ",
    "czechia": "CZ",
    "germany": "DE",
    "france": "FR",
    "spain": "ES",
    "japan": "JP",
    "india": "IN",
    "brazil": "BR",
    "singapore": "SG",
    "canada": "CA",
    "australia": "AU",
    "netherlands": "NL",
    "switzerland": "CH",
    "sweden": "SE",
    "norway": "NO",
    "denmark": "DK",
    "finland": "FI",
    "ireland": "IE",
    "belgium": "BE",
    "austria": "AT",
    "poland": "PL",
    "portugal": "PT",
    "greece": "GR",
    "turkey": "TR",
    "new zealand": "NZ",
    "iran": "IR",
    "israel": "IL",
    "mexico": "MX",
    "italy": "IT",
    "romania": "RO",
    "russia": "RU",
    "ukraine": "UA",
    "hong kong": "HK",
    "china": "CN",
    "taiwan": "TW",
    "south korea": "KR",
    "korea, republic of": "KR",
}


def _country_to_iso2(v: Any) -> Optional[str]:
    """
    Normalize country to ISO-3166-1 alpha-2 (uppercase).
    - If already a 2-letter alpha code, returns it uppercased.
    - Else maps common country names to codes via a small built-in map.
    - Returns None if cannot be determined.
    """
    s = _clean_str(v)
    if not s:
        return None

    # Already looks like a code
    up = s.upper()
    if len(up) == 2 and up.isalpha():
        return up

    # Try name mapping
    code = _COUNTRY_TO_ISO2.get(s.lower())
    if code:
        return code

    # Fallback: None (avoid guessing wrong codes)
    return None


# --- Public transform ------------------------------------------------------

def normalize_customers(rows: List[Dict]) -> List[Dict]:
    """
    Normalize heterogeneous customer rows into a canonical schema:
    - customer_id: str|None (trimmed)
    - email: normalized lowercase valid email or None
    - first_name / last_name: title-cased names (e.g., 'O'Neil')
    - country: ISO-2 uppercase (e.g., 'GB'); None if unknown
    - last_purchase_at: ISO-8601 UTC or None
    """
    out: List[Dict] = []
    for r in rows:
        o = {
            "customer_id": _clean_str(r.get("customer_id") or r.get("id") or r.get("Id")),
            "email": _valid_email(r.get("email") or r.get("Email")),
            "first_name": _normalize_person_name(
                r.get("first_name") or r.get("FirstName") or r.get("firstname")
            ),
            "last_name": _normalize_person_name(
                r.get("last_name") or r.get("LastName") or r.get("lastname")
            ),
            "country": _country_to_iso2(r.get("country") or r.get("Country")),
            "last_purchase_at": _parse_date_iso(
                r.get("last_purchase_at")
                or r.get("LastPurchase")
                or r.get("last_purchase")
                or r.get("LastModifiedDate")
            ),
        }
        out.append(o)
    return out
