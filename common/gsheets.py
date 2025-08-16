"""
Google Sheets helpers (auth + utilities)

This module centralizes:
- Extracting a spreadsheet ID from a full Sheets URL (`extract_sheet_id`).
- Creating cached gspread clients with least-privilege scopes for **read** or **write**
  (`get_read_client`, `get_write_client`), from either:
    1) a **path** to a service account JSON file (cached), or
    2) an in-memory **Credentials** object (not cached, but convenient in cloud setups).
- Opening a spreadsheet by URL or ID (`open_by_url_or_id`).

SCOPES (least privilege):
- Read-only:  "https://www.googleapis.com/auth/spreadsheets.readonly"
- Read-write: "https://www.googleapis.com/auth/spreadsheets"

ACCESS NOTE (service account):
To let a service account access your sheet, open the spreadsheet in Google Sheets,
click **Share**, and grant access to the service account's email (the `client_email`
field in the JSON key). Give **Viewer** for read-only, or **Editor** for write.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Final, Optional, Tuple

import gspread
from google.oauth2.service_account import Credentials

# Precompiled regex to extract the spreadsheet ID from a full URL
_SHEET_ID_RE: Final = re.compile(r"/spreadsheets/d/([a-zA-Z0-9\-_]+)")

_READONLY_SCOPES: Tuple[str, ...] = ("https://www.googleapis.com/auth/spreadsheets.readonly",)
_WRITE_SCOPES: Tuple[str, ...] = ("https://www.googleapis.com/auth/spreadsheets",)


def extract_sheet_id(url_or_id: str) -> str:
    """
    Return the spreadsheet ID from a Google Sheets URL, or the input if it's already an ID.
    Raises ValueError if the string looks like a URL but no ID can be extracted.
    """
    if not isinstance(url_or_id, str):
        raise TypeError("url_or_id must be a string")
    if "docs.google.com/spreadsheets" in url_or_id:
        m = _SHEET_ID_RE.search(url_or_id)
        if not m:
            raise ValueError("Invalid Google Sheets URL; cannot extract spreadsheet ID.")
        return m.group(1)
    return url_or_id


@lru_cache(maxsize=8)
def _client_from_path(credentials_path: str, scopes: Tuple[str, ...]) -> gspread.Client:
    """
    Internal: build and cache a gspread client from a key file path + scopes.
    Tuple 'scopes' is used so the function remains hashable for caching.
    """
    creds = Credentials.from_service_account_file(credentials_path, scopes=list(scopes))
    return gspread.authorize(creds)


def get_read_client(*, credentials: Optional[Credentials] = None,
                    credentials_path: Optional[str] = None) -> gspread.Client:
    """
    Obtain a gspread client authorized for READ-ONLY access.

    You can provide either:
      - credentials_path: path to service account JSON (cached client), OR
      - credentials: a preloaded Credentials instance (not cached; will be scoped here).
    """
    if credentials is not None:
        creds_scoped = credentials.with_scopes(list(_READONLY_SCOPES))
        return gspread.authorize(creds_scoped)
    if not credentials_path:
        raise ValueError("Provide either 'credentials' or 'credentials_path'.")
    return _client_from_path(credentials_path, _READONLY_SCOPES)


def get_write_client(*, credentials: Optional[Credentials] = None,
                     credentials_path: Optional[str] = None) -> gspread.Client:
    """
    Obtain a gspread client authorized for READ-WRITE access.

    You can provide either:
      - credentials_path: path to service account JSON (cached client), OR
      - credentials: a preloaded Credentials instance (not cached; will be scoped here).
    """
    if credentials is not None:
        creds_scoped = credentials.with_scopes(list(_WRITE_SCOPES))
        return gspread.authorize(creds_scoped)
    if not credentials_path:
        raise ValueError("Provide either 'credentials' or 'credentials_path'.")
    return _client_from_path(credentials_path, _WRITE_SCOPES)


def open_by_url_or_id(client: gspread.Client, url_or_id: str) -> gspread.Spreadsheet:
    """
    Open a spreadsheet using either a full URL or a bare ID with an existing gspread client.
    """
    return client.open_by_key(extract_sheet_id(url_or_id))
