"""
AI Fix Agent - Generates secure fixes for ALL SonarCloud vulnerabilities.
Uses the OWASP security skill for best practices.
"""
import asyncio
import os
from pathlib import Path
from claude_agent_sdk import query, ClaudeAgentOptions


async def main():
    issue_number = os.getenv("ISSUE_NUMBER", "0")
    output_dir = Path(os.getenv("OUTPUT_DIR", "./fix-output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.md"
    
    print(f"Starting AI Fix Agent for issue #{issue_number}")
    print(f"Summary will be written to {summary_path}")
    print("=" * 60)
    
    options = ClaudeAgentOptions(
        system_prompt=(
            "You are a security code-fixing agent. Your mission is to:\n"
            "1. Fetch ALL vulnerable findings from SonarCloud\n"
            "2. For EACH finding, apply a secure fix using the Edit tool\n"
            "3. Follow OWASP best practices (use the owasp-security skill)\n"
            "4. Make MINIMAL changes - only fix what's vulnerable\n"
            "5. Preserve all existing functionality\n"
            "6. Do NOT add comments like 'VULN' or 'FIXED'\n"
            "7. After all fixes, write a markdown summary to fix-output/summary.md"
        ),
        permission_mode="bypassPermissions",
        allowed_tools=[
            "Bash",
            "Read",
            "Edit",
            "Write",
            "Glob",
            "Grep",
            "Skill",
        ],
        max_turns=30,
        cwd=".",
    )
    
    prompt = f"""Fix ALL SonarCloud vulnerabilities in this repository.

WORKFLOW:

Step 1 - Discover vulnerabilities:
Use the sonarcloud-api-navigation skill to fetch ALL findings.

Step 2 - For EACH finding:
- Read the source code with the Read tool
- Reference the owasp-security skill for the correct fix pattern
- Apply the fix with the Edit tool

Step 3 - Apply these specific patterns:

For SQL Injection (jssecurity:S3649 / CWE-89):
- Replace template literals with parameterized queries
- Example for SQLite:
  BEFORE: `SELECT * FROM users WHERE username = '${{username}}'`
  AFTER:  db.all('SELECT * FROM users WHERE username = ?', [username], cb)

For XSS (jssecurity:S5131 / CWE-79):
- Escape user input before HTML reflection
- Add at top of file: const escapeHtml = (s) => String(s).replace(/[&<>"']/g, c => ({{
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }}[c]));
- Wrap user input: ${{escapeHtml(query)}}

For Path Traversal (jssecurity:S2083 / CWE-22):
- Validate filename doesn't contain '..' or '/'
- Use path.basename() to strip directory components
- Example:
  const safeName = path.basename(filename);
  if (safeName !== filename) return res.status(400).json({{error: 'Invalid filename'}});
  const filePath = path.join(__dirname, 'public', safeName);

For Command Injection (jssecurity:S2076 / CWE-78):
- Replace exec() with execFile() and array arguments
- Validate input strictly (whitelist hostnames)
- Example:
  BEFORE: exec(`ping -c 1 ${{host}}`, cb)
  AFTER:  
    if (!/^[a-zA-Z0-9.-]+$/.test(host)) return res.status(400).json({{error: 'Invalid host'}});
    execFile('ping', ['-c', '1', host], cb)

Step 4 - Write a summary:
Use the Write tool to create 'fix-output/summary.md' with this EXACT format:

# AI Fix Summary

Issue: #{issue_number}

## Vulnerabilities Fixed

### 1. SQL Injection (jssecurity:S3649)
- **File:** app/server.js (line 50-52)
- **Endpoint:** POST /login
- **Fix:** Replaced template literal with parameterized query
- **Before:** `db.all(\\`SELECT * FROM users WHERE username = '${{username}}'\\`)`
- **After:** `db.all('SELECT * FROM users WHERE username = ?', [username])`

### 2. XSS (jssecurity:S5131)
[similar format for each finding]

## Total: X vulnerabilities fixed

CRITICAL RULES:
- Make ONLY the security fixes, nothing else
- Preserve all existing functionality
- Do NOT add explanatory comments in code
- Do NOT remove "VULN X" comments if they exist (developer reference)
- Test that the file still parses (no syntax errors)
"""
    
    async for message in query(prompt=prompt, options=options):
        print(message)
    
    print("=" * 60)
    if summary_path.exists():
        print(f"Summary saved to {summary_path}")
        print("--- Summary content ---")
        print(summary_path.read_text())
    else:
        print(f"WARNING: No summary file generated at {summary_path}")
        # Create minimal fallback summary
        fallback = f"""# AI Fix Summary

Issue: #{issue_number}

The AI Fix Agent attempted to apply security fixes. Please review the diff in this PR.
"""
        summary_path.write_text(fallback)


if __name__ == "__main__":
    asyncio.run(main())