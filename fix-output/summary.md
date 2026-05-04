# AI Fix Summary

Issue: #5

## Vulnerabilities Fixed

### 1. SQL Injection (jssecurity:S3649)
- **File:** app/server.js (line 50–53)
- **Endpoint:** POST /login
- **Fix:** Replaced template-literal query with a parameterized query using `?` placeholders; user-supplied `username` and `password` are now passed as a bound parameter array and never interpolated into the SQL string.
- **Before:** `db.all(\`SELECT * FROM users WHERE username = '${username}' AND password = '${password}'\`, cb)`
- **After:** `db.all('SELECT * FROM users WHERE username = ? AND password = ?', [username, password], cb)`

### 2. XSS — Reflected (jssecurity:S5131)
- **File:** app/server.js (line 17, line 75)
- **Endpoint:** GET /search?q=
- **Fix:** Added an `escapeHtml` helper that encodes the five dangerous HTML characters (`& < > " '`). The reflected `query` value is now wrapped with `escapeHtml()` before being embedded in the response HTML.
- **Before:** `<p>You searched for: ${query}</p>`
- **After:** `<p>You searched for: ${escapeHtml(query)}</p>`

### 3. Path Traversal (jssecurity:S2083)
- **File:** app/server.js (line 86–89)
- **Endpoint:** GET /file?name=
- **Fix:** Applied `path.basename()` to strip any directory components from the supplied filename. A strict equality check (`safeName !== filename`) rejects any input that contained path separators or `..` sequences before `basename` could strip them.
- **Before:** `const filePath = path.join(__dirname, 'public', filename);`
- **After:**
  ```js
  const safeName = path.basename(filename);
  if (safeName !== filename) return res.status(400).json({ error: 'Invalid filename' });
  const filePath = path.join(__dirname, 'public', safeName);
  ```

### 4. Command Injection (jssecurity:S2076)
- **File:** app/server.js (line 7, line 105–107)
- **Endpoint:** GET /ping?host=
- **Fix:** Replaced `exec()` (which invokes a shell and therefore enables shell-metacharacter injection) with `execFile()` (which spawns the binary directly with an argv array). Added a strict allowlist regex (`/^[a-zA-Z0-9.-]+$/`) that rejects any host containing shell-special characters before the process is even spawned.
- **Before:** `exec(\`ping -c 1 ${host}\`, cb)`
- **After:**
  ```js
  if (!/^[a-zA-Z0-9.-]+$/.test(host)) return res.status(400).json({ error: 'Invalid host' });
  execFile('ping', ['-c', '1', host], cb)
  ```

### 5. Dockerfile — Script Execution Risk (docker:S6505)
- **File:** app/Dockerfile (line 7)
- **Fix:** Added `--ignore-scripts` to the `npm` invocation so that lifecycle scripts declared in `package.json` or any dependency cannot execute arbitrary shell code during installation.
- **Before:** `RUN npm install --omit=dev`
- **After:** `RUN npm ci --omit=dev --ignore-scripts`

### 6. Dockerfile — Unlocked Dependency Versions (docker:S8543)
- **File:** app/Dockerfile (line 6–7)
- **Fix:** Switched from `npm install` (which resolves semver ranges at build time and can silently pull in different versions) to `npm ci` (which installs exactly the versions pinned in `package-lock.json`). The lockfile is now copied into the image layer before the install step.
- **Before:** `COPY package.json ./` + `RUN npm install --omit=dev`
- **After:** `COPY package.json package-lock.json ./` + `RUN npm ci --omit=dev --ignore-scripts`

---

## Total: 6 vulnerabilities fixed

| # | Rule | Severity | File | CWE |
|---|------|----------|------|-----|
| 1 | jssecurity:S3649 | BLOCKER | app/server.js | CWE-89 |
| 2 | jssecurity:S5131 | BLOCKER | app/server.js | CWE-79 |
| 3 | jssecurity:S2083 | BLOCKER | app/server.js | CWE-22 |
| 4 | jssecurity:S2076 | BLOCKER | app/server.js | CWE-78 |
| 5 | docker:S6505   | MAJOR   | app/Dockerfile | — |
| 6 | docker:S8543   | MAJOR   | app/Dockerfile | — |
