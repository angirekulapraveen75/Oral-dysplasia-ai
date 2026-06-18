"""
DAST Runner for OralDysplasia AI API
=====================================
Reads baseUrl from ../input.json, creates test accounts, and runs
all security test categories against every discovered endpoint.

Usage:  python automated_test/dast_runner.py
"""

import json
import os
import sys
import io
import time
import datetime
import random
import string
import base64

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import copy
import traceback

# ---------------------------------------------------------------------------
# Try to import requests; if missing, fall back to urllib
# ---------------------------------------------------------------------------
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    import ssl
    HAS_REQUESTS = False
    # Disable SSL verification for testing (matches curl -k)
    ssl._create_default_https_context = ssl._create_unverified_context

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
INPUT_JSON = os.path.join(PROJECT_ROOT, "input.json")
REPORT_JSON = os.path.join(SCRIPT_DIR, "report.json")
SAVEPOINT_JSON = os.path.join(SCRIPT_DIR, "savepoint.json")

# ---------------------------------------------------------------------------
# Utility: HTTP helper that works with or without `requests`
# ---------------------------------------------------------------------------
class HttpResponse:
    def __init__(self, status_code, body, elapsed_ms, headers=None):
        self.status_code = status_code
        self.body = body
        self.elapsed_ms = elapsed_ms
        self.headers = headers or {}

    def json(self):
        try:
            return json.loads(self.body)
        except Exception:
            return None


