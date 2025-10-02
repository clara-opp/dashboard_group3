import requests
import time
from datetime import datetime, timezone
from textwrap import shorten
import pandas as pd
import sqlite3
from typing import Dict, Any, List

# aa_travelwarning_collect.py

BASE = "https://www.auswaertiges-amt.de/opendata"
S = requests.Session()
S.headers.update({"Accept": "application/json", "User-Agent": "aa-travelwarning-demo/0.2"})

WRITE_SQLITE = False  # set True to persist into SQLite
SQLITE_PATH = "travelwarnings.db"

def ts_iso(ts: int | None) -> str | None:
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    except Exception:
        return None

def get_json(path: str) -> Dict[str, Any] | List[Any]:
    r = S.get(f"{BASE}{path}", timeout=30)
    r.raise_for_status()
    return r.json()

def collect_travel_warnings(limit: int | None = None, sleep_sec: float = 0.15) -> pd.DataFrame:
    root = get_json("/travelwarning")   # <- dict with "response" and contentId entries
    if not isinstance(root, dict) or "response" not in root:
        raise RuntimeError(f"Unexpected payload from /travelwarning: {type(root)}")

    resp = root["response"]
    global_last_modified = ts_iso(resp.get("lastModified"))

    # Build a list of (contentId, meta)
    items: List[tuple[str, Dict[str, Any]]] = [
        (k, v) for k, v in resp.items() if k != "lastModified"
    ]
    # Optional: limit for faster testing
    if limit:
        items = items[:limit]

    rows: List[Dict[str, Any]] = []

    print(f"# Travel warnings index updated: {global_last_modified}")
    print(f"# Countries in index: {len(items)}\n")

    for i, (content_id, meta) in enumerate(items, start=1):
        # Fetch details for full advisory content
        try:
            detail = get_json(f"/travelwarning/{content_id}")
        except requests.HTTPError as e:
            print(f"[{i}/{len(items)}] {content_id}: HTTP {e.response.status_code if e.response else 'ERR'}")
            continue
        except requests.RequestException as e:
            print(f"[{i}/{len(items)}] {content_id}: request error {e}")
            continue

        # Normalize fields (be lenient: some keys may vary)
        country_name = (
            detail.get("countryName") or detail.get("country") or detail.get("state") or meta.get("countryName")
        )
        country_code = detail.get("countryCode") or meta.get("countryCode")
        iso3 = detail.get("iso3CountryCode") or meta.get("iso3CountryCode")
        title = detail.get("title") or detail.get("name") or meta.get("title")
        last_mod = ts_iso(detail.get("lastModified") or meta.get("lastModified"))
        effective = ts_iso(detail.get("effective"))
        content = detail.get("content") or ""
        url = detail.get("url") or meta.get("url")  # sometimes present
        warning = bool(detail.get("warning", meta.get("warning", False)))
        partial_warning = bool(detail.get("partialWarning", meta.get("partialWarning", False)))
        situation_warning = bool(detail.get("situationWarning", meta.get("situationWarning", False)))
        situation_part_warning = bool(detail.get("situationPartWarning", meta.get("situationPartWarning", False)))

        # Build DB-ready row
        row = {
            "content_id": int(content_id),
            "title": title,
            "country_name": country_name,
            "country_code": country_code,
            "iso3_country_code": iso3,
            "last_modified_iso": last_mod,
            "effective_iso": effective,
            "warning": int(warning),
            "partial_warning": int(partial_warning),
            "situation_warning": int(situation_warning),
            "situation_part_warning": int(situation_part_warning),
            "source_url": url,
            "content": content,
        }
        rows.append(row)

        # Console overview
        preview = shorten((content or "").replace("\n", " "), width=160, placeholder="…")
        flags = []
        if warning: flags.append("WARNING")
        if partial_warning: flags.append("PARTIAL")
        if situation_warning: flags.append("SIT")
        if situation_part_warning: flags.append("SIT-PART")
        flags_str = ", ".join(flags) if flags else "—"

        print(f"[{i}/{len(items)}] {country_name} ({country_code}/{iso3}) | {flags_str} | last: {last_mod} | {title}")
        if preview:
            print(f"    {preview}")

        time.sleep(sleep_sec)  # gentle pacing

    df = pd.DataFrame(rows)
    # Write a CSV snapshot for quick inspection
    df.to_csv("travelwarnings_snapshot.csv", index=False, encoding="utf-8")
    print(f"\nSaved CSV snapshot with {len(df)} rows → travelwarnings_snapshot.csv")

    if WRITE_SQLITE:
        write_sqlite(df, SQLITE_PATH)

    return df

