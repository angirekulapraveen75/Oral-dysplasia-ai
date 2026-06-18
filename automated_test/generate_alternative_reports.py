import json
import os
import csv
import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_JSON = os.path.join(SCRIPT_DIR, "report.json")
HTML_OUTPUT = os.path.join(SCRIPT_DIR, "DAST_Security_Report.html")
FINDINGS_CSV = os.path.join(SCRIPT_DIR, "DAST_Security_Findings.csv")
ALL_RESULTS_CSV = os.path.join(SCRIPT_DIR, "DAST_All_Test_Results.csv")

# Load report data
with open(REPORT_JSON, "r") as f:
    results = json.load(f)

findings = [r for r in results if r.get("finding")]
total_tests = len(results)
total_findings = len(findings)

critical_count = len([f for f in findings if f["severity"].upper() == "CRITICAL"])
high_count = len([f for f in findings if f["severity"].upper() == "HIGH"])
medium_count = len([f for f in findings if f["severity"].upper() == "MEDIUM"])
low_count = len([f for f in findings if f["severity"].upper() == "LOW"])
info_count = len([f for f in findings if f["severity"].upper() == "INFO"])

# ── Generate CSVs ───────────────────────────────────────────────────

# 1. Findings CSV
with open(FINDINGS_CSV, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Index", "Severity", "Category", "Endpoint", "Method", "Role Context", "Description"])
    for i, r in enumerate(findings, 1):
        writer.writerow([
            i,
            r.get("severity", "").upper(),
            r.get("test_category", "").replace("_", " ").title(),
            r.get("endpoint", ""),
            r.get("method", ""),
            r.get("role", ""),
            r.get("note", "")
        ])

# 2. All Test Results CSV
with open(ALL_RESULTS_CSV, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Index", "Endpoint", "Method", "Role Context", "Response Status", "Expected Status", "Is Finding?", "Severity", "Response Time (ms)", "Note"])
    for i, r in enumerate(results, 1):
        writer.writerow([
            i,
            r.get("endpoint", ""),
            r.get("method", ""),
            r.get("role", ""),
            r.get("status", ""),
            r.get("expected_status", ""),
            "YES" if r.get("finding") else "NO",
            r.get("severity", "").upper() if r.get("finding") else "info",
            r.get("response_time_ms", 0),
            r.get("note", "")
        ])

# ── Generate HTML Report ────────────────────────────────────────────

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DAST Security Report - OralDysplasia AI</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #2D336B;
            --primary-dark: #1B1F3B;
            --bg: #F8F9FA;
            --card-bg: #FFFFFF;
            --text-main: #333333;
            --text-muted: #666666;
            --border: #E5E7EB;
            
            --critical: #DC2626;
            --high: #EA580C;
            --medium: #EAB308;
            --low: #2563EB;
            --pass: #16A34A;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        
        body {{
            background-color: var(--bg);
            color: var(--text-main);
            padding: 40px 20px;
            line-height: 1.5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            background: linear-gradient(135deg, var(--primary-dark), var(--primary));
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }}
        
        header h1 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 5px;
        }}
        
        header p {{
            font-size: 14px;
            opacity: 0.85;
            margin-top: 5px;
        }}
        
        .grid-kpis {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .kpi-card {{
            background: var(--card-bg);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid var(--border);
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .kpi-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}
        
        .kpi-value {{
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 5px;
        }}
        
        .kpi-label {{
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--text-muted);
            letter-spacing: 0.5px;
        }}
        
        .tabs-header {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid var(--border);
            padding-bottom: 10px;
        }}
        
        .tab-btn {{
            background: none;
            border: none;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
            color: var(--text-muted);
            cursor: pointer;
            border-radius: 6px;
            transition: all 0.2s;
        }}
        
        .tab-btn:hover {{
            color: var(--primary);
            background-color: rgba(45, 51, 107, 0.05);
        }}
        
        .tab-btn.active {{
            color: white;
            background-color: var(--primary);
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        
        .card h2 {{
            font-size: 20px;
            margin-bottom: 20px;
            color: var(--primary-dark);
            border-left: 4px solid var(--primary);
            padding-left: 10px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 14px;
            text-align: left;
        }}
        
        th {{
            background-color: #F3F4F6;
            color: var(--text-main);
            font-weight: 600;
            padding: 12px 16px;
            border-bottom: 2px solid var(--border);
        }}
        
        td {{
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            vertical-align: middle;
        }}
        
        tr:hover td {{
            background-color: #F9FAFB;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            color: white;
        }}
        
        .badge.critical {{ background-color: var(--critical); }}
        .badge.high {{ background-color: var(--high); }}
        .badge.medium {{ background-color: var(--medium); }}
        .badge.low {{ background-color: var(--low); }}
        .badge.pass {{ background-color: var(--pass); }}
        .badge.fail {{ background-color: var(--critical); }}
        
        .finding-card {{
            border-left: 5px solid var(--border);
            margin-bottom: 20px;
            padding-left: 20px;
        }}
        
        .finding-card.critical {{ border-left-color: var(--critical); }}
        .finding-card.high {{ border-left-color: var(--high); }}
        .finding-card.medium {{ border-left-color: var(--medium); }}
        
        .finding-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 5px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .finding-meta {{
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 10px;
        }}
        
        .finding-desc {{
            font-size: 14px;
            color: #444;
            background: #F9FAFB;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #F3F4F6;
        }}
        
        .remediation-box {{
            background-color: #EFF6FF;
            border: 1px solid #BFDBFE;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            font-size: 14px;
        }}
        
        .remediation-box h4 {{
            color: #1E40AF;
            margin-bottom: 5px;
            font-weight: 600;
        }}
        
        /* Search styling */
        .search-bar {{
            width: 100%;
            padding: 10px 15px;
            font-size: 14px;
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 20px;
            outline: none;
        }}
        .search-bar:focus {{
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(45, 51, 107, 0.15);
        }}
        
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }}
        
        .meta-item {{
            font-size: 14px;
        }}
        .meta-item strong {{
            color: var(--primary-dark);
        }}
    </style>
