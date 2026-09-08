"""Online OSINT: RDAP WHOIS, IP geolocation/ASN, certificate-transparency
subdomain enumeration, and an optional Shodan host lookup.

Unlike Host Recon (which shells out to local system tools), every check
here talks to a public web API, so the target — and, for Shodan, your API
key — is sent to a third-party service over the network.
"""
from __future__ import annotations

import ipaddress
import socket

from PySide6.QtWidgets import QCheckBox, QFormLayout, QLineEdit, QVBoxLayout, QWidget

from jegeo.core import http, settings
from jegeo.modules.base import BaseModule

RDAP_DOMAIN_URL = "https://rdap.org/domain/{}"
RDAP_IP_URL = "https://rdap.org/ip/{}"
GEO_URL = "https://ipwho.is/{}"
CRTSH_URL = "https://crt.sh/"
SHODAN_HOST_URL = "https://api.shodan.io/shodan/host/{}"


def is_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def vcard_text(vcard_array, field: str) -> str | None:
    """Best-effort pull of a named field (e.g. 'fn') out of an RDAP vCard array."""
    try:
        for entry in vcard_array[1]:
            if entry[0] == field and len(entry) > 3 and entry[3]:
                return entry[3]
    except (IndexError, TypeError):
        pass
    return None


def dedupe_cert_names(rows: list[dict]) -> list[str]:
    names = set()
    for row in rows:
        for raw in str(row.get("name_value", "")).split("\n"):
            cleaned = raw.strip().lstrip("*.")
            if cleaned:
                names.add(cleaned)
    return sorted(names)


