# AI Fix Summary

Issue: #7

## Vulnerabilities Fixed

### 1. SQL Injection (jssecurity:S3649)
- **File:** app/server.js (lines 52–54)
- **Endpoint:** POST /login
- **Fix:** Replaced template literal string concatenation with a parameterized query using `?` placeholders and a bound parameter array, eliminating any possibility of user input altering the SQL statement structure.
- **Before:** `db.all(\`SELECT * FROM users WHERE username = '${username}' AND password = '${password}'\`, (err, rows) => {`
- **After:** `db.all('SELECT * FROM users WHERE username = ? AND password = ?', [username, password], (err, rows) => {`

### 2. XSS – Reflected Cross-Site Scripting (jssecurity:S5131)
- **File:** app/server.js (line 76)
- **Endpoint:** GET /search?q=
- **Fix:** Added an `escapeHtml` helper (line 11) that encodes the five dangerous HTML characters (`& < > " '`) into their entity equivalents. The reflected `query` parameter is now passed through `escapeHtml()` before being embedded in the response body.
- **Before:** `<p>You searched for: ${query}</p>`
- **After:** `<p>You searched for: ${escapeHtml(query)}</p>`

### 3. Path Traversal (jssecurity:S2083)
- **File:** app/server.js (lines 88–90)
- **Endpoint:** GET /file?name=
- **Fix:** Applied `path.basename()` to strip any directory components from the supplied filename, then validated that the result equals the original input (rejecting values like `../etc/passwd`). The resolved file path is constructed exclusively from the sanitised basename.
- **Before:** `const filePath = path.join(__dirname, 'public', filename);`
- **After:**
  ```js
  const safeName = path.basename(filename);
  if (safeName !== filename) return res.status(400).json({ error: 'Invalid filename' });
  const filePath = path.join(__dirname, 'public', safeName);
  ```

### 4. Command Injection (jssecurity:S2076)
- **File:** app/server.js (lines 7, 106–108)
- **Endpoint:** GET /ping?host=
- **Fix:** Replaced `exec()` with `execFile()` (imported at line 7) so the command and its arguments are passed as a discrete array — never interpreted by a shell. A strict allowlist regex (`/^[a-zA-Z0-9.-]+$/`) rejects any host value containing shell-special characters before the syscall is made.
- **Before:**
  ```js
  const { exec } = require('child_process');
  // ...
  const command = `ping -c 1 ${host}`;
  exec(command, (err, stdout, stderr) => { ... });
  ```
- **After:**
  ```js
  const { execFile } = require('child_process');
  // ...
  if (!/^[a-zA-Z0-9.-]+$/.test(host)) return res.status(400).json({ error: 'Invalid host' });
  execFile('ping', ['-c', '1', host], (err, stdout, stderr) => { ... });
  ```

### 5. Dockerfile – Script Execution During Install (docker:S6505)
- **File:** app/Dockerfile (line 7)
- **Fix:** Added `--ignore-scripts` to the npm install invocation, preventing any lifecycle scripts bundled with transitive dependencies from executing during the image build.
- **Before:** `RUN npm install --omit=dev`
- **After:** `RUN npm ci --omit=dev --ignore-scripts`

### 6. Dockerfile – Unlocked Dependency Versions (docker:S8543)
- **File:** app/Dockerfile (lines 6–7) + new `app/package-lock.json`
- **Fix:** Switched from `npm install` (which resolves versions at build time and can pick up new, potentially malicious releases) to `npm ci` (which installs exactly the versions recorded in `package-lock.json`). The `COPY` instruction was updated to `package*.json` so the lock file is included in the build context. `package-lock.json` was generated via `npm install --package-lock-only`.
- **Before:** `COPY package.json ./` / `RUN npm install --omit=dev`
- **After:** `COPY package*.json ./` / `RUN npm ci --omit=dev --ignore-scripts`

## Total: 6 vulnerabilities fixed

| # | Rule | Severity | CWE | File |
|---|------|----------|-----|------|
| 1 | jssecurity:S3649 | BLOCKER | CWE-89 | app/server.js |
| 2 | jssecurity:S5131 | BLOCKER | CWE-79 | app/server.js |
| 3 | jssecurity:S2083 | BLOCKER | CWE-22 | app/server.js |
| 4 | jssecurity:S2076 | BLOCKER | CWE-78 | app/server.js |
| 5 | docker:S6505   | MAJOR   | —       | app/Dockerfile |
| 6 | docker:S8543   | MAJOR   | —       | app/Dockerfile |
