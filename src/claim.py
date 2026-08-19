"""
Qoder Creator - Claim Manager
Automate Qoder trial claim via Qoder CLI / device API on Linux / Ubuntu.
"""

import os
import sys
import subprocess
import shutil
import platform
import json
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Any, List

from .utils import write_log, load_jsonl, generate_machine_id
from .config import ACCOUNTS_FILE


class ClaimManager:
    """Handle trial claim on Linux / Ubuntu."""

    @staticmethod
    def is_linux() -> bool:
        return platform.system() == "Linux"

    @staticmethod
    def get_cli_path() -> Optional[str]:
        """Check if qodercli or qodercli-wake is installed in PATH or local dir."""
        for binary in ["qodercli-wake", "qodercli", "qoder"]:
            path = shutil.which(binary)
            if path:
                return path
            local_bin = Path.home() / ".qoder" / "bin" / binary
            if local_bin.exists():
                return str(local_bin)
        return None

    @classmethod
    async def claim_account(cls, account: Dict[str, Any]) -> bool:
        """
        Claim trial for a given account dict (containing email, pat_token, etc.).
        Returns True if successful.
        """
        email = account.get("email", "?")
        pat = account.get("pat_token")

        if not pat:
            write_log(f"Cannot claim for {email}: missing PAT token", "ERROR")
            return False

        write_log(f"Starting claim for {email}...", "INFO")

        # 1. Try via qodercli-wake / qodercli binary if available
        cli = cls.get_cli_path()
        if cli:
            try:
                cmd = [cli, "login", "--token", pat]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if res.returncode == 0:
                    write_log(f"CLI claim success for {email}", "SUCCESS")
                    return True

                # Try protocol handler URI
                uri = f"qoder://login?token={pat}"
                res_uri = subprocess.run([cli, uri], capture_output=True, text=True, timeout=30)
                if res_uri.returncode == 0:
                    write_log(f"CLI URI claim success for {email}", "SUCCESS")
                    return True
            except Exception as e:
                write_log(f"CLI claim error: {e}", "WARNING")

        # 2. Device API claim request with hardware fingerprint header
        try:
            url = "https://openapi.qoder.sh/api/v1/user/claim-trial"
            req = urllib.request.Request(url, method="POST")
            req.add_header("Authorization", f"Bearer {pat}")
            req.add_header("Content-Type", "application/json")
            req.add_header("X-Device-Id", generate_machine_id())
            req.add_header("User-Agent", "QoderCLI/1.0 (Ubuntu Linux x86_64)")

            body = json.dumps({"source": "cli", "platform": "linux"}).encode()
            with urllib.request.urlopen(req, data=body, timeout=15) as resp:
                status = resp.status
                res_body = resp.read().decode()
                if status in (200, 201):
                    write_log(f"API claim success for {email}: {res_body}", "SUCCESS")
                    return True
        except Exception as e:
            write_log(f"API claim for {email}: {e}", "WARNING")

        return False

    @classmethod
    async def claim_all(cls) -> List[Dict[str, Any]]:
        """Claim trial for all unclaimed accounts in accounts.jsonl."""
        accounts = load_jsonl(ACCOUNTS_FILE)
        results = []
        for acc in accounts:
            if acc.get("pat_valid") and not acc.get("claimed"):
                ok = await cls.claim_account(acc)
                acc["claimed"] = ok
                results.append(acc)
        return results
