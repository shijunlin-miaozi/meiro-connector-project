# Integration: RandomUser fetch (network). 
# With a fixed seed, ensures deterministic IDs across repeated fetches.

from connector.random_user import RandomUserConnector


def test_randomuser_fetch_seed_network():
    conn = RandomUserConnector(results_per_page=5, pages=1, seed="ci-seed", nat=None)
    rows1 = conn.fetch()
    rows2 = conn.fetch()
    ids1 = [r["id"] for r in rows1]
    ids2 = [r["id"] for r in rows2]
    assert ids1 == ids2 and len(ids1) == 5