</head>
<body>

<div class="container">
    <header>
        <h1>DAST Security Assessment Report</h1>
        <p>OralDysplasia AI — API Security Performance Analysis</p>
        <p>Target Deployment: <strong>https://oral-dysplasia-ai.vercel.app</strong> | Run Date: {datetime.date.today().strftime('%d %B %Y')}</p>
    </header>

    <div class="grid-kpis">
        <div class="kpi-card">
            <div class="kpi-value" style="color: var(--primary);">{total_tests}</div>
            <div class="kpi-label">Total Tests Run</div>
        </div>
        <div class="kpi-card" style="background-color: {'#FFF5F5' if total_findings > 0 else '#F0FDF4'}; border-color: {'#FEB2B2' if total_findings > 0 else '#BBF7D0'};">
            <div class="kpi-value" style="color: {'var(--critical)' if total_findings > 0 else 'var(--pass)'};">{total_findings}</div>
            <div class="kpi-label" style="color: {'var(--critical)' if total_findings > 0 else 'var(--pass)'};">Security Findings</div>
        </div>
        <div class="kpi-card" style="background-color: var(--critical); color: white;">
            <div class="kpi-value" style="color: white;">{critical_count}</div>
            <div class="kpi-label" style="color: white; opacity: 0.9;">Critical</div>
        </div>
        <div class="kpi-card" style="background-color: var(--high); color: white;">
            <div class="kpi-value" style="color: white;">{high_count}</div>
            <div class="kpi-label" style="color: white; opacity: 0.9;">High</div>
        </div>
        <div class="kpi-card" style="background-color: var(--medium); color: white;">
            <div class="kpi-value" style="color: white;">{medium_count}</div>
            <div class="kpi-label" style="color: white; opacity: 0.9;">Medium</div>
        </div>
    </div>

    <div class="tabs-header">
        <button class="tab-btn active" onclick="switchTab('summary')">Executive Summary</button>
        <button class="tab-btn" onclick="switchTab('findings')">Detailed Findings ({total_findings})</button>
        <button class="tab-btn" onclick="switchTab('results')">All Tests ({total_tests})</button>
        <button class="tab-btn" onclick="switchTab('endpoints')">Endpoints Catalog</button>
    </div>

    <!-- TAB 1: EXECUTIVE SUMMARY -->
    <div id="tab-summary" class="tab-content active">
        <div class="card">
            <h2>Overview & Scope</h2>
            <p>This report documents the results of a Dynamic Application Security Testing (DAST) pass performed against the deployed FastAPI backend. The test suite automatically validated access control boundaries, rate limits, CORS configurations, JWT verification, and injection safety across all exposed routes.</p>
            
            <div class="meta-grid">
                <div class="meta-item"><strong>Target URL:</strong> <a href="https://oral-dysplasia-ai.vercel.app" target="_blank">https://oral-dysplasia-ai.vercel.app</a></div>
                <div class="meta-item"><strong>Authentication:</strong> JWT (Bearer tokens)</div>
                <div class="meta-item"><strong>Endpoints Tested:</strong> 13</div>
                <div class="meta-item"><strong>Test Date:</strong> {datetime.date.today().strftime('%Y-%m-%d')}</div>
            </div>
        </div>
        
        <div class="card">
            <h2>Summary of Results by Test Category</h2>
            <table>
                <thead>
                    <tr>
                        <th>Test Category</th>
                        <th style="text-align: center;">Tests Run</th>
                        <th style="text-align: center;">Passed</th>
                        <th style="text-align: center;">Findings Detected</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""

