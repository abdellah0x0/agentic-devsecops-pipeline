# Agentic-DevSecOps-Pipeline

**Agentic DevSecOps Pipeline** is a CI/CD security workflow that uses AI agents to validate SAST findings through actual exploitation, then automatically generates secure code fixes via Pull Requests. Built on GitHub Actions, SonarCloud, and the Claude Agent SDK, it transforms vulnerability prioritization from probabilistic guessing to deterministic proof-by-exploitation, while keeping a human-in-the-loop review step before any code is merged.


## Components
 
### Pipeline 1 — Detection
 
`devsecops-pipeline.yml`
 
| Job | Purpose |
|-----|---------|
| `build` | Builds the vulnerable app as a Docker image |
| `sonarcloud-scan` | Runs SonarCloud SAST scan |
| `exploit-gate` | Spawns sandbox + runs AI Exploit Agent |
| `publish-dashboard` | Generates HTML dashboard, deploys to GitHub Pages |
 
### Pipeline 2 — Auto-Fix
 
`auto-fix.yml`
 
Triggered when a GitHub issue receives the `auto-fix` label. Runs the AI Fix Agent which:
1. Fetches all vulnerabilities from SonarCloud
2. Applies secure patterns from the OWASP skill
3. Pushes changes to a new branch
4. Opens a Pull Request


### AI Agents
 
| Agent | Role | Skills used |
|-------|------|-------------|
| **Exploit Agent** | Validates findings by exploitation | `sonarcloud-api-navigation` |
| **Fix Agent** | Generates secure code fixes | `sonarcloud-api-navigation`, `owasp-security` |
 
### Skills
 
Reusable knowledge modules for Claude agents:
 
- **`sonarcloud-api-navigation`** — Fetches findings and source code context from SonarCloud API
- **`owasp-security`** — Battle-tested secure-by-default code patterns for OWASP Top 10
### Vulnerable Application
 
A deliberately vulnerable Express.js application with 4 OWASP-class vulnerabilities:
 
| Endpoint | Vulnerability | CWE |
|----------|---------------|-----|
| `POST /login` | SQL Injection | CWE-89 |
| `GET /search?q=` | Reflected XSS | CWE-79 |
| `GET /file?name=` | Path Traversal | CWE-22 |
| `GET /ping?host=` | Command Injection (RCE) | CWE-78 |
 
---
 
## Tech Stack
 
| Layer | Technology |
|-------|------------|
| CI/CD | GitHub Actions |
| SAST | SonarCloud |
| AI | Claude Sonnet 4.6 (via Agent SDK) |
| Container | Docker |
| App | Node.js + Express + SQLite |
| Dashboard | Static HTML (GitHub Pages) |
| Skills format | Claude Code SKILL.md |
 
---
 
## Setup
 
### Prerequisites
 
- GitHub account with Actions enabled
- SonarCloud account (free for public repos)
- Claude Pro subscription (for OAuth token)
### 1. Fork or clone the repo
 
```bash
git clone https://github.com/abdellah0x0/agentic-devsecops-pipeline.git
cd agentic-devsecops-pipeline
```
 
### 2. Configure SonarCloud
 
1. Create a project on [SonarCloud](https://sonarcloud.io)
2. Set "New Code" definition to "Previous version"
3. Disable Automatic Analysis (we use CI-based)
4. Generate a token from your account settings
### 3. Generate Claude OAuth token
 
```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code
 
# Generate a long-lived token for CI/CD
claude setup-token
# Follow browser flow, copy the token
```
 
### 4. Configure GitHub Secrets
 
Repository → Settings → Secrets and variables → Actions:
 
| Secret | Value |
|--------|-------|
| `SONAR_TOKEN` | Your SonarCloud token |
| `CLAUDE_CODE_OAUTH_TOKEN` | Token from `claude setup-token` |
 
### 5. Configure GitHub Permissions
 
Settings → Actions → General → Workflow permissions:
- Enable **Read and write permissions**
- Enable **Allow GitHub Actions to create and approve pull requests**
### 6. Enable GitHub Pages
 
Settings → Pages:
- Source: **Deploy from a branch**
- Branch: `gh-pages` / root (created automatically by the first run)
### 7. Update SonarCloud project key
 
Edit `.github/workflows/devsecops-pipeline.yml` and `.github/workflows/auto-fix.yml`, replacing:
```yaml
SONAR_PROJECT_KEY: abdellah0x0_agentic-devsecops-pipeline
```
with your own SonarCloud project key.
 
---
 
## Usage
 
### Trigger detection
 
```bash
git push
```
 
Pipeline 1 runs automatically, results visible at:
- **Actions tab** → workflow logs
- **Artifacts** → `report.json`
- **Dashboard** → `https://YOUR_USERNAME.github.io/YOUR_REPO/`
<img width="1919" height="864" alt="image" src="https://github.com/user-attachments/assets/0f3c3bdb-290b-4561-9413-2553e550a116" />

### Trigger auto-fix
 
1. Open the published dashboard
2. Click **"Generate AI Fix for All Vulnerabilities"**
3. GitHub opens an issue creation page (pre-filled)
4. Submit the issue
<img width="1919" height="657" alt="image" src="https://github.com/user-attachments/assets/86ea12a1-913d-439b-bc91-efee5c8d8206" />

6. Pipeline 2 starts automatically and creates a PR
<img width="1888" height="560" alt="image" src="https://github.com/user-attachments/assets/7371ef19-f4ba-4985-974d-8c88d4c56a60" />



### Review and merge
 
1. Open the generated Pull Request
<img width="1916" height="866" alt="image" src="https://github.com/user-attachments/assets/9ba9c25e-223c-42da-894c-430d53686979" />
3. Review the code diff
<img width="1887" height="863" alt="image" src="https://github.com/user-attachments/assets/73cf0790-743b-4598-8d44-7cc70009bf10" />
4. Wait for Pipeline 1 to re-validate (comment will appear)
5. Merge if validation passes
---
 
## Project Structure
 
```
agentic-devsecops-pipeline/
├── .github/workflows/
│   ├── devsecops-pipeline.yml    # Pipeline 1 (detection + dashboard)
│   └── auto-fix.yml               # Pipeline 2 (AI fix)
├── .claude/skills/
│   ├── sonarcloud-api-navigation/
│   │   └── SKILL.md
│   └── owasp-security/
│       └── SKILL.md
├── exploit-gate/
│   ├── main.py                    # Exploit agent entry point
│   └── requirements.txt
├── fix-agent/
│   ├── main.py                    # Fix agent entry point
│   └── requirements.txt
├── scripts/
│   └── generate_dashboard.py      # JSON → HTML dashboard
├── app/                           # Vulnerable Express.js app
│   ├── server.js
│   ├── Dockerfile
│   ├── package.json
│   └── public/
│       └── readme.txt
└── sonar-project.properties
```
