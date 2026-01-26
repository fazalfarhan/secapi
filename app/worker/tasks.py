"""Celery tasks for security scanning."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from app.worker import celery_app


@celery_app.task(name="trivy_scan")
def trivy_scan(target: str, scan_type: str = "filesystem") -> dict:
    """
    Run Trivy security scan.

    Args:
        target: Target to scan (file path, image URL, or git repo)
        scan_type: Type of scan - filesystem, image, or repo

    Returns:
        Scan results as dict
    """
    cmd = ["trivy", scan_type, "--format", "json", target]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minutes
        )

        if result.stdout:
            return {
                "success": True,
                "target": target,
                "scan_type": scan_type,
                "results": json.loads(result.stdout),
            }
        else:
            return {
                "success": True,
                "target": target,
                "scan_type": scan_type,
                "results": {"Vulnerabilities": []},
                "stderr": result.stderr,
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "target": target,
            "error": "Scan timed out after 30 minutes",
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "target": target,
            "error": f"Failed to parse Trivy output: {e}",
            "raw_output": result.stdout if 'result' in locals() else None,
        }
    except Exception as e:
        return {
            "success": False,
            "target": target,
            "error": str(e),
        }