# Re-tally by category for the HTML summary table
cat_tallies = {}
for r in results:
    cat = r["test_category"]
    cat_tallies.setdefault(cat, {"total": 0, "findings": 0})
    cat_tallies[cat]["total"] += 1
    if r.get("finding"):
        cat_tallies[cat]["findings"] += 1

for cat_key, stats in cat_tallies.items():
    display = cat_key.replace("_", " ").title()
    t = stats["total"]
    f = stats["findings"]
    p = t - f
    status_badge = f'<span class="badge pass">PASS</span>' if f == 0 else f'<span class="badge fail">{f} FAIL</span>'
    html_template += f"""
                    <tr>
                        <td><strong>{display}</strong></td>
                        <td style="text-align: center;">{t}</td>
                        <td style="text-align: center;">{p}</td>
                        <td style="text-align: center; font-weight: bold; color: {'var(--critical)' if f > 0 else 'inherit'};">{f}</td>
                        <td>{status_badge}</td>
                    </tr>"""

html_template += f"""
                </tbody>
            </table>
        </div>
    </div>

    <!-- TAB 2: DETAILED FINDINGS -->
    <div id="tab-findings" class="tab-content">
        <div class="card">
            <h2>Security Findings ({total_findings})</h2>
"""

if not findings:
    html_template += "<p style='color: var(--pass); font-weight: 600;'>No security vulnerabilities were detected! All checks passed.</p>"