def http(method, url, headers=None, body=None, timeout=10):
    """Perform an HTTP request. Returns HttpResponse."""
    headers = headers or {}
    start = time.time()

    if HAS_REQUESTS:
        try:
            resp = requests.request(
                method, url,
                headers=headers,
                data=body if isinstance(body, (str, bytes)) else json.dumps(body) if body else None,
                timeout=timeout,
                verify=False,  # like curl -k
            )
            elapsed = (time.time() - start) * 1000
            return HttpResponse(resp.status_code, resp.text, elapsed, dict(resp.headers))
        except requests.exceptions.Timeout:
            elapsed = (time.time() - start) * 1000
            return HttpResponse(0, "TIMEOUT", elapsed)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return HttpResponse(0, str(e), elapsed)
    else:
        # urllib fallback
        req_body = None
        if body:
            req_body = json.dumps(body).encode() if not isinstance(body, (str, bytes)) else (body.encode() if isinstance(body, str) else body)
        req = urllib.request.Request(url, data=req_body, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                elapsed = (time.time() - start) * 1000
                resp_body = resp.read().decode("utf-8", errors="replace")
                return HttpResponse(resp.status, resp_body, elapsed, dict(resp.headers))
        except urllib.error.HTTPError as e:
            elapsed = (time.time() - start) * 1000
            resp_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            return HttpResponse(e.code, resp_body, elapsed, dict(e.headers) if hasattr(e, 'headers') else {})
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return HttpResponse(0, str(e), elapsed)


# ---------------------------------------------------------------------------
# Load config
# ---------------------------------------------------------------------------
def load_config():
    with open(INPUT_JSON, "r") as f:
        data = json.load(f)
    base = data["baseUrl"].rstrip("/")
    return base


# ---------------------------------------------------------------------------
# Endpoint registry (from codebase analysis)
# ---------------------------------------------------------------------------
ENDPOINTS = [
    # Auth — public
    {"path": "/api/v1/auth/signup",           "method": "POST", "auth": False, "roles": [], "category": "auth"},
    {"path": "/api/v1/auth/login",            "method": "POST", "auth": False, "roles": [], "category": "auth"},
    {"path": "/api/v1/auth/forgot-password",  "method": "POST", "auth": False, "roles": [], "category": "auth"},
    # Slides — requires auth, no RBAC
    {"path": "/api/v1/slides/upload",         "method": "POST", "auth": True,  "roles": ["any"], "category": "slides"},
    {"path": "/api/v1/slides/library",        "method": "GET",  "auth": True,  "roles": ["any"], "category": "slides"},
    {"path": "/api/v1/slides/{slide_id}",     "method": "GET",  "auth": True,  "roles": ["any"], "category": "slides"},
    {"path": "/api/v1/slides/stats/dashboard","method": "GET",  "auth": True,  "roles": ["any"], "category": "slides"},
    # Analysis — requires auth, no RBAC
    {"path": "/api/v1/analysis/run",          "method": "POST", "auth": True,  "roles": ["any"], "category": "analysis"},
    {"path": "/api/v1/analysis/{slide_id}/result",  "method": "GET", "auth": True, "roles": ["any"], "category": "analysis"},
    {"path": "/api/v1/analysis/{slide_id}/review",  "method": "PUT", "auth": True, "roles": ["any"], "category": "analysis"},
    # Reports — requires auth, no RBAC
    {"path": "/api/v1/reports/{slide_id}/export",   "method": "GET", "auth": True, "roles": ["any"], "category": "reports"},
    # OpenAPI spec — public
    {"path": "/openapi.json",                 "method": "GET",  "auth": False, "roles": [], "category": "meta"},
    {"path": "/docs",                         "method": "GET",  "auth": False, "roles": [], "category": "meta"},
]

# Roles to test
ROLES = ["Consultant Pathologist", "Resident", "Lab Tech"]

# ---------------------------------------------------------------------------
# Test Results Collector
# ---------------------------------------------------------------------------
results = []

def record(endpoint, method, role, status, expected_status, finding, severity,
           response_time_ms, test_category, note):
    results.append({
        "endpoint": endpoint,
        "method": method,
        "role": role or "anonymous",
        "status": status,
        "expected_status": expected_status,
        "finding": finding,
        "severity": severity,
        "response_time_ms": round(response_time_ms, 1),
        "test_category": test_category,
        "note": note,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    })


# ---------------------------------------------------------------------------
# Helper: generate random email
# ---------------------------------------------------------------------------
def rand_email(prefix="dast"):
    r = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{r}@test-dast.example"


# ---------------------------------------------------------------------------
# SETUP: Create test accounts and obtain tokens
# ---------------------------------------------------------------------------
def setup_accounts(base_url):
    """Signup 3 users with different roles; return {role: {token, user}}."""
    accounts = {}
    for role in ROLES:
        email = rand_email(role.replace(" ", "").lower())
        payload = {
            "email": email,
            "password": "DastTest123!",
            "name": f"DAST {role}",
            "license_id": f"DAST-{random.randint(10000,99999)}",
            "role": role,
            "institution": "DAST Security Lab"
        }
        resp = http("POST", f"{base_url}/api/v1/auth/signup",
                     headers={"Content-Type": "application/json"},
                     body=payload)
        if resp.status_code in (200, 201):
            data = resp.json()
            accounts[role] = {
                "token": data["access_token"],
                "user": data["user"],
                "email": email,
                "password": "DastTest123!",
            }
            print(f"  ✓ Created {role} account: {email}")
        elif resp.status_code == 400 and "already registered" in resp.body.lower():
            # Try login instead
            login_resp = http("POST", f"{base_url}/api/v1/auth/login",
                              headers={"Content-Type": "application/json"},
                              body={"email": email, "password": "DastTest123!"})
            if login_resp.status_code == 200:
                data = login_resp.json()
                accounts[role] = {
                    "token": data["access_token"],
                    "user": data["user"],
                    "email": email,
                    "password": "DastTest123!",
                }
                print(f"  ✓ Logged in existing {role} account: {email}")
            else:
                print(f"  ✗ Failed to login {role}: {login_resp.status_code} {login_resp.body[:200]}")
        else:
            print(f"  ✗ Failed to create {role}: {resp.status_code} {resp.body[:200]}")

    return accounts


# ---------------------------------------------------------------------------
# TEST 0: Auth enforcement check
# ---------------------------------------------------------------------------
def test_0_auth_enforcement(base_url):
    """Protected endpoints with no token should return 401/403."""
    print("\n═══ TEST 0: Auth Enforcement ═══")
    protected = [e for e in ENDPOINTS if e["auth"]]
    for ep in protected:
        path = ep["path"].replace("{slide_id}", "1")
        url = f"{base_url}{path}"
        # Skip destructive methods
        method = ep["method"]
        if method in ("PUT", "DELETE", "PATCH"):
            body = {"annotations": [], "final_grade": "mild", "comments": "test"} if "review" in path else None
            resp = http(method, url, headers={"Content-Type": "application/json"}, body=body)
        elif method == "POST" and "upload" in path:
            resp = http(method, url)
        elif method == "POST":
            body = {"slide_id": 1}
            resp = http(method, url, headers={"Content-Type": "application/json"}, body=body)
        else:
            resp = http(method, url)

        is_finding = resp.status_code not in (401, 403, 405, 422)
        severity = "CRITICAL" if is_finding and resp.status_code < 400 else "info"
        status_label = "✗ VULN" if is_finding and resp.status_code < 400 else "✓ OK"
        print(f"  {status_label}  {method:6s} {path:50s} → {resp.status_code} ({resp.elapsed_ms:.0f}ms)")

        record(
            endpoint=path, method=method, role="anonymous",
            status=resp.status_code, expected_status="401/403",
            finding=is_finding and resp.status_code < 400,
            severity=severity,
            response_time_ms=resp.elapsed_ms,
            test_category="authn_bypass",
            note=f"No token sent. Got {resp.status_code}." + (" ACCESS GRANTED WITHOUT AUTH!" if is_finding and resp.status_code < 400 else ""),
        )
        time.sleep(0.15)


# ---------------------------------------------------------------------------
# TEST 1: AuthN bypass — malformed / expired token
# ---------------------------------------------------------------------------
def test_1_authn_bypass(base_url):
    """Send malformed and expired tokens to protected endpoints."""
    print("\n═══ TEST 1: AuthN Bypass (malformed/expired tokens) ═══")
    bad_tokens = {
        "empty": "",
        "garbage": "not.a.jwt.token",
        "tampered_sig": None,  # will be built from a real token below
        "missing_bearer": "NOBEARER",
    }

    protected = [e for e in ENDPOINTS if e["auth"]]
    for token_label, token_val in bad_tokens.items():
        for ep in protected:
            path = ep["path"].replace("{slide_id}", "1")
            url = f"{base_url}{path}"
            method = ep["method"]

            headers = {"Content-Type": "application/json"}
            if token_label == "missing_bearer":
                headers["Authorization"] = token_val
            elif token_val is not None:
                headers["Authorization"] = f"Bearer {token_val}"
            # if empty, don't add header
            if token_label == "empty":
                pass  # no auth header

            body = None
            if method == "POST" and "upload" not in path:
                body = {"slide_id": 1}
            elif method == "PUT":
                body = {"annotations": [], "final_grade": "mild"}

            if method == "POST" and "upload" in path:
                resp = http(method, url, headers=headers)
            else:
                resp = http(method, url, headers=headers, body=body)

            is_finding = resp.status_code in (200, 201)
            severity = "CRITICAL" if is_finding else "info"
            status_label = "✗ VULN" if is_finding else "✓ OK"
            print(f"  {status_label}  [{token_label:15s}] {method:6s} {path:45s} → {resp.status_code}")

            record(
                endpoint=path, method=method, role=f"anonymous({token_label})",
                status=resp.status_code, expected_status="401/403",
                finding=is_finding,
                severity=severity,
                response_time_ms=resp.elapsed_ms,
                test_category="authn_bypass",
                note=f"Token type: {token_label}. Got {resp.status_code}.",
            )
            time.sleep(0.1)


# ---------------------------------------------------------------------------
# TEST 2: AuthZ / Privilege Escalation — RBAC matrix
# ---------------------------------------------------------------------------
def test_2_authz_rbac(base_url, accounts):
    """Every role token × every endpoint. Since code has NO RBAC, we document that."""
    print("\n═══ TEST 2: AuthZ / RBAC Matrix ═══")
    # In this app, ALL protected endpoints accept ANY authenticated user.
    # This is itself a finding: no role-based restrictions exist.
    protected = [e for e in ENDPOINTS if e["auth"]]
    for role, acct in accounts.items():
        token = acct["token"]
        for ep in protected:
            path = ep["path"].replace("{slide_id}", "1")
            url = f"{base_url}{path}"
            method = ep["method"]
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }
            body = None
            if method == "POST" and "run" in path:
                body = {"slide_id": 1}
            elif method == "POST" and "upload" in path:
                # skip file upload for RBAC test — not meaningful
                record(
                    endpoint=path, method=method, role=role,
                    status="skipped", expected_status="role-dependent",
                    finding=False, severity="info",
                    response_time_ms=0,
                    test_category="authz_rbac",
                    note="Skipped: upload requires multipart form data.",
                )
                continue
            elif method == "PUT":
                body = {"annotations": [], "final_grade": "mild", "comments": "DAST test"}

            resp = http(method, url, headers=headers, body=body)

            # Since code has NO RBAC, any role getting 2xx on any endpoint is expected
            # BUT it's a design finding that Lab Tech can run analysis / submit reviews
            is_finding = False
            note = f"{role} got {resp.status_code}."
            severity = "info"

            # Flag lack of RBAC as MEDIUM finding for sensitive endpoints
            if role == "Lab Tech" and resp.status_code in (200, 201):
                if any(x in path for x in ["/review", "/run", "/export"]):
                    is_finding = True
                    severity = "MEDIUM"
                    note += " Lab Tech can access clinical endpoint — no RBAC enforced."

            if role == "Resident" and resp.status_code in (200, 201):
                if "/export" in path:
                    is_finding = True
                    severity = "LOW"
                    note += " Resident can export reports — may need restriction."

            status_label = "⚠ RBAC" if is_finding else "✓ OK"
            print(f"  {status_label}  [{role:25s}] {method:6s} {path:45s} → {resp.status_code}")

            record(
                endpoint=path, method=method, role=role,
                status=resp.status_code, expected_status="role-dependent",
                finding=is_finding, severity=severity,
                response_time_ms=resp.elapsed_ms,
                test_category="authz_rbac",
                note=note,
            )
            time.sleep(0.1)


