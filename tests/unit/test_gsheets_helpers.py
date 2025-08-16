# Unit tests for common.gsheets.extract_sheet_id
# ensure ID is parsed from URL and ID passthrough works.

from common.gsheets import extract_sheet_id

def test_extract_sheet_id_from_url():
    url = "https://docs.google.com/spreadsheets/d/1AbC-XYZ_1234567890abcdef/edit#gid=0"
    assert extract_sheet_id(url) == "1AbC-XYZ_1234567890abcdef"

def test_extract_sheet_id_from_id_passthrough():
    the_id = "1AbC-XYZ_1234567890abcdef"
    assert extract_sheet_id(the_id) == the_id
