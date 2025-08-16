# Unit tests for connector.transforms helpers and normalize_customers
# trimming, email validation, UTC date normalization.

from datetime import timezone
from dateutil import parser as dateparser

from connector.transforms import _clean_str, _valid_email, _parse_date_iso, normalize_customers

def test_clean_str():
    assert _clean_str(None) is None
    assert _clean_str("") is None
    assert _clean_str("   ") is None
    assert _clean_str(123) == "123"
    assert _clean_str("  ok  ") == "ok"

def test_valid_email():
    # Valid -> normalized (lowercased domain/local per library normalization)
    assert _valid_email("  ALICE@EXAMPLE.COM  ") == "alice@example.com"
    # Invalid -> None
    assert _valid_email("not-an-email") is None
    assert _valid_email(None) is None
    assert _valid_email("   ") is None

def test_parse_date_iso_naive_assumes_utc():
    iso = _parse_date_iso("2025-07-15 10:00")
    assert iso is not None
    dt = dateparser.parse(iso)
    assert dt.tzinfo is not None
    assert dt.utcoffset() == timezone.utc.utcoffset(dt)

def test_parse_date_iso_aware_converted_to_utc():
    iso = _parse_date_iso("2025-07-15T12:00:00+02:00")
    assert iso is not None
    dt = dateparser.parse(iso)
    # 12:00 +02:00 should become 10:00 +00:00
    assert dt.hour == 10 and dt.tzinfo is not None and dt.utcoffset().total_seconds() == 0

def test_normalize_customers_sample():
    rows = [
        {"Id":"101","Email":" alice@example.com ","FirstName":"Alice","LastName":"Tan","Country":"SG","LastPurchase":"2025-08-01 09:00"},
        {"customer_id":"102","email":"invalid@","first_name":"Bob","last_name":"Lee","country":"CZ","last_purchase_at":"2025-07-15T10:00:00+01:00"},
    ]
    out = normalize_customers(rows)
    assert out[0]["customer_id"] == "101"
    assert out[0]["email"] == "alice@example.com"
    assert out[0]["first_name"] == "Alice"
    assert out[0]["last_name"] == "Tan"
    assert out[0]["country"] == "SG"
    assert out[0]["last_purchase_at"] is not None

    assert out[1]["customer_id"] == "102"
    assert out[1]["email"] is None
    assert out[1]["country"] == "CZ"
    # Should be normalized to UTC
    dt = dateparser.parse(out[1]["last_purchase_at"])
    assert dt.utcoffset().total_seconds() == 0