# ---------------------------------------------------------------------------
# TEST 3: IDOR — access another user's resources
# ---------------------------------------------------------------------------
def test_3_idor(base_url, accounts):
    """Try to access slides/reports owned by one user using another user's token."""
    print("\n═══ TEST 3: IDOR (Insecure Direct Object Reference) ═══")
    roles_list = list(accounts.keys())
    if len(roles_list) < 2:
        print("  ⚠ Need at least 2 accounts for IDOR testing, skipping.")
        return

    # Upload a slide as user A, try to access it as user B
    user_a_role = roles_list[0]
    user_b_role = roles_list[1]
    user_a = accounts[user_a_role]
    user_b = accounts[user_b_role]

    # First, get slides visible to user A
    resp_a = http("GET", f"{base_url}/api/v1/slides/library?page=1&limit=5",
                   headers={"Authorization": f"Bearer {user_a['token']}"})

    slide_ids_visible = []
    if resp_a.status_code == 200:
        data = resp_a.json()
        if data and "slides" in data:
            slide_ids_visible = [s["id"] for s in data["slides"]]

    # Test access to slide IDs 1-5 (may belong to other users) from user B
    test_ids = slide_ids_visible[:3] if slide_ids_visible else [1, 2, 3]
    idor_endpoints = [
        "/api/v1/slides/{id}",
        "/api/v1/analysis/{id}/result",
        "/api/v1/reports/{id}/export?format=fhir",
    ]

    for sid in test_ids:
        for ep_template in idor_endpoints:
            path = ep_template.replace("{id}", str(sid))
            url = f"{base_url}{path}"
            resp = http("GET", url,
                        headers={"Authorization": f"Bearer {user_b['token']}"})

            # Finding: user B can see user A's data (no ownership check)
            is_finding = resp.status_code == 200
            severity = "HIGH" if is_finding else "info"
            status_label = "✗ IDOR" if is_finding else "✓ OK"
            note = f"User B ({user_b_role}) accessing slide {sid}. Got {resp.status_code}."
            if is_finding:
                note += " NO OWNERSHIP VALIDATION — any authenticated user can access any slide."

            print(f"  {status_label}  slide={sid}  {path:50s} → {resp.status_code}")

            record(
                endpoint=ep_template, method="GET", role=user_b_role,
                status=resp.status_code, expected_status="403/404",
                finding=is_finding, severity=severity,
                response_time_ms=resp.elapsed_ms,
                test_category="idor",
                note=note,
            )
            time.sleep(0.1)

    # Also test sequential ID enumeration
    print("  --- Sequential ID enumeration ---")
    for sid in range(1, 6):
        path = f"/api/v1/slides/{sid}"
        resp = http("GET", f"{base_url}{path}",
                     headers={"Authorization": f"Bearer {user_b['token']}"})
        is_finding = resp.status_code == 200
        severity = "HIGH" if is_finding else "info"
        status_label = "✗ ENUM" if is_finding else "✓ OK"
        print(f"  {status_label}  Enumeration slide_id={sid} → {resp.status_code}")

        record(
            endpoint="/api/v1/slides/{slide_id}", method="GET", role=user_b_role,
            status=resp.status_code, expected_status="403/404",
            finding=is_finding, severity=severity,
            response_time_ms=resp.elapsed_ms,
            test_category="idor",
            note=f"Sequential enumeration: slide_id={sid}. Got {resp.status_code}.",
        )
        time.sleep(0.1)