class OsintIntelModule(BaseModule):
    display_name = "OSINT Intel"
    glyph = "⌖"
    tagline = "Online WHOIS / geolocation / subdomains / Shodan"
    notice = "Sends the target to public third-party APIs (rdap.org, ipwho.is, crt.sh, optionally Shodan) — only look up things you're authorized to research."

    def build_controls(self) -> QWidget:
        wrapper = QWidget()
        outer = QVBoxLayout(wrapper)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        form = QFormLayout()
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("domain or IP, e.g. example.com or 8.8.8.8")
        form.addRow("TARGET", self.target_input)
        outer.addLayout(form)

        self.chk_rdap = QCheckBox("RDAP WHOIS (online registry lookup)")
        self.chk_rdap.setChecked(True)
        self.chk_geo = QCheckBox("IP geolocation && ASN / ISP")
        self.chk_geo.setChecked(True)
        self.chk_subs = QCheckBox("Subdomain enumeration (certificate transparency — domains only)")
        self.chk_subs.setChecked(True)
        self.chk_shodan = QCheckBox("Shodan host lookup (needs your own API key — see Settings)")
        self.chk_shodan.setChecked(False)
        for c in (self.chk_rdap, self.chk_geo, self.chk_subs, self.chk_shodan):
            outer.addWidget(c)

        return wrapper

    def make_task(self):
        target = self.target_input.text().strip()
        if not target:
            raise ValueError("target is required")
        do_rdap = self.chk_rdap.isChecked()
        do_geo = self.chk_geo.isChecked()
        do_subs = self.chk_subs.isChecked()
        do_shodan = self.chk_shodan.isChecked()
        shodan_key = settings.get("shodan_api_key", "")
        target_is_ip = is_ip(target)

        def task(emit, is_cancelled):
            resolved_ip = target if target_is_ip else None

            if not target_is_ip:
                emit(f"resolving {target}...", "meta")
                try:
                    resolved_ip = socket.gethostbyname(target)
                    emit(f"  -> {resolved_ip}", "success")
                except socket.gaierror as exc:
                    emit(f"  resolution failed: {exc}", "warn")

            if do_rdap:
                emit("== RDAP WHOIS ==", "cyan")
                url = RDAP_IP_URL.format(target) if target_is_ip else RDAP_DOMAIN_URL.format(target)
                try:
                    data = http.get_json(url)
                except Exception as exc:
                    emit(f"  RDAP lookup failed: {exc}", "error")
                else:
                    name = data.get("name") or data.get("ldhName") or target
                    emit(f"  name: {name}", "info")
                    statuses = data.get("status") or []
                    if statuses:
                        emit(f"  status: {', '.join(statuses)}", "info")
                    for ev in data.get("events", []) or []:
                        emit(f"  {ev.get('eventAction', '?')}: {ev.get('eventDate', '?')}", "info")
                    ns = [n.get("ldhName") for n in data.get("nameservers", []) or [] if n.get("ldhName")]
                    if ns:
                        emit(f"  nameservers: {', '.join(ns)}", "info")
                    for ent in data.get("entities", []) or []:
                        roles = ", ".join(ent.get("roles", [])) or "entity"
                        fn = vcard_text(ent.get("vcardArray"), "fn") if ent.get("vcardArray") else None
                        if fn:
                            emit(f"  {roles}: {fn}", "meta")

            if is_cancelled():
                return

            if do_geo:
                emit("== IP GEOLOCATION / ASN ==", "cyan")
                if not resolved_ip:
                    emit("  no IP available to geolocate", "warn")
                else:
                    try:
                        data = http.get_json(GEO_URL.format(resolved_ip))
                    except Exception as exc:
                        emit(f"  geolocation lookup failed: {exc}", "error")
                    else:
                        if data.get("success") is False:
                            emit(f"  lookup returned no data: {data.get('message', 'unknown error')}", "warn")
                        else:
                            city = data.get("city") or "?"
                            region = data.get("region") or "?"
                            country = data.get("country") or "?"
                            emit(f"  location: {city}, {region}, {country}", "info")
                            conn = data.get("connection") or {}
                            isp = conn.get("isp") or conn.get("org") or "?"
                            asn = conn.get("asn", "?")
                            emit(f"  ISP/org: {isp}  (ASN {asn})", "info")

            if is_cancelled():
                return

            if do_subs:
                emit("== SUBDOMAIN ENUMERATION (crt.sh) ==", "cyan")
                if target_is_ip:
                    emit("  skipped — target is an IP, not a domain", "meta")
                else:
                    try:
                        rows = http.get_json(
                            CRTSH_URL, params={"q": f"%.{target}", "output": "json"}, timeout=25,
                        )
                    except Exception as exc:
                        emit(f"  crt.sh lookup failed: {exc}", "error")
                    else:
                        names = dedupe_cert_names(rows)
                        if names:
                            emit(f"  {len(names)} unique name(s) found:", "info")
                            for n in names[:200]:
                                emit(f"    {n}", "success")
                            if len(names) > 200:
                                emit(f"    ... ({len(names) - 200} more truncated)", "meta")
                        else:
                            emit("  no certificate-logged names found", "info")

            if is_cancelled():
                return

            if do_shodan:
                emit("== SHODAN HOST LOOKUP ==", "cyan")
                if not shodan_key:
                    emit("  no Shodan API key configured — add one in the Settings module", "warn")
                elif not resolved_ip:
                    emit("  no IP available to query", "warn")
                else:
                    try:
                        data = http.get_json(SHODAN_HOST_URL.format(resolved_ip), params={"key": shodan_key})
                    except Exception as exc:
                        emit(f"  Shodan lookup failed: {exc}", "error")
                    else:
                        emit(f"  org: {data.get('org', '?')}  isp: {data.get('isp', '?')}  os: {data.get('os') or 'unknown'}", "info")
                        ports = sorted(data.get("ports", []) or [])
                        if ports:
                            emit(f"  open ports seen by Shodan: {', '.join(str(p) for p in ports)}", "info")
                        vulns = data.get("vulns") or []
                        if vulns:
                            emit(f"  flagged CVEs: {', '.join(sorted(vulns)[:20])}", "warn")
                        hostnames = data.get("hostnames") or []
                        if hostnames:
                            emit(f"  hostnames: {', '.join(hostnames)}", "info")

            emit("OSINT sweep complete", "success")

        return task
