# Unit test for RandomUserConnector.transform
# maps input dict to canonical schema and normalizes dates to UTC.

from connector.random_user import RandomUserConnector
from dateutil import parser as dateparser

def test_random_user_transform_maps_to_canonical_schema():
    # Simulate what fetch() yields from Random User (pre-normalization)
    raw = [{
        "id": "uuid-123",
        "Email": "USER@EXAMPLE.COM",
        "FirstName": "Jane",
        "LastName": "Doe",
        "Country": "US",
        "LastPurchase": "2025-08-12T14:15:00+02:00",
    }]
    conn = RandomUserConnector(results_per_page=1, pages=1, seed="test-seed", nat=None)
    out = conn.transform(raw)
    assert len(out) == 1
    row = out[0]
    assert set(row.keys()) == {"customer_id","email","first_name","last_name","country","last_purchase_at"}
    assert row["customer_id"] == "uuid-123"
    assert row["email"] == "user@example.com"
    assert row["first_name"] == "Jane"
    assert row["last_name"] == "Doe"
    assert row["country"] == "US"
    # UTC normalization
    dt = dateparser.parse(row["last_purchase_at"])
    assert dt.utcoffset() is not None and dt.utcoffset().total_seconds() == 0
