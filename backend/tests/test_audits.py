"""Exécute les 4 audits historiques sous pytest (41 tests internes + 100 samples chacun).

Permet à `pytest` de rester le point d'entrée unique de la validation,
tout en conservant les scripts build*_audit.py exécutables individuellement.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AUDITS = ["build1_2_audit.py", "build12_audit.py",
          "build13_audit.py", "build14_audit.py"]


@pytest.mark.parametrize("script", AUDITS)
def test_audit_passes(script):
    result = subprocess.run([sys.executable, script], cwd=ROOT,
                            capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"status": "PASS"' in result.stdout, result.stdout
