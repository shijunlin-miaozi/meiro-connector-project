# Unit tests for connector.uploader.chunked
# verifies chunk splitting for size=0,1,exact,remainder.

from connector.uploader import chunked

def test_chunked_size_zero_returns_all():
    data = list(range(7))
    chunks = list(chunked(data, 0))
    assert len(chunks) == 1
    assert chunks[0] == data

def test_chunked_size_one():
    data = list(range(3))
    chunks = list(chunked(data, 1))
    assert [len(c) for c in chunks] == [1,1,1]
    assert [item for c in chunks for item in c] == data

def test_chunked_exact_boundary():
    data = list(range(6))
    chunks = list(chunked(data, 3))
    assert [len(c) for c in chunks] == [3,3]
    assert [item for c in chunks for item in c] == data

def test_chunked_with_remainder():
    data = list(range(7))
    chunks = list(chunked(data, 3))
    assert [len(c) for c in chunks] == [3,3,1]
    assert [item for c in chunks for item in c] == data