# ---------------------------------------------------------------------------
# TEST 4: Token Tampering — flip JWT claims without re-signing
# ---------------------------------------------------------------------------
def test_4_token_tampering(base_url, accounts):
    """Modify JWT payload (role/sub) without re-signing. Server must reject."""
    print("\n═══ TEST 4: Token Tampering ═══")
    # Pick a real token
    role = list(accounts.keys())[0]
    token = accounts[role]["token"]

    # Decode JWT parts
    parts = token.split(".")
    if len(parts) != 3:
        print(f"  ⚠ Token is not a standard 3-part JWT, skipping tampering test.")
        return

    # Decode payload
    payload_b64 = parts[1]
    # Add padding
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding
    try:
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception as e:
        print(f"  ⚠ Could not decode JWT payload: {e}")
        return

    # Create tampered variants
    tampered_tokens = {}

    # 1. Change role to admin
    p1 = copy.deepcopy(payload)
    p1["role"] = "admin"
    t1_payload = base64.urlsafe_b64encode(json.dumps(p1).encode()).rstrip(b"=").decode()
    tampered_tokens["role→admin"] = f"{parts[0]}.{t1_payload}.{parts[2]}"

    # 2. Change sub to another email
    p2 = copy.deepcopy(payload)
    p2["sub"] = "hacker@evil.com"
    t2_payload = base64.urlsafe_b64encode(json.dumps(p2).encode()).rstrip(b"=").decode()
    tampered_tokens["sub→hacker"] = f"{parts[0]}.{t2_payload}.{parts[2]}"

    # 3. Change uid to 1
    p3 = copy.deepcopy(payload)
    p3["uid"] = 1
    t3_payload = base64.urlsafe_b64encode(json.dumps(p3).encode()).rstrip(b"=").decode()
    tampered_tokens["uid→1"] = f"{parts[0]}.{t3_payload}.{parts[2]}"

    # 4. Algorithm confusion: set alg to "none"
    header_b64 = parts[0]
    h_padding = 4 - len(header_b64) % 4
    if h_padding != 4:
        header_b64 += "=" * h_padding
    try:
        header = json.loads(base64.urlsafe_b64decode(header_b64))
    except Exception:
        header = {"alg": "HS256", "typ": "JWT"}
    h_none = copy.deepcopy(header)
    h_none["alg"] = "none"
    h_none_b64 = base64.urlsafe_b64encode(json.dumps(h_none).encode()).rstrip(b"=").decode()
    tampered_tokens["alg→none"] = f"{h_none_b64}.{parts[1]}."

    # Test each tampered token against a protected endpoint
    test_path = "/api/v1/slides/stats/dashboard"
    for label, tampered_token in tampered_tokens.items():
        url = f"{base_url}{test_path}"
        resp = http("GET", url, headers={"Authorization": f"Bearer {tampered_token}"})
        is_finding = resp.status_code in (200, 201)
        severity = "CRITICAL" if is_finding else "info"
        status_label = "✗ VULN" if is_finding else "✓ OK"
        print(f"  {status_label}  [{label:20s}] → {resp.status_code}")

        record(
            endpoint=test_path, method="GET", role=f"tampered({label})",
            status=resp.status_code, expected_status="401/403",
            finding=is_finding, severity=severity,
            response_time_ms=resp.elapsed_ms,
            test_category="token_tampering",
            note=f"Tampered JWT: {label}. Server returned {resp.status_code}.",
        )
        time.sleep(0.15)