def write_sqlite(df: pd.DataFrame, db_path: str):
    # Two-table schema (normalized-ish): metadata and content, joined by content_id
    meta_cols = [
        "content_id", "title", "country_name", "country_code", "iso3_country_code",
        "last_modified_iso", "effective_iso", "warning", "partial_warning",
        "situation_warning", "situation_part_warning", "source_url"
    ]
    content_cols = ["content_id", "content"]

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS travelwarning_meta (
            content_id INTEGER PRIMARY KEY,
            title TEXT,
            country_name TEXT,
            country_code TEXT,
            iso3_country_code TEXT,
            last_modified_iso TEXT,
            effective_iso TEXT,
            warning INTEGER,
            partial_warning INTEGER,
            situation_warning INTEGER,
            situation_part_warning INTEGER,
            source_url TEXT
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS travelwarning_content (
            content_id INTEGER PRIMARY KEY,
            content TEXT,
            FOREIGN KEY(content_id) REFERENCES travelwarning_meta(content_id)
        )
        """)
        # Upsert (SQLite 3.24+)
        meta_df = df[meta_cols].copy()
        content_df = df[content_cols].copy()

        meta_df.to_sql("travelwarning_meta_tmp", conn, if_exists="replace", index=False)
        content_df.to_sql("travelwarning_content_tmp", conn, if_exists="replace", index=False)

        cur.executescript("""
        INSERT INTO travelwarning_meta
        SELECT * FROM travelwarning_meta_tmp
        ON CONFLICT(content_id) DO UPDATE SET
          title=excluded.title,
          country_name=excluded.country_name,
          country_code=excluded.country_code,
          iso3_country_code=excluded.iso3_country_code,
          last_modified_iso=excluded.last_modified_iso,
          effective_iso=excluded.effective_iso,
          warning=excluded.warning,
          partial_warning=excluded.partial_warning,
          situation_warning=excluded.situation_warning,
          situation_part_warning=excluded.situation_part_warning,
          source_url=excluded.source_url;

        INSERT INTO travelwarning_content
        SELECT * FROM travelwarning_content_tmp
        ON CONFLICT(content_id) DO UPDATE SET
          content=excluded.content;

        DROP TABLE travelwarning_meta_tmp;
        DROP TABLE travelwarning_content_tmp;
        """)
        conn.commit()
    print(f"Saved {len(df)} rows into SQLite → {db_path} (tables: travelwarning_meta, travelwarning_content)")

if __name__ == "__main__":
    try:
        # For a quick test while developing, set limit=10; remove it to fetch all.
        collect_travel_warnings(limit=None)
    except requests.HTTPError as e:
        print("HTTP error:", e, "| response snippet:", getattr(e.response, "text", "")[:300])
    except requests.RequestException as e:
        print("Request error:", e)

# aa_travelwarning_collect.py

BASE = "https://www.auswaertiges-amt.de/opendata"
S = requests.Session()
S.headers.update({"Accept": "application/json", "User-Agent": "aa-travelwarning-demo/0.2"})

WRITE_SQLITE = False  # set True to persist into SQLite
SQLITE_PATH = "travelwarnings.db"

def ts_iso(ts: int | None) -> str | None:
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    except Exception:
        return None

def get_json(path: str) -> Dict[str, Any] | List[Any]:
    r = S.get(f"{BASE}{path}", timeout=30)
    r.raise_for_status()
    return r.json()

def collect_travel_warnings(limit: int | None = None, sleep_sec: float = 0.15) -> pd.DataFrame:
    root = get_json("/travelwarning")   # <- dict with "response" and contentId entries
    if not isinstance(root, dict) or "response" not in root:
        raise RuntimeError(f"Unexpected payload from /travelwarning: {type(root)}")

    resp = root["response"]
    global_last_modified = ts_iso(resp.get("lastModified"))

    # Build a list of (contentId, meta)
    items: List[tuple[str, Dict[str, Any]]] = [
        (k, v) for k, v in resp.items() if k != "lastModified"
    ]
    # Optional: limit for faster testing
    if limit:
        items = items[:limit]

    rows: List[Dict[str, Any]] = []

    print(f"# Travel warnings index updated: {global_last_modified}")
    print(f"# Countries in index: {len(items)}\n")

    for i, (content_id, meta) in enumerate(items, start=1):
        # Fetch details for full advisory content
        try:
            detail = get_json(f"/travelwarning/{content_id}")
        except requests.HTTPError as e:
            print(f"[{i}/{len(items)}] {content_id}: HTTP {e.response.status_code if e.response else 'ERR'}")
            continue
        except requests.RequestException as e:
            print(f"[{i}/{len(items)}] {content_id}: request error {e}")
            continue

        # Normalize fields (be lenient: some keys may vary)
        country_name = (
            detail.get("countryName") or detail.get("country") or detail.get("state") or meta.get("countryName")
        )
        country_code = detail.get("countryCode") or meta.get("countryCode")
        iso3 = detail.get("iso3CountryCode") or meta.get("iso3CountryCode")
        title = detail.get("title") or detail.get("name") or meta.get("title")
        last_mod = ts_iso(detail.get("lastModified") or meta.get("lastModified"))
        effective = ts_iso(detail.get("effective"))
        content = detail.get("content") or ""
        url = detail.get("url") or meta.get("url")  # sometimes present
        warning = bool(detail.get("warning", meta.get("warning", False)))
        partial_warning = bool(detail.get("partialWarning", meta.get("partialWarning", False)))
        situation_warning = bool(detail.get("situationWarning", meta.get("situationWarning", False)))
        situation_part_warning = bool(detail.get("situationPartWarning", meta.get("situationPartWarning", False)))

        # Build DB-ready row
        row = {
            "content_id": int(content_id),
            "title": title,
            "country_name": country_name,
            "country_code": country_code,
            "iso3_country_code": iso3,
            "last_modified_iso": last_mod,
            "effective_iso": effective,
            "warning": int(warning),
            "partial_warning": int(partial_warning),
            "situation_warning": int(situation_warning),
            "situation_part_warning": int(situation_part_warning),
            "source_url": url,
            "content": content,
        }
        rows.append(row)

        # Console overview
        preview = shorten((content or "").replace("\n", " "), width=160, placeholder="…")
        flags = []
        if warning: flags.append("WARNING")
        if partial_warning: flags.append("PARTIAL")
        if situation_warning: flags.append("SIT")
        if situation_part_warning: flags.append("SIT-PART")
        flags_str = ", ".join(flags) if flags else "—"

        print(f"[{i}/{len(items)}] {country_name} ({country_code}/{iso3}) | {flags_str} | last: {last_mod} | {title}")
        if preview:
            print(f"    {preview}")

        time.sleep(sleep_sec)  # gentle pacing

    df = pd.DataFrame(rows)
    # Write a CSV snapshot for quick inspection
    df.to_csv("travelwarnings_snapshot.csv", index=False, encoding="utf-8")
    print(f"\nSaved CSV snapshot with {len(df)} rows → travelwarnings_snapshot.csv")

    if WRITE_SQLITE:
        write_sqlite(df, SQLITE_PATH)

    return df

def write_sqlite(df: pd.DataFrame, db_path: str):
    # Two-table schema (normalized-ish): metadata and content, joined by content_id
    meta_cols = [
        "content_id", "title", "country_name", "country_code", "iso3_country_code",
        "last_modified_iso", "effective_iso", "warning", "partial_warning",
        "situation_warning", "situation_part_warning", "source_url"
    ]
    content_cols = ["content_id", "content"]

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS travelwarning_meta (
            content_id INTEGER PRIMARY KEY,
            title TEXT,
            country_name TEXT,
            country_code TEXT,
            iso3_country_code TEXT,
            last_modified_iso TEXT,
            effective_iso TEXT,
            warning INTEGER,
            partial_warning INTEGER,
            situation_warning INTEGER,
            situation_part_warning INTEGER,
            source_url TEXT
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS travelwarning_content (
            content_id INTEGER PRIMARY KEY,
            content TEXT,
            FOREIGN KEY(content_id) REFERENCES travelwarning_meta(content_id)
        )
        """)
        # Upsert (SQLite 3.24+)
        meta_df = df[meta_cols].copy()
        content_df = df[content_cols].copy()

        meta_df.to_sql("travelwarning_meta_tmp", conn, if_exists="replace", index=False)
        content_df.to_sql("travelwarning_content_tmp", conn, if_exists="replace", index=False)

        cur.executescript("""
        INSERT INTO travelwarning_meta
        SELECT * FROM travelwarning_meta_tmp
        ON CONFLICT(content_id) DO UPDATE SET
          title=excluded.title,
          country_name=excluded.country_name,
          country_code=excluded.country_code,
          iso3_country_code=excluded.iso3_country_code,
          last_modified_iso=excluded.last_modified_iso,
          effective_iso=excluded.effective_iso,
          warning=excluded.warning,
          partial_warning=excluded.partial_warning,
          situation_warning=excluded.situation_warning,
          situation_part_warning=excluded.situation_part_warning,
          source_url=excluded.source_url;

        INSERT INTO travelwarning_content
        SELECT * FROM travelwarning_content_tmp
        ON CONFLICT(content_id) DO UPDATE SET
          content=excluded.content;

        DROP TABLE travelwarning_meta_tmp;
        DROP TABLE travelwarning_content_tmp;
        """)
        conn.commit()
    print(f"Saved {len(df)} rows into SQLite → {db_path} (tables: travelwarning_meta, travelwarning_content)")

if __name__ == "__main__":
    try:
        # For a quick test while developing, set limit=10; remove it to fetch all.
        collect_travel_warnings(limit=None)
    except requests.HTTPError as e:
        print("HTTP error:", e, "| response snippet:", getattr(e.response, "text", "")[:300])
    except requests.RequestException as e:
        print("Request error:", e)