else:
    # Sort findings Critical -> High -> Medium
    sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    sorted_findings = sorted(findings, key=lambda x: sev_order.get(x["severity"].upper(), 5))
    
    for i, f in enumerate(sorted_findings, 1):
        sev_upper = f["severity"].upper()
        sev_class = sev_upper.lower()
        
        # Determine recommendations
        rec = ""
        if "SECRET_KEY" in f.get("note", "") or "F1" in f.get("note", "") or "config.py" in f.get("endpoint", ""):
            rec = "Remove the hardcoded default SECRET_KEY in config.py. Retrieve it exclusively from environment variables (e.g. <code>os.environ.get('SECRET_KEY')</code>). Add a startup validation check that prevents the application from booting if this environment variable is missing or insecure."
        elif "Encryption" in f.get("note", "") or "encryption" in f.get("note", ""):
            rec = "Move patient PII cryptography keys (Fernet) to an environment variable. Never check raw symmetric keys into git repositories. Set up automatic key rotation policies."
        elif "DB" in f.get("note", "") or "mysql" in f.get("note", ""):
            rec = "Remove passwordless MySQL defaults. Configure all database credentials via an encrypted secrets manager or environment variables (e.g. <code>DATABASE_URL</code>)."
        elif "signup" in f.get("endpoint", "") or "role" in f.get("note", "").lower():
            rec = "Restrict role self-assignment on registration. Do not accept arbitrary 'role' strings in signup endpoints. Enforce a strict whitelist of roles (e.g., Resident, Consultant Pathologist, Lab Tech) or assign a standard default role like 'Resident' to all signups."
        elif "RBAC" in f.get("note", "") or "roles" in f.get("note", "").lower():
            rec = "Implement Role-Based Access Control (RBAC) in FastAPI using helper dependencies (e.g. checking <code>user.role in allowed_roles</code>). Decorate clinical actions (running analysis, submitting review, exporting reports) to deny unauthorized roles like Lab Tech."
        elif "Rate Limit" in f.get("note", "") or "rate_limiting" in f.get("test_category", ""):
            rec = "Add rate-limiting middleware (like <code>slowapi</code>) to sensitive endpoints. Set limits of 5 login attempts per minute per IP address, and general API limits of 60 requests per minute."
        elif "CORS" in f.get("note", "") or "cors" in f.get("test_category", ""):
            rec = "Specify explicit, trusted domains in the <code>allow_origins</code> parameter of FastAPI CORSMiddleware. Do not use wildcard origins (<code>*</code>) while <code>allow_credentials=True</code> is enabled."
        else:
            rec = "Review the endpoint logic to validate input bounds, check object ownership, and enforce authorization policies."

        html_template += f"""
            <div class="finding-card {sev_class}">
                <div class="finding-title">
                    <span class="badge {sev_class}">{sev_upper}</span>
                    <strong>{f.get('test_category', '').replace('_', ' ').title()} Vulnerability</strong>
                </div>
                <div class="finding-meta">
                    <strong>Endpoint:</strong> <code>{f.get('method', '')} {f.get('endpoint', '')}</code> | 
                    <strong>Tested Role:</strong> <code>{f.get('role', 'N/A')}</code>
                </div>
                <div class="finding-desc">
                    {f.get('note', '')}
                </div>
                <div class="remediation-box">
                    <h4>Remediation Action:</h4>
                    <p>{rec}</p>
                </div>
            </div>
            <hr style="margin: 20px 0; border: 0; border-top: 1px solid var(--border);">
        """

html_template += """
        </div>
    </div>

    <!-- TAB 3: ALL TEST RESULTS -->
    <div id="tab-results" class="tab-content">
        <div class="card">
            <h2>Complete Verification Ledger</h2>
            <p style="margin-bottom: 15px; font-size: 14px; color: var(--text-muted);">This ledger contains details of all 99 dynamic tests executed during the scan.</p>
            
            <input type="text" id="searchInput" class="search-bar" placeholder="Search tests by endpoint, category, status, or notes..." onkeyup="filterTests()">
            
            <table id="resultsTable">
                <thead>
                    <tr>
                        <th style="width: 50px; text-align: center;">#</th>
                        <th>Category</th>
                        <th>Endpoint</th>
                        <th style="text-align: center;">Method</th>
                        <th style="text-align: center;">Status</th>
                        <th style="text-align: center;">Expected</th>
                        <th style="text-align: center;">Finding?</th>
                        <th style="text-align: center;">Resp (ms)</th>
                    </tr>
                </thead>
                <tbody>
"""

