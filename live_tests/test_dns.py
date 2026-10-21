"""DNS records needed to receive mail and to deliver it without landing in spam.

Needs MAIL_DOMAIN; SERVER_IP additionally checks that the records point at the right machine.
"""

import ipaddress

import dns.reversename
import pytest

from live_support import lookup


@pytest.fixture(scope="module")
def server_ip(settings, mx_host):
    return settings.server_ip or (lookup(mx_host, "A") or [None])[0]


def test_mx_host_resolves_to_the_server(mx_host, settings):
    addresses = lookup(mx_host, "A")
    assert addresses, f"{mx_host} has no A record"
    if settings.server_ip:
        assert settings.server_ip in addresses, f"{mx_host} points to {addresses}, not {settings.server_ip}"


def test_website_resolves_to_the_server(settings, mail_domain):
    host = settings.web_host or mail_domain
    try:
        ipaddress.ip_address(host)
        pytest.skip("BASE_URL uses an IP address")
    except ValueError:
        pass
    if host == "localhost":
        pytest.skip("BASE_URL is local")
    addresses = lookup(host, "A")
    assert addresses, f"{host} has no A record"
    if settings.server_ip:
        assert settings.server_ip in addresses


def spf_allows(record, ip, domain, depth=0):
    """Small SPF evaluator for the ip4/ip6/a/mx/include mechanisms and the redirect modifier."""
    ip = ipaddress.ip_address(ip)
    for term in record.split()[1:]:
        term = term.lstrip("+")
        mechanism, _, value = term.partition(":")
        if mechanism in ("ip4", "ip6"):
            if ip in ipaddress.ip_network(value, strict=False):
                return True
        elif mechanism == "a" and str(ip) in lookup(value or domain, "A"):
            return True
        elif mechanism == "mx" and any(str(ip) in lookup(host, "A") for host in lookup(value or domain, "MX")):
            return True
        elif (mechanism == "include" or term.startswith("redirect=")) and depth < 5:
            target = value or term.partition("=")[2]
            included = [t for t in lookup(target, "TXT") if t.lower().startswith("v=spf1")]
            if included and spf_allows(included[0], ip, target, depth + 1):
                return True
    return False


def test_spf(mail_domain, server_ip):
    records = [t for t in lookup(mail_domain, "TXT") if t.lower().startswith("v=spf1")]
    assert len(records) == 1, f'expected exactly one SPF record, found {records}; add  TXT @ "v=spf1 mx -all"'
    record = records[0]
    ends_well = record.split()[-1] in ("-all", "~all") or "redirect=" in record
    assert ends_well, f"SPF should end with -all (or ~all), otherwise anyone may send as {mail_domain}: {record}"
    if server_ip:
        assert spf_allows(record, server_ip, mail_domain), f"SPF does not authorise the server {server_ip}: {record}"


def test_dmarc(mail_domain):
    records = [t for t in lookup(f"_dmarc.{mail_domain}", "TXT") if t.startswith("v=DMARC1")]
    assert len(records) == 1, f'add  TXT _dmarc "v=DMARC1; p=none; rua=mailto:you@{mail_domain}"'
    assert any(f"p={policy}" in records[0].replace(" ", "") for policy in ("none", "quarantine", "reject"))


def test_dkim(mail_domain, settings):
    name = f"{settings.dkim_selector}._domainkey.{mail_domain}"
    records = lookup(name, "TXT")
    assert records, f"no DKIM key at {name} (set DKIM_SELECTOR if you use another selector)"
    key = records[0].replace(" ", "")
    assert "p=" in key and not key.endswith("p="), f"DKIM record has no public key: {records[0]}"


def test_reverse_dns_matches_the_mail_host(mx_host, server_ip):
    """Gmail and others reject mail from an IP whose PTR does not match its forward name."""
    assert server_ip, "cannot determine the server IP"
    names = lookup(dns.reversename.from_address(server_ip), "PTR")
    assert names, f"{server_ip} has no PTR record; ask the hosting provider to set it to {mx_host}"
    assert mx_host in names, f"PTR of {server_ip} is {names}; ask the hosting provider to set it to {mx_host}"
    assert server_ip in lookup(mx_host, "A")  # forward-confirmed reverse DNS


def test_ipv6_reverse_dns(mx_host):
    addresses = lookup(mx_host, "AAAA")
    if not addresses:
        pytest.skip(f"{mx_host} has no IPv6 address (make Postfix send over IPv4: inet_protocols = ipv4)")
    for address in addresses:
        names = lookup(dns.reversename.from_address(address), "PTR")
        assert mx_host in names, f"IPv6 {address} needs a PTR record pointing to {mx_host}"
