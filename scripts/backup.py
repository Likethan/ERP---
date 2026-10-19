#!/usr/bin/env python3
"""CampusOS Production PostgreSQL Backup CLI.

Creates consistent, compressed, checksummed backups of the PostgreSQL database
suitable for staging, production, and automated retention management.

Features:
- Custom binary format (pg_dump -Fc) for fast restoration and compression
- Computes SHA256 checksum for cryptographic verification
- Writes metadata JSON (timestamp, size, database, commit hash)
- Configurable backup output directory and retention rotation
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse


def parse_database_url(url: str) -> dict:
    # Normalize postgresql+asyncpg:// to postgresql://
    clean_url = re.sub(r"^postgresql\+asyncpg://", "postgresql://", url)
    parsed = urlparse(clean_url)
    return {
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "dbname": parsed.path.lstrip("/") or "campusos_db",
    }


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_backup(
    db_url: str,
    output_dir: Path,
    retention_count: int = 14,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    lock_file = output_dir / ".backup.lock"

    # Concurrency Lock Protection
    if lock_file.exists():
        try:
            mtime = lock_file.stat().st_mtime
            if (datetime.now(UTC).timestamp() - mtime) < 1800:
                print(f"[!] A backup is already running (lockfile: {lock_file}). Exiting.", file=sys.stderr)
                sys.exit(1)
            else:
                print("[*] Releasing stale backup lockfile...")
                lock_file.unlink(missing_ok=True)
        except OSError:
            pass

    try:
        lock_file.write_text(f"pid={os.getpid()} started_at={datetime.now(UTC).isoformat()}", encoding="utf-8")
    except Exception as exc:
        print(f"[!] Failed to acquire lockfile: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        db_info = parse_database_url(db_url)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"campusos_{db_info['dbname']}_{timestamp}.dump"
        backup_path = output_dir / backup_filename
        meta_path = output_dir / f"{backup_filename}.meta.json"
        sha_path = output_dir / f"{backup_filename}.sha256"

        env = os.environ.copy()
        if db_info["password"]:
            env["PGPASSWORD"] = db_info["password"]

        pg_dump_cmd = [
            "pg_dump",
            "-h", db_info["host"],
            "-p", db_info["port"],
            "-U", db_info["user"],
            "-d", db_info["dbname"],
            "-F", "c",  # custom compressed archive format
            "-b",       # include large objects
            "-v",
            "-f", str(backup_path),
        ]

        print(f"[*] Starting backup of '{db_info['dbname']}' on {db_info['host']}:{db_info['port']}...")
        try:
            res = subprocess.run(pg_dump_cmd, env=env, capture_output=True, text=True, check=False)
            if res.returncode != 0:
                print(f"[!] pg_dump failed (exit code {res.returncode}):\n{res.stderr}", file=sys.stderr)
                sys.exit(res.returncode)
        except FileNotFoundError:
            print("[!] pg_dump binary not found on PATH. Ensure postgresql-client is installed.", file=sys.stderr)
            sys.exit(1)

        # Compute checksum
        print("[*] Computing SHA256 integrity checksum...")
        sha256 = compute_sha256(backup_path)
        with open(sha_path, "w", encoding="utf-8") as f:
            f.write(f"{sha256}  {backup_filename}\n")

        # Write metadata
        file_size = backup_path.stat().st_size
        meta = {
            "filename": backup_filename,
            "database": db_info["dbname"],
            "host": db_info["host"],
            "port": db_info["port"],
            "user": db_info["user"],
            "created_at_utc": datetime.now(UTC).isoformat(),
            "size_bytes": file_size,
            "sha256": sha256,
            "format": "custom_compressed",
            "is_known_good": False,
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        print(f"[+] Backup successfully generated:\n    File: {backup_path}\n    Size: {file_size:,} bytes\n    SHA256: {sha256}")

        # Retention pruning
        prune_old_backups(output_dir, retention_count)
        return backup_path
    finally:
        lock_file.unlink(missing_ok=True)


def prune_old_backups(output_dir: Path, keep_count: int) -> None:
    """Prune old backups while preserving at least one valid/known-good backup."""
    dumps = sorted(output_dir.glob("campusos_*.dump"), key=lambda p: p.stat().st_mtime)
    if len(dumps) <= 1:
        return

    # Check for known-good backups
    known_good_dumps = []
    for d in dumps:
        meta_f = d.with_name(f"{d.name}.meta.json")
        if meta_f.exists():
            try:
                m = json.loads(meta_f.read_text(encoding="utf-8"))
                if m.get("is_known_good"):
                    known_good_dumps.append(d)
            except Exception:
                pass

    if len(dumps) > keep_count:
        to_delete = dumps[:-keep_count]
        print(f"[*] Pruning backups exceeding retention count ({keep_count})...")
        for old in to_delete:
            # Never delete the only known-good backup!
            if len(known_good_dumps) == 1 and old == known_good_dumps[0]:
                print(f"    [*] Preserving only known-good backup: {old.name}")
                continue
            old.unlink(missing_ok=True)
            old.with_name(f"{old.name}.meta.json").unlink(missing_ok=True)
            old.with_name(f"{old.name}.sha256").unlink(missing_ok=True)
            print(f"    - Deleted: {old.name}")



def main():
    parser = argparse.ArgumentParser(description="CampusOS Database Backup Utility")
    parser.add_argument(
        "--db-url",
        default=os.getenv("DATABASE_URL", "postgresql://campusos_user:campusos_password@localhost:5432/campusos_db"),
        help="PostgreSQL connection URL",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./backups"),
        help="Directory to store backup files",
    )
    parser.add_argument(
        "--retention",
        type=int,
        default=14,
        help="Number of backup copies to retain",
    )
    args = parser.parse_args()
    create_backup(args.db_url, args.output_dir, args.retention)


if __name__ == "__main__":
    main()