for i, r in enumerate(results, 1):
    is_finding = r.get("finding", False)
    badge = '<span class="badge fail">YES</span>' if is_finding else '<span class="badge pass">NO</span>'
    html_template += f"""
                    <tr class="test-row">
                        <td style="text-align: center; color: var(--text-muted);">{i}</td>
                        <td>{r.get('test_category', '').replace('_', ' ').title()}</td>
                        <td><code>{r.get('endpoint', '')}</code></td>
                        <td style="text-align: center;"><code>{r.get('method', '')}</code></td>
                        <td style="text-align: center;">{r.get('status', '')}</td>
                        <td style="text-align: center;">{r.get('expected_status', '')}</td>
                        <td style="text-align: center;">{badge}</td>
                        <td style="text-align: center; color: var(--text-muted);">{r.get('response_time_ms', 0)}ms</td>
                    </tr>"""

html_template += """
                </tbody>
            </table>
        </div>
    </div>

    <!-- TAB 4: ENDPOINTS CATALOG -->
    <div id="tab-endpoints" class="tab-content">
        <div class="card">
            <h2>Endpoints Catalog</h2>
            <p style="margin-bottom: 15px; font-size: 14px; color: var(--text-muted);">The 13 backend endpoints audited during endpoint discovery:</p>
            <table>
                <thead>
                    <tr>
                        <th style="width: 50px; text-align: center;">#</th>
                        <th style="text-align: center;">Method</th>
                        <th>Path</th>
                        <th style="text-align: center;">Auth Type</th>
                        <th style="text-align: center;">RBAC Protection</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="text-align: center;">1</td>
                        <td style="text-align: center;"><strong>POST</strong></td>
                        <td><code>/api/v1/auth/signup</code></td>
                        <td style="text-align: center;">Public</td>
                        <td style="text-align: center; color: var(--critical); font-weight: 600;">None (Self-Assign)</td>
                        <td>User registration endpoint</td>
                    </tr>
                    <tr>
                        <td style="text-align: center;">2</td>
                        <td style="text-align: center;"><strong>POST</strong></td>
                        <td><code>/api/v1/auth/login</code></td>
                        <td style="text-align: center;">Public</td>
                        <td style="text-align: center;">None</td>
                        <td>User authentication / JWT issues</td>
                    </tr>
                    <tr>
                        <td style="text-align: center;">3</td>
                        <td style="text-align: center;"><strong>POST</strong></td>
                        <td><code>/api/v1/auth/forgot-password</code></td>
                        <td style="text-align: center;">Public</td>
                        <td style="text-align: center;">None</td>
                        <td>Password recovery verification</td>
                    </tr>
                    <tr>
                        <td style="text-align: center;">4</td>
                        <td style="text-align: center;"><strong>POST</strong></td>
                        <td><code>/api/v1/slides/upload</code></td>
                        <td style="text-align: center; color: var(--low); font-weight: 600;">JWT Req.</td>
                        <td style="text-align: center; color: var(--critical); font-weight: 600;">None</td>
                        <td>Pathology slide image upload</td>
                    </tr>
                    <tr>
                        <td style="text-align: center;">5</td>
                        <td style="text-align: center;"><strong>GET</strong></td>
                        <td><code>/api/v1/slides/library</code></td>
                        <td style="text-align: center; color: var(--low); font-weight: 600;">JWT Req.</td>
                        <td style="text-align: center;">None</td>
                        <td>Paginated slide gallery view</td>
                    </tr>
                    <tr>
                        <td style="text-align: center;">6</td>
                        <td style="text-align: center;"><strong>GET</strong></td>
                        <td><code>/api/v1/slides/{slide_id}</code></td>
                        <td style="text-align: center; color: var(--low); font-weight: 600;">JWT Req.</td>
                        <td style="text-align: center; color: var(--high); font-weight: 600;">IDOR Risk</td>
                        <td>Single slide detail information</td>
                    </tr>
                    <tr>
                        <td style="text-align: center;">7</td>
                        <td style="text-align: center;"><strong>GET</strong></td>
                        <td><code>/api/v1/slides/stats/dashboard</code></td>
                        <td style="text-align: center; color: var(--low); font-weight: 600;">JWT Req.</td>
                        <td style="text-align: center;">None</td>
                        <td>Diagnostic database aggregations</td>
                    </tr>
                    <tr>
                        <td style="text-align: center;">8</td>
                        <td style="text-align: center;"><strong>POST</strong></td>
                        <td><code>/api/v1/analysis/run</code></td>
                        <td style="text-align: center; color: var(--low); font-weight: 600;">JWT Req.</td>
                        <td style="text-align: center; color: var(--critical); font-weight: 600;">None</td>
                        <td>Trigger AI model segmentation</td>
                    </tr>
                    <tr>
                        <td style="text-align: center;">9</td>
                        <td style="text-align: center;"><strong>GET</strong></td>
                        <td><code>/api/v1/analysis/{slide_id}/result</code></td>
                        <td style="text-align: center; color: var(--low); font-weight: 600;">JWT Req.</td>
                        <td style="text-align: center; color: var(--high); font-weight: 600;">IDOR Risk</td>
                        <td>Fetch model output files and labels</td>
                    </tr>
                    <tr>
                        <td style="text-align: center;">10</td>
                        <td style="text-align: center;"><strong>PUT</strong></td>
                        <td><code>/api/v1/analysis/{slide_id}/review</code></td>
                        <td style="text-align: center; color: var(--low); font-weight: 600;">JWT Req.</td>
                        <td style="text-align: center; color: var(--critical); font-weight: 600;">None</td>
                        <td>Pathologist verification input</td>
                    </tr>
                    <tr>
                        <td style="text-align: center;">11</td>
                        <td style="text-align: center;"><strong>GET</strong></td>
                        <td><code>/api/v1/reports/{slide_id}/export</code></td>
                        <td style="text-align: center; color: var(--low); font-weight: 600;">JWT Req.</td>
                        <td style="text-align: center; color: var(--critical); font-weight: 600;">None</td>
                        <td>PDF export builder</td>
                    </tr>
                    <tr>
                        <td style="text-align: center;">12</td>
                        <td style="text-align: center;"><strong>GET</strong></td>
                        <td><code>/openapi.json</code></td>
                        <td style="text-align: center;">Public</td>
                        <td style="text-align: center;">None</td>
                        <td>Auto-generated OpenAPI spec</td>
                    </tr>
                    <tr>
                        <td style="text-align: center;">13</td>
                        <td style="text-align: center;"><strong>GET</strong></td>
                        <td><code>/docs</code></td>
                        <td style="text-align: center;">Public</td>
                        <td style="text-align: center;">None</td>
                        <td>Interactive Swagger UI docs</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<script>
function switchTab(tabId) {{
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    event.currentTarget.classList.add('active');
    document.getElementById('tab-' + tabId).classList.add('active');
}}

function filterTests() {{
    const query = document.getElementById('searchInput').value.toLowerCase();
    const rows = document.querySelectorAll('.test-row');
    
    rows.forEach(row => {{
        const text = row.textContent.toLowerCase();
        if(text.includes(query)) {{
            row.style.display = '';
        }} else {{
            row.style.display = 'none';
        }}
    }});
}}
</script>

</body>
</html>
"""

with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"Alternative reports generated:")
print(f" - HTML Format (Open in any Browser): {HTML_OUTPUT}")
print(f" - Findings CSV (Open in Excel/Google Sheets): {FINDINGS_CSV}")
print(f" - All Results CSV (Open in Excel/Google Sheets): {ALL_RESULTS_CSV}")
