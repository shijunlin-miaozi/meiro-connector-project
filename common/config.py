import os
from dataclasses import dataclass
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()


# ------------ helpers (typed + validated) ------------

def _get_str(name: str, default: str = "") -> str:
    val = os.getenv(name)
    return default if val is None else val.strip()


def _get_optional_str(name: str) -> Optional[str]:
    val = os.getenv(name)
    if val is None:
        return None
    s = val.strip()
    return s if s else None


def _get_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None or val.strip() == "":
        return default
    try:
        return int(val.strip())
    except ValueError:
        raise ValueError(f"Invalid integer for {name}: {val!r}")


def _get_bounded_int(name: str, default: int, min_value: int, max_value: Optional[int] = None) -> int:
    n = _get_int(name, default)
    if n < min_value:
        raise ValueError(f"{name} must be >= {min_value}, got {n}")
    if max_value is not None and n > max_value:
        raise ValueError(f"{name} must be <= {max_value}, got {n}")
    return n


# ------------ settings ------------

@dataclass
class Settings:
    # Core
    CONNECTOR: str
    LOG_LEVEL: str

    # Google Sheets (read)
    GOOGLE_APPLICATION_CREDENTIALS: str
    SHEET_URL_OR_ID: str
    SHEET_TAB: str

    # Google Sheets (write)
    UPLOAD_SHEET_URL_OR_ID: str
    UPLOAD_SHEET_TAB: str

    # Output / HTTP uploader
    OUTPUT_PATH: str
    UPLOAD_URL: str
    CHUNK_SIZE: int  # 1..10_000

    # Random User connector
    RANDOMUSER_RESULTS: int  # 1..500
    RANDOMUSER_PAGES: int    # 1..100
    RANDOMUSER_SEED: Optional[str]
    RANDOMUSER_NAT: Optional[str]

    # Derived convenience
    @property
    def randomuser_nat_list(self) -> List[str]:
        """
        Return RANDOMUSER_NAT as a validated list of two-letter country codes, or [] if unset.
        Examples: 'us,gb', 'fr', 'cz,sk'
        """
        if not self.RANDOMUSER_NAT:
            return []
        parts = [part.strip().lower() for part in self.RANDOMUSER_NAT.split(",") if part.strip()]
        for code in parts:
            if len(code) != 2 or not code.isalpha():
                raise ValueError(
                    f"Invalid nationality code '{code}' in RANDOMUSER_NAT. "
                    f"Must be two letters (e.g., 'us', 'gb')."
                )
        return parts

    @property
    def randomuser_nat_csv(self) -> str | None:
        """
        Comma-separated 'nat' for the Random User API, or None if unset.
        Derived from randomuser_nat_list.
        """
        parts = self.randomuser_nat_list
        return ",".join(parts) if parts else None


def load_settings() -> Settings:
    # connector
    connector = _get_str("CONNECTOR", "randomuser").lower()
    if connector not in {"randomuser", "sheets"}:
        raise ValueError("CONNECTOR must be 'randomuser' or 'sheets'")

    s = Settings(
        CONNECTOR=connector,
        LOG_LEVEL=_get_str("LOG_LEVEL", "INFO"),

        # Google Sheets (read)
        GOOGLE_APPLICATION_CREDENTIALS=_get_str("GOOGLE_APPLICATION_CREDENTIALS", ""),
        SHEET_URL_OR_ID=_get_str("SHEET_URL_OR_ID", ""),
        SHEET_TAB=_get_str("SHEET_TAB", "Sheet1"),

        # Google Sheets (write)
        UPLOAD_SHEET_URL_OR_ID=_get_str("UPLOAD_SHEET_URL_OR_ID", ""),
        UPLOAD_SHEET_TAB=_get_str("UPLOAD_SHEET_TAB", "Ingested"),

        # Output / HTTP uploader
        OUTPUT_PATH=_get_str("OUTPUT_PATH", "/app/out/customers.csv"),
        UPLOAD_URL=_get_str("UPLOAD_URL", "http://host.docker.internal:8000/ingest"),
        CHUNK_SIZE=_get_bounded_int("CHUNK_SIZE", 100, min_value=1, max_value=10_000),

        # Random User connector
        RANDOMUSER_RESULTS=_get_bounded_int("RANDOMUSER_RESULTS", 50, min_value=1, max_value=500),
        RANDOMUSER_PAGES=_get_bounded_int("RANDOMUSER_PAGES", 1, min_value=1, max_value=100),
        RANDOMUSER_SEED=_get_optional_str("RANDOMUSER_SEED"),
        RANDOMUSER_NAT=_get_optional_str("RANDOMUSER_NAT"),
    )

    # cross-field checks
    if s.CONNECTOR == "sheets":
        if not s.GOOGLE_APPLICATION_CREDENTIALS:
            raise ValueError("For CONNECTOR=sheets, set GOOGLE_APPLICATION_CREDENTIALS (path to service account JSON).")
        if not s.SHEET_URL_OR_ID:
            raise ValueError("For CONNECTOR=sheets, set SHEET_URL_OR_ID (source sheet).")

    return s


# module-level instance for easy import
settings = load_settings()
