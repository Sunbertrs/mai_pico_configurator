from __future__ import annotations

import json
import os
import subprocess

# This script for Powershell returns a list like [{"Port": "COMxx", "Name": "Mai Pico Port"}, ...]
script = r"""
Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
    Where-Object { $_.Class -eq 'Ports' } |
    ForEach-Object {
        $desc = (Get-PnpDeviceProperty -InstanceId $_.InstanceId `
                 -KeyName 'DEVPKEY_Device_BusReportedDeviceDesc' `
                 -ErrorAction SilentlyContinue).Data
        if ($desc -and $_.FriendlyName -match '\((COM\d+)\)') {
            [PSCustomObject]@{ Port = $Matches[1]; Name = $desc }
        }
    } |
ConvertTo-Json -Compress
"""

_cache: dict = None


def detect_ports(refresh: bool = False) -> dict[str, str]:
    """
    Return {"COMxx": "Mai Pico Port", ...}

    The result is cached because starting PowerShell costs about a second;
    pass refresh=True to scan again after plugging a device in.
    """
    global _cache
    if _cache is not None and not refresh:
        return _cache

    port_list = {}
    if os.name == "nt":
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            items = json.loads(result.stdout)
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
            items = []
        for item in items:
            if "mai pico" in item["Name"].lower():
                port_list[item["Port"]] = item["Name"]

    _cache = port_list
    return port_list

if __name__=="__main__":
    print(detect_ports())