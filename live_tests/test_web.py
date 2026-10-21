"""The website and the API are up, routed and hardened. Needs only BASE_URL."""

import re

import pytest
import requests

TIMEOUT = 15


def get(url, **kwargs):
    return requests.get(url, timeout=TIMEOUT, **kwargs)


def test_api_health(base_url):
    response = get(f"{base_url}/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("path", ["/", "/login", "/dashboard", "/settings", "/help", "/no-such-page"])
def test_frontend_routes_serve_the_app(base_url, path):
    response = get(base_url + path)
    assert response.status_code == 200
    assert "text/html" in response.headers["Content-Type"]
    assert '<div id="root">' in response.text


def test_page_security_headers(base_url):
    headers = get(base_url + "/").headers
    csp = headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp and "frame-ancestors 'none'" in csp, "CSP missing (Vite dev server?)"
    assert "'unsafe-inline'" not in csp
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("Referrer-Policy") == "no-referrer"
    assert "nginx/" not in headers.get("Server", ""), "server version is disclosed"


def test_index_is_revalidated_and_assets_are_cached(base_url):
    index = get(base_url + "/")
    assert "no-cache" in index.headers.get("Cache-Control", "")
    asset = re.search(r'src="(/assets/[^"]+\.js)"', index.text).group(1)
    response = get(base_url + asset)
    assert response.status_code == 200
    assert "immutable" in response.headers.get("Cache-Control", "")
    compressed = get(base_url + asset, headers={"Accept-Encoding": "gzip"})
    assert compressed.headers.get("Content-Encoding") == "gzip"


def test_api_security_headers(base_url):
    headers = get(f"{base_url}/api/health").headers
    assert headers.get("Cache-Control") == "no-store"
    assert "default-src 'none'" in headers.get("Content-Security-Policy", "")
    assert headers.get("X-Content-Type-Options") == "nosniff"


def test_api_errors_are_json_without_internals(base_url):
    for response in (
        get(f"{base_url}/api/does-not-exist"),
        requests.post(f"{base_url}/api/auth/login", data="{broken", timeout=TIMEOUT),
    ):
        assert response.headers["Content-Type"].startswith("application/json")
        assert set(response.json()) >= {"error", "code"}
        assert "Traceback" not in response.text and "SQL" not in response.text


@pytest.mark.parametrize("path", ["/account", "/aliases"])
def test_private_endpoints_require_login(base_url, path):
    response = get(f"{base_url}/api{path}")
    assert response.status_code == 401
    forged = get(f"{base_url}/api{path}", headers={"Authorization": "Bearer eyJhbGciOiJub25lIn0.e30."})
    assert forged.status_code == 401


def test_cors_is_closed_to_other_sites(base_url):
    response = requests.options(
        f"{base_url}/api/aliases",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
        timeout=TIMEOUT,
    )
    assert "Access-Control-Allow-Origin" not in response.headers


def test_wrong_login_is_rejected_uniformly(base_url):
    response = requests.post(
        f"{base_url}/api/auth/login", json={"email": "nobody@example.com", "password": "Wrong-pass1"}, timeout=TIMEOUT
    )
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"
    assert "X-RateLimit-Limit" in response.headers, "rate limiting is not active"


def test_https(base_url):
    if not base_url.startswith("https://"):
        pytest.skip("BASE_URL is not https")
    host = base_url.split("://", 1)[1]
    plain = get(f"http://{host}/", allow_redirects=False)
    assert plain.status_code in (301, 302, 307, 308), "http:// should redirect to https://"
    assert plain.headers["Location"].startswith("https://")
    # requests verifies the certificate chain and host name by default
    headers = get(base_url + "/").headers
    assert "max-age=" in headers.get("Strict-Transport-Security", ""), "enable HSTS once https works"
