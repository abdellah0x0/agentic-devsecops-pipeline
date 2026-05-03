"""
Dashboard generator - Transforms exploit-gate JSON report into a static HTML dashboard.
Output is published to GitHub Pages.
"""
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Exploit Gate - {repo}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f0;
            color: #2c2c2a;
            padding: 2rem 1rem;
            min-height: 100vh;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        .header {{
            background: white;
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            border: 1px solid #e0e0d8;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        .header-left h1 {{ font-size: 28px; margin-bottom: 8px; }}
        .header-left p {{ color: #888780; font-size: 14px; }}
        .meta-pill {{
            display: inline-block;
            background: #f5f5f0;
            padding: 4px 10px;
            border-radius: 4px;
            font-family: 'SF Mono', Consolas, monospace;
            font-size: 12px;
            margin-right: 4px;
        }}
        .fix-all-btn {{
            background: #1D9E75;
            color: white;
            border: none;
            padding: 14px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 15px;
            font-weight: 600;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: background 0.2s;
        }}
        .fix-all-btn:hover {{ background: #0F6E56; }}
        .fix-all-btn:disabled {{ background: #888780; cursor: not-allowed; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        .stat-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            border: 1px solid #e0e0d8;
        }}
        .stat-num {{ font-size: 36px; font-weight: 600; line-height: 1; }}
        .stat-label {{ color: #888780; font-size: 13px; margin-top: 8px; text-transform: uppercase; letter-spacing: 0.05em; }}
        .findings-section h2 {{
            font-size: 20px;
            margin-bottom: 1rem;
            padding-left: 4px;
        }}
        .finding-card {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border: 1px solid #e0e0d8;
        }}
        .finding-card.exploited {{
            border-left: 4px solid #E24B4A;
        }}
        .finding-card.safe {{
            border-left: 4px solid #1D9E75;
            opacity: 0.7;
        }}
        .finding-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }}
        .severity {{
            padding: 4px 10px;
            border-radius: 4px;
            color: white;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .severity.BLOCKER {{ background: #E24B4A; }}
        .severity.CRITICAL {{ background: #D85A30; }}
        .severity.MAJOR {{ background: #EF9F27; }}
        .severity.MINOR {{ background: #888780; }}
        h3 {{ font-size: 17px; flex: 1; }}
        .status-badge {{
            font-weight: 600;
            font-size: 13px;
            padding: 4px 10px;
            border-radius: 4px;
        }}
        .status-badge.exploited {{ background: #FBE5E4; color: #B23938; }}
        .status-badge.safe {{ background: #E6F4EE; color: #0F6E56; }}
        .finding-body p {{ margin-bottom: 8px; line-height: 1.5; font-size: 14px; }}
        .finding-body strong {{ color: #2c2c2a; }}
        pre {{
            background: #2c2c2a;
            color: #f5f5f0;
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
            font-family: 'SF Mono', Consolas, monospace;
            font-size: 12px;
            margin: 8px 0;
            line-height: 1.4;
        }}
        code {{
            background: #f5f5f0;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'SF Mono', Consolas, monospace;
            font-size: 13px;
            color: #B23938;
        }}
        .empty-state {{
            text-align: center;
            padding: 4rem 2rem;
            color: #888780;
        }}
        .empty-state h2 {{ color: #2c2c2a; margin-bottom: 8px; }}
        .footer {{
            text-align: center;
            color: #888780;
            font-size: 13px;
            margin-top: 2rem;
            padding: 1rem;
        }}
        .footer a {{ color: #1D9E75; }}
        @media (max-width: 600px) {{
            .header {{ flex-direction: column; }}
            .fix-all-btn {{ width: 100%; justify-content: center; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-left">
                <h1>🛡️ AI Exploit Gate Report</h1>
                <p>
                    <span class="meta-pill">{repo}</span>
                    <span class="meta-pill">{commit_short}</span>
                    <span class="meta-pill">{generated_at}</span>
                </p>
            </div>
            {fix_button}
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-num">{total_findings}</div>
                <div class="stat-label">Total Findings</div>
            </div>
            <div class="stat-card">
                <div class="stat-num" style="color: #E24B4A">{exploited_count}</div>
                <div class="stat-label">Exploited</div>
            </div>
            <div class="stat-card">
                <div class="stat-num" style="color: #888780">{false_positive_count}</div>
                <div class="stat-label">False Positives</div>
            </div>
            <div class="stat-card">
                <div class="stat-num" style="color: #1D9E75">{exploit_rate}%</div>
                <div class="stat-label">Exploit Rate</div>
            </div>
        </div>
        
        <div class="findings-section">
            <h2>Findings Detail</h2>
            {findings_html}
        </div>
        
        <div class="footer">
            <p>Generated by <strong>Claude Sonnet 4.6</strong> via Agent SDK · 
            <a href="https://github.com/{repo}" target="_blank">View on GitHub</a></p>
        </div>
    </div>
</body>
</html>
"""


def render_finding(f):
    """Render a single finding card."""
    exploited = f.get("exploited", False)
    severity = f.get("severity", "MAJOR")
    
    status_class = "exploited" if exploited else "safe"
    status_text = "🔴 EXPLOITED" if exploited else "✅ NOT EXPLOITED"
    
    payload = f.get("payload", "N/A")
    if isinstance(payload, str) and len(payload) > 200:
        payload = payload[:200] + "..."
    
    reproduction = f.get("reproduction_steps", [])
    reproduction_html = ""
    if reproduction:
        steps = "\n".join(f"  {i+1}. {step}" for i, step in enumerate(reproduction))
        reproduction_html = f"""
        <p><strong>Reproduction:</strong></p>
        <pre>{escape_html(steps)}</pre>
        """
    
    return f"""
    <div class="finding-card {status_class}">
        <div class="finding-header">
            <span class="severity {severity}">{severity}</span>
            <h3>{escape_html(f.get('vulnerability_type', 'Unknown'))}</h3>
            <span class="status-badge {status_class}">{status_text}</span>
        </div>
        <div class="finding-body">
            <p><strong>Endpoint:</strong> <code>{escape_html(f.get('endpoint', 'N/A'))}</code></p>
            <p><strong>File:</strong> <code>{escape_html(f.get('file', 'N/A'))}:{f.get('sink_line', '?')}</code></p>
            <p><strong>Rule:</strong> <code>{escape_html(f.get('rule_id', 'N/A'))}</code> · <strong>CWE:</strong> {escape_html(f.get('cwe', 'N/A'))}</p>
            <p><strong>Payload that worked:</strong></p>
            <pre>{escape_html(str(payload))}</pre>
            <p><strong>Evidence:</strong> {escape_html(f.get('evidence', 'N/A'))}</p>
            <p><strong>Impact:</strong> {escape_html(f.get('impact', 'N/A'))}</p>
            {reproduction_html}
        </div>
    </div>
    """


def escape_html(text):
    """Basic HTML escaping."""
    if text is None:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def generate_html(report, repo, commit):
    """Generate the full dashboard HTML."""
    findings = report.get("findings", [])
    summary = report.get("summary", {})
    
    total = summary.get("total_findings", 0)
    exploited = summary.get("exploited_count", 0)
    fp = summary.get("false_positive_count", 0)
    exploit_rate = round(exploited / max(total, 1) * 100) if total > 0 else 0
    
    # Empty state if no findings
    if not findings:
        findings_html = """
        <div class="empty-state">
            <h2>No vulnerabilities found</h2>
            <p>SonarCloud scan completed without flagging any security issues.</p>
        </div>
        """
        fix_button = ""
    else:
        findings_html = "".join(render_finding(f) for f in findings)
        # Build URL to create issue with auto-fix label
        issue_title = f"Auto-fix all {exploited} exploitable vulnerabilities"
        issue_body = (
            f"**Commit:** {commit[:7]}\n\n"
            f"**Vulnerabilities to fix:** {exploited}\n\n"
            f"This issue was created from the AI Exploit Gate dashboard.\n"
            f"The AI Fix Agent will be triggered automatically by the `auto-fix` label."
        )
        from urllib.parse import quote
        issue_url = (
            f"https://github.com/{repo}/issues/new?"
            f"title={quote(issue_title)}"
            f"&body={quote(issue_body)}"
            f"&labels=auto-fix,security"
        )
        fix_button = f"""
        <a href="{issue_url}" target="_blank" class="fix-all-btn">
            Generate AI Fix for All Vulnerabilities
        </a>
        """
    
    html = HTML_TEMPLATE.format(
        repo=repo,
        commit_short=commit[:7],
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        total_findings=total,
        exploited_count=exploited,
        false_positive_count=fp,
        exploit_rate=exploit_rate,
        findings_html=findings_html,
        fix_button=fix_button,
    )
    return html


def main():
    parser = argparse.ArgumentParser(description="Generate dashboard HTML from exploit report")
    parser.add_argument("--report", required=True, help="Path to report.json")
    parser.add_argument("--output", required=True, help="Output HTML file path")
    parser.add_argument("--repo", required=True, help="GitHub repo (owner/name)")
    parser.add_argument("--commit", required=True, help="Commit SHA")
    args = parser.parse_args()
    
    report_path = Path(args.report)
    if not report_path.exists():
        print(f"Report not found at {report_path}, generating empty dashboard")
        report = {"summary": {}, "findings": []}
    else:
        with open(report_path) as f:
            report = json.load(f)
    
    html = generate_html(report, args.repo, args.commit)
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)
    
    print(f"Dashboard written to {output_path}")
    print(f"Findings: {len(report.get('findings', []))}")


if __name__ == "__main__":
    main()