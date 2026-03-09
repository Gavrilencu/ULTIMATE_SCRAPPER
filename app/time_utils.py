# -*- coding: utf-8 -*-
"""
Utilitare pentru fus orar: toată aplicația folosește ora Chișinău (Europe/Chisinau).
Datele sunt stocate în UTC; la afișare se convertesc în timezone-ul configurat.
"""
from datetime import datetime


def get_tz(name="Europe/Chisinau"):
    """Returnează ZoneInfo pentru numele dat."""
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except ImportError:
        try:
            from backports.zoneinfo import ZoneInfo
            return ZoneInfo(name)
        except ImportError:
            return None


def get_app_timezone(app=None):
    """Returnează ZoneInfo pentru timezone-ul aplicației (din config sau Europe/Chisinau)."""
    if app is not None:
        name = app.config.get("TIMEZONE", "Europe/Chisinau")
        return get_tz(name)
    return get_tz("Europe/Chisinau")


def utc_to_local(dt, tz=None):
    """
    Convertește un datetime (considerat UTC, naive) în timezone-ul local (Chișinău).
    Returnează datetime local (naive) sau dt neschimbat dacă tz nu e disponibil.
    """
    if dt is None:
        return None
    if tz is None:
        tz = get_tz("Europe/Chisinau")
    if tz is None:
        return dt
    # Considerăm că dt este UTC (naive)
    from datetime import timezone
    dt_utc = dt.replace(tzinfo=timezone.utc)
    return dt_utc.astimezone(tz).replace(tzinfo=None)


def format_local_datetime(dt, fmt="%d.%m.%Y %H:%M:%S", tz=None):
    """
    Formatează un datetime (UTC în DB) ca string în ora Chișinău.
    """
    local = utc_to_local(dt, tz=tz)
    if local is None:
        return "—"
    return local.strftime(fmt)