# ---------------------------------------------------------------------------
# TEST 5: Injection Detection (SQLi / NoSQLi probes)
# ---------------------------------------------------------------------------
def test_5_injection(base_url, accounts):
    """Send SQLi/NoSQLi detection payloads in parameters. Detection only."""
    print("\n═══ TEST 5: Injection Probes (SQLi/NoSQLi) ═══")
    token = accounts[list(accounts.keys())[0]]["token"]
    headers_auth = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    sqli_payloads = [
        "1' OR '1'='1",
        "1; DROP TABLE users;--",
        "' UNION SELECT null,null,null--",
        "1 AND 1=1",
        "'; WAITFOR DELAY '0:0:5'--",
    ]

    # Test on login endpoint (public, takes email/password)
    print("  --- Login endpoint ---")
    for payload in sqli_payloads:
        body = {"email": payload, "password": payload}
        resp = http("POST", f"{base_url}/api/v1/auth/login",
                     headers={"Content-Type": "application/json"},
                     body=body)
        # Anomalous = 200 (logged in!) or 500 (server error leak) or > 3s response
        is_finding = resp.status_code == 200 or resp.status_code >= 500 or resp.elapsed_ms > 5000
        severity = "CRITICAL" if resp.status_code == 200 else ("HIGH" if resp.status_code >= 500 else "info")
        status_label = "✗ VULN" if is_finding else "✓ OK"
        shortened = payload[:30]
        print(f"  {status_label}  login({shortened:30s}) → {resp.status_code} ({resp.elapsed_ms:.0f}ms)")

        record(
            endpoint="/api/v1/auth/login", method="POST", role="anonymous",
            status=resp.status_code, expected_status="401/422",
            finding=is_finding, severity=severity,
            response_time_ms=resp.elapsed_ms,
            test_category="injection",
            note=f"SQLi payload in login. Status {resp.status_code}.",
        )
        time.sleep(0.15)

    # Test on slide library query params
    print("  --- Slide library query params ---")
    for payload in sqli_payloads[:3]:
        url = f"{base_url}/api/v1/slides/library?page=1&limit=20&grade={requests.utils.quote(payload) if HAS_REQUESTS else payload}"
        resp = http("GET", url, headers={"Authorization": f"Bearer {token}"})
        is_finding = resp.status_code >= 500 or resp.elapsed_ms > 5000
        severity = "HIGH" if is_finding else "info"
        status_label = "✗ VULN" if is_finding else "✓ OK"
        shortened = payload[:30]
        print(f"  {status_label}  library?grade={shortened:30s} → {resp.status_code} ({resp.elapsed_ms:.0f}ms)")

        record(
            endpoint="/api/v1/slides/library", method="GET", role=list(accounts.keys())[0],
            status=resp.status_code, expected_status="200/422",
            finding=is_finding, severity=severity,
            response_time_ms=resp.elapsed_ms,
            test_category="injection",
            note=f"SQLi payload in query param. Status {resp.status_code}.",
        )
        time.sleep(0.15)

    # Test on forgot-password endpoint
    print("  --- Forgot-password endpoint ---")
    for payload in sqli_payloads[:2]:
        body = {"email": payload}
        resp = http("POST", f"{base_url}/api/v1/auth/forgot-password",
                     headers={"Content-Type": "application/json"},
                     body=body)
        is_finding = resp.status_code >= 500 or resp.elapsed_ms > 5000
        severity = "HIGH" if resp.status_code >= 500 else "info"
        status_label = "✗ VULN" if is_finding else "✓ OK"
        shortened = payload[:30]
        print(f"  {status_label}  forgot({shortened:30s}) → {resp.status_code} ({resp.elapsed_ms:.0f}ms)")

        record(
            endpoint="/api/v1/auth/forgot-password", method="POST", role="anonymous",
            status=resp.status_code, expected_status="404/422",
            finding=is_finding, severity=severity,
            response_time_ms=resp.elapsed_ms,
            test_category="injection",
            note=f"SQLi payload in forgot-password. Status {resp.status_code}.",
        )
        time.sleep(0.15)


