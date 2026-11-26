"""Medición ligera del consumo del proceso actual (sin dependencias): CPU acumulada y memoria residente.

- CPU: os.times() (usuario + sistema del proceso), multiplataforma.
- Memoria residente: /proc/self/status (Linux, contenedores) o GetProcessMemoryInfo (Windows).
"""
import os
import sys
import time
import uuid

INSTANCE_ID = uuid.uuid4().hex[:12]  # identifica el proceso: evita restar contadores de procesos distintos
_STARTED = time.time()


def _rss_bytes():
    try:
        with open("/proc/self/status", encoding="ascii") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
    except OSError:
        pass
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class Counters(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
            counters = Counters()
            counters.cb = ctypes.sizeof(Counters)
            kernel32, psapi = ctypes.WinDLL("kernel32"), ctypes.WinDLL("psapi")
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
            if psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
                return int(counters.WorkingSetSize)
        except (OSError, AttributeError):
            return None
    return None


def snapshot():
    times = os.times()
    return {"instance_id": INSTANCE_ID, "cpu_seconds": times.user + times.system, "rss_bytes": _rss_bytes(),
            "uptime_seconds": time.time() - _STARTED}
