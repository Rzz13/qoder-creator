"""
Qoder Creator - Claim Manager
Automate Qoder trial claim via Qoder CLI / device authentication on Linux / Ubuntu & In-Browser PKCE Auth.
"""

import os
import sys
import subprocess
import shutil
import platform
import json
import asyncio
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

from .utils import write_log, load_jsonl
from .config import ACCOUNTS_FILE


class ClaimManager:
    """Handle device trial claim via Qoder CLI (qodercli-wake) & In-Browser PKCE Auth."""

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
            local_cli = Path.home() / ".local" / "bin" / binary
            if local_cli.exists():
                return str(local_cli)
        return None

    @classmethod
    async def auto_device_authorize(cls, page) -> bool:
        """
        Run qodercli login in background to obtain device auth URL,
        then navigate and authorize automatically in the active logged-in browser session.
        """
        cli = cls.get_cli_path()
        if not cli:
            return False

        auth_url = None
        proc = None

        try:
            write_log("Starting background qodercli login for device authorization...", "INFO")
            proc = subprocess.Popen(
                [cli, "login"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            start_time = time.time()
            while time.time() - start_time < 10:
                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break
                if "https://qoder.com/device/selectAccounts" in line:
                    match = re.search(r"https://qoder\.com/device/selectAccounts\?[^\s]+", line)
                    if match:
                        auth_url = match.group(0)
                        break
                await asyncio.sleep(0.2)

            if auth_url:
                write_log(f"Captured device auth URL: {auth_url}", "INFO")
                await page.goto(auth_url, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(3000)

                btns = await page.query_selector_all("button, a")
                for b in btns:
                    try:
                        text = (await b.inner_text()).strip()
                        if any(w in text.lower() for w in ["authorize", "confirm", "allow", "continue", "select"]):
                            await b.click()
                            write_log(f"Clicked device authorization button: '{text}'", "SUCCESS")
                            await page.wait_for_timeout(3000)
                            return True
                    except Exception:
                        pass
        except Exception as e:
            write_log(f"Auto device authorization error: {e}", "WARNING")
        finally:
            if proc and proc.poll() is None:
                proc.terminate()

        return False

    @classmethod
    def claim_via_cli(cls, pat: str, email: str) -> bool:
        """Run qodercli-wake binary on native Linux / Ubuntu."""
        cli = cls.get_cli_path()
        if not cli:
            return False

        try:
            for cmd in [
                [cli, "login", pat],
                [cli, "login", "-t", pat],
                [cli, "login", "--token", pat],
            ]:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if res.returncode == 0 and "unknown option" not in res.stderr.lower():
                    write_log(f"qodercli claim success for {email}", "SUCCESS")
                    return True
        except Exception as e:
            write_log(f"CLI claim error for {email}: {e}", "WARNING")

        return False

    @classmethod
    def claim_via_wsl(cls, pat: str, email: str) -> bool:
        """Claim trial using WSL2 Ubuntu environment on Windows."""
        try:
            wsl_test = subprocess.run(["wsl", "uname"], capture_output=True, text=True, timeout=5)
            if wsl_test.returncode == 0:
                cmd = [
                    "wsl", "bash", "-c",
                    f"export PAT='{pat}' && "
                    f"curl -fsSL https://qoder.sh/install.sh | bash > /dev/null 2>&1 || true && "
                    f"~/.qoder/bin/qodercli-wake login --token '{pat}'"
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
                if res.returncode == 0 and "error" not in res.stderr.lower():
                    write_log(f"WSL Linux claim success for {email}", "SUCCESS")
                    return True
        except Exception as e:
            write_log(f"WSL claim attempt for {email}: {e}", "WARNING")
        return False

    @classmethod
    def claim_via_docker(cls, pat: str, email: str) -> bool:
        """Claim trial inside an isolated Docker Ubuntu container."""
        try:
            docker_check = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=5)
            if docker_check.returncode != 0:
                return False

            cmd = [
                "docker", "run", "--rm",
                "-e", f"PAT={pat}",
                "ubuntu:24.04",
                "bash", "-c",
                "apt-get update -qq && apt-get install -y -qq curl ca-certificates > /dev/null 2>&1 && "
                "curl -fsSL https://qoder.sh/install.sh | bash > /dev/null 2>&1 && "
                "~/.qoder/bin/qodercli-wake login --token $PAT"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if res.returncode == 0 and "error" not in res.stderr.lower():
                write_log(f"Docker container claim success for {email}", "SUCCESS")
                return True
        except Exception as e:
            write_log(f"Docker container claim attempt for {email}: {e}", "WARNING")
        return False

    @classmethod
    async def claim_account(cls, account: Dict[str, Any]) -> bool:
        """
        Claim trial for a given account dict using device authentication.
        """
        email = account.get("email", "?")
        pat = account.get("pat_token")

        if not pat:
            write_log(f"Cannot claim for {email}: missing PAT token", "ERROR")
            return False

        write_log(f"Starting claim for {email}...", "INFO")

        if cls.claim_via_cli(pat, email):
            return True

        if sys.platform == "win32":
            if cls.claim_via_wsl(pat, email):
                return True

        if cls.claim_via_docker(pat, email):
            return True

        write_log(f"Claim requires active qodercli on Linux/Ubuntu or Docker Desktop daemon running for {email}", "WARNING")
        return False

    @classmethod
    async def claim_all(cls) -> List[Dict[str, Any]]:
        """Claim trial for all unclaimed accounts in accounts.jsonl."""
        accounts = load_jsonl(ACCOUNTS_FILE)
        results = []
        modified = False
        for acc in accounts:
            if acc.get("pat_valid") and not acc.get("claimed"):
                ok = await cls.claim_account(acc)
                if ok:
                    acc["claimed"] = True
                    modified = True
                    results.append(acc)
        if modified:
            with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
                for a in accounts:
                    f.write(json.dumps(a, ensure_ascii=False) + "\n")
        return results