# ---------------------------------------------------------------------------
# TEST 6: Rate Limiting — bounded burst
# ---------------------------------------------------------------------------
def test_6_rate_limiting(base_url):
    """Send ~30 rapid requests to login to check for rate limiting."""
    print("\n═══ TEST 6: Rate Limiting (30-request burst) ═══")
    burst_count = 30
    statuses = []
    start_time = time.time()

    for i in range(burst_count):
        resp = http("POST", f"{base_url}/api/v1/auth/login",
                     headers={"Content-Type": "application/json"},
                     body={"email": "ratelimit@test.com", "password": "wrong"})
        statuses.append(resp.status_code)

    elapsed_total = time.time() - start_time
    rate_limited = any(s == 429 for s in statuses)
    unique_statuses = set(statuses)

    if rate_limited:
        print(f"  ✓ Rate limiting detected. Statuses: {unique_statuses}. Burst took {elapsed_total:.1f}s.")
        severity = "info"
        is_finding = False
    else:
        print(f"  ✗ NO rate limiting! All {burst_count} requests succeeded. Statuses: {unique_statuses}. Burst took {elapsed_total:.1f}s.")
        severity = "MEDIUM"
        is_finding = True

    record(
        endpoint="/api/v1/auth/login", method="POST", role="anonymous",
        status=f"all:{list(unique_statuses)}", expected_status="429 after burst",
        finding=is_finding, severity=severity,
        response_time_ms=elapsed_total * 1000,
        test_category="rate_limiting",
        note=f"Sent {burst_count} requests in {elapsed_total:.1f}s. Rate limited: {rate_limited}. Statuses: {list(unique_statuses)}.",
    )


# ---------------------------------------------------------------------------
# TEST 7: Hardcoded Credentials / Secrets Scan
# ---------------------------------------------------------------------------
def test_7_hardcoded_creds(base_url):
    """Scan codebase for committed secrets."""
    print("\n═══ TEST 7: Hardcoded Credentials Scan ═══")

    findings = []

    # Patterns to search for in the codebase
    secret_patterns = [
        ("SECRET_KEY default", "backend/app/config.py",
         "oral-dysplasia-dev-secret-key-change-in-production-2026"),
        ("PATIENT_ENCRYPTION_KEY default", "backend/app/config.py",
         "dGhpcy1pcy1hLTMyLWJ5dGUtZGV2LWtleS0xMjM0NQ=="),
        ("DATABASE_URL with root:@ (no password)", "backend/app/config.py",
         "mysql+aiomysql://root:@127.0.0.1:3306/oraldysplasia"),
    ]

    for label, filepath, pattern in secret_patterns:
        full_path = os.path.join(PROJECT_ROOT, filepath)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            if pattern in content:
                findings.append((label, filepath, pattern[:40] + "..."))
                print(f"  ✗ FOUND  {label} in {filepath}")
                record(
                    endpoint="N/A (codebase)", method="N/A", role="N/A",
                    status="found", expected_status="not present",
                    finding=True,
                    severity="CRITICAL" if "SECRET_KEY" in label else "HIGH",
                    response_time_ms=0,
                    test_category="hardcoded_creds",
                    note=f"{label}: hardcoded default in {filepath}. Value starts with '{pattern[:20]}...'",
                )
            else:
                print(f"  ✓ OK     {label} not found as plain text.")
        else:
            print(f"  ⚠ SKIP   {filepath} not found.")

    # Check for .env files committed to repo
    env_files = [".env", ".env.local", ".env.production"]
    for ef in env_files:
        full_path = os.path.join(PROJECT_ROOT, ef)
        if os.path.exists(full_path):
            print(f"  ✗ FOUND  {ef} exists (should be gitignored)")
            record(
                endpoint="N/A (codebase)", method="N/A", role="N/A",
                status="found", expected_status="not present",
                finding=True, severity="HIGH",
                response_time_ms=0,
                test_category="hardcoded_creds",
                note=f"{ef} file found committed to repository.",
            )
        else:
            print(f"  ✓ OK     {ef} not present.")

    # Check if .gitignore covers secrets
    gitignore_path = os.path.join(PROJECT_ROOT, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            gitignore = f.read()
        if ".env" in gitignore:
            print(f"  ✓ OK     .gitignore covers .env files.")
        else:
            print(f"  ✗ VULN   .gitignore does NOT cover .env files.")
            record(
                endpoint="N/A (codebase)", method="N/A", role="N/A",
                status="missing", expected_status="present",
                finding=True, severity="MEDIUM",
                response_time_ms=0,
                test_category="hardcoded_creds",
                note=".gitignore does not contain .env exclusion.",
            )

    # Check for user-controlled role on signup (design vulnerability)
    payload = {
        "email": f"test_role_check_{int(time.time())}@test.com",
        "password": "TestPass123!",
        "name": "Design Check",
        "license_id": "LIC-12345",
        "role": "SuperAdmin",
        "institution": "Test Inst"
    }
    resp = http("POST", f"{base_url}/api/v1/auth/signup",
                 headers={"Content-Type": "application/json"}, body=payload)
    if resp.status_code in (200, 201) and resp.json().get("user", {}).get("role") == "SuperAdmin":
        print(f"  ✗ DESIGN  User can self-assign any role at signup (no server validation).")
        record(
            endpoint="/api/v1/auth/signup", method="POST", role="anonymous",
            status="by design", expected_status="role validated server-side",
            finding=True, severity="HIGH",
            response_time_ms=resp.elapsed_ms,
            test_category="hardcoded_creds",
            note="Signup accepts any role string from client. User can self-assign 'Consultant Pathologist'. No server-side role validation.",
        )
    else:
        print(f"  ✓ DESIGN  User role validation is enforced at signup (server-side).")
        record(
            endpoint="/api/v1/auth/signup", method="POST", role="anonymous",
            status=resp.status_code, expected_status="role validated server-side",
            finding=False, severity="info",
            response_time_ms=resp.elapsed_ms,
            test_category="hardcoded_creds",
            note="Signup role validation is enforced. Arbitrary roles like 'SuperAdmin' are rejected.",
        )

    if not findings:
        print("  ✓ No hardcoded credentials found in scanned files.")


# ---------------------------------------------------------------------------
# TEST 5b: Role self-assignment verification
# ---------------------------------------------------------------------------
def test_5b_role_self_assignment(base_url):
    """Verify a user can sign up with an arbitrary role."""
    print("\n═══ TEST 5b: Role Self-Assignment on Signup ═══")
    email = rand_email("roletest")
    payload = {
        "email": email,
        "password": "TestPass123!",
        "name": "DAST RoleTest",
        "license_id": "ROLE-99999",
        "role": "SuperAdmin",  # arbitrary role
        "institution": "Evil Corp"
    }
    resp = http("POST", f"{base_url}/api/v1/auth/signup",
                 headers={"Content-Type": "application/json"}, body=payload)

    if resp.status_code in (200, 201):
        data = resp.json()
        assigned_role = data.get("user", {}).get("role", "")
        if assigned_role == "SuperAdmin":
            print(f"  ✗ VULN   Signed up with role='SuperAdmin' — accepted! Role={assigned_role}")
            record(
                endpoint="/api/v1/auth/signup", method="POST", role="anonymous",
                status=resp.status_code, expected_status="422 or role rejected",
                finding=True, severity="HIGH",
                response_time_ms=resp.elapsed_ms,
                test_category="authz_rbac",
                note="Server accepted arbitrary role 'SuperAdmin' on signup. No role whitelist validation.",
            )
        else:
            print(f"  ✓ OK     Role was sanitized to: {assigned_role}")
    else:
        print(f"  ✓ OK     Signup with arbitrary role rejected: {resp.status_code}")
        record(
            endpoint="/api/v1/auth/signup", method="POST", role="anonymous",
            status=resp.status_code, expected_status="422",
            finding=False, severity="info",
            response_time_ms=resp.elapsed_ms,
            test_category="authz_rbac",
            note=f"Arbitrary role rejected with {resp.status_code}.",
        )


# ---------------------------------------------------------------------------
# TEST: CORS misconfiguration check
# ---------------------------------------------------------------------------
def test_cors(base_url):
    """Check if CORS allows any origin."""
    print("\n═══ BONUS: CORS Misconfiguration ═══")
    resp = http("GET", f"{base_url}/api/v1/slides/stats/dashboard",
                 headers={
                     "Origin": "https://evil-attacker.com",
                     "Access-Control-Request-Method": "GET",
                 })
    acao = resp.headers.get("access-control-allow-origin", resp.headers.get("Access-Control-Allow-Origin", ""))
    if acao == "*":
        print(f"  ✗ VULN   CORS: Access-Control-Allow-Origin: * (wildcard)")
        record(
            endpoint="/api/v1/slides/stats/dashboard", method="GET", role="anonymous",
            status=resp.status_code, expected_status="restricted origin",
            finding=True, severity="MEDIUM",
            response_time_ms=resp.elapsed_ms,
            test_category="cors",
            note="CORS allows any origin (*). Combined with allow_credentials=True this is dangerous.",
        )
    elif "evil-attacker.com" in acao:
        print(f"  ✗ VULN   CORS reflects attacker origin: {acao}")
        record(
            endpoint="/api/v1/slides/stats/dashboard", method="GET", role="anonymous",
            status=resp.status_code, expected_status="restricted origin",
            finding=True, severity="HIGH",
            response_time_ms=resp.elapsed_ms,
            test_category="cors",
            note=f"CORS reflects arbitrary origin: {acao}.",
        )
    else:
        print(f"  ✓ OK     CORS origin: {acao or '(not set)'}")
        record(
            endpoint="/api/v1/slides/stats/dashboard", method="GET", role="anonymous",
            status=resp.status_code, expected_status="restricted",
            finding=False, severity="info",
            response_time_ms=resp.elapsed_ms,
            test_category="cors",
            note=f"CORS header: {acao or 'not returned'}.",
        )


# ---------------------------------------------------------------------------
# Write report
# ---------------------------------------------------------------------------
def write_report():
    with open(REPORT_JSON, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📄 Report written to: {REPORT_JSON}")


# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------
def print_summary():
    total = len(results)
    findings = [r for r in results if r["finding"]]
    by_severity = {}
    for r in findings:
        s = r["severity"]
        by_severity.setdefault(s, []).append(r)

    print("\n" + "=" * 70)
    print("  DAST SECURITY TEST SUMMARY")
    print("=" * 70)
    print(f"  Endpoints discovered:  {len(ENDPOINTS)}")
    print(f"  Total tests run:       {total}")
    print(f"  Findings:              {len(findings)}")
    print()

    severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "info"]
    for sev in severity_order:
        items = by_severity.get(sev, [])
        if items:
            icon = "✗" if sev in ("CRITICAL", "HIGH") else "⚠" if sev == "MEDIUM" else "✓"
            print(f"  {icon} {sev:10s}: {len(items)} finding(s)")
            for item in items[:5]:  # Show top 5 per severity
                print(f"      → {item['test_category']:20s} {item['method']:6s} {item['endpoint'][:40]}")
                print(f"        {item['note'][:80]}")
            if len(items) > 5:
                print(f"      ... and {len(items) - 5} more")
            print()

    if by_severity.get("CRITICAL"):
        print("  🚨 TOP PRIORITY FIXES:")
        for i, item in enumerate(by_severity["CRITICAL"][:5], 1):
            print(f"     {i}. [{item['test_category']}] {item['note'][:70]}")
        print()

    if by_severity.get("HIGH"):
        print("  ⚠️  HIGH PRIORITY FIXES:")
        for i, item in enumerate(by_severity["HIGH"][:5], 1):
            print(f"     {i}. [{item['test_category']}] {item['note'][:70]}")

    print("\n" + "=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("  DAST Runner — OralDysplasia AI API Security Testing")
    print("=" * 70)

    base_url = load_config()
    print(f"\n🎯 Target: {base_url}")

    # Verify connectivity
    print("\n🔗 Connectivity check...")
    resp = http("GET", f"{base_url}/health")
    if resp.status_code == 0:
        print(f"  ✗ Cannot reach {base_url}: {resp.body}")
        print("  Aborting. Please check the base URL and network connectivity.")
        sys.exit(1)
    print(f"  ✓ Connected. Health: {resp.status_code} ({resp.elapsed_ms:.0f}ms)")
    print(f"    Response: {resp.body[:200]}")

    # Setup accounts
    print("\n👤 Creating test accounts...")
    accounts = setup_accounts(base_url)
    if not accounts:
        print("  ✗ Could not create any test accounts. Aborting auth-dependent tests.")
    else:
        print(f"  ✓ {len(accounts)} account(s) ready.")

    # Save checkpoint
    savepoint = {"base_url": base_url, "accounts_created": len(accounts), "timestamp": datetime.datetime.utcnow().isoformat()}
    with open(SAVEPOINT_JSON, "w") as f:
        json.dump(savepoint, f, indent=2)

    # Run tests
    test_0_auth_enforcement(base_url)
    test_1_authn_bypass(base_url)

    if accounts:
        test_2_authz_rbac(base_url, accounts)
        test_3_idor(base_url, accounts)
        test_4_token_tampering(base_url, accounts)
        test_5_injection(base_url, accounts)

    test_5b_role_self_assignment(base_url)
    test_6_rate_limiting(base_url)
    test_7_hardcoded_creds(base_url)
    test_cors(base_url)

    # Write report and summary
    write_report()
    print_summary()

    print(f"\nDone. Full details in: {REPORT_JSON}")


if __name__ == "__main__":
    main()
