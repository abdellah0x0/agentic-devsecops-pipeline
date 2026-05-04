# AI Fix Summary

Issue: #9

## Vulnerabilities Fixed

### 1. SQL Injection (jssecurity:S3649)
- **File:** app/server.js (lines 50–53)
- **Endpoint:** POST /login
- **Fix:** Removed template-literal query construction; replaced with a parameterized `db.all()` call using `?` placeholders and a values array. The intermediate `query` variable was eliminated entirely so user-controlled strings never touch the SQL text.
- **Before:** `const query = \`SELECT * FROM users WHERE username = '${username}' AND password = '${password}'\`; db.all(query, cb)`
- **After:** `db.all('SELECT * FROM users WHERE username = ? AND password = ?', [username, password], cb)`

### 2. XSS – Reflected (jssecurity:S5131)
- **File:** app/server.js (line 75)
- **Endpoint:** GET /search?q=
- **Fix:** Added an `escapeHtml` helper at module scope (line 11) that maps the five dangerous HTML characters (`& < > " '`) to their safe entity equivalents. The reflected `query` value is now wrapped with `escapeHtml()` before being interpolated into the response HTML.
- **Before:** `<p>You searched for: ${query}</p>`
- **After:** `<p>You searched for: ${escapeHtml(query)}</p>`

### 3. Path Traversal (jssecurity:S2083)
- **File:** app/server.js (lines 87–89)
- **Endpoint:** GET /file?name=
- **Fix:** Applied `path.basename()` to strip any directory components from the user-supplied filename, then validated that the stripped name equals the original input (rejects inputs containing `/` or `..`). The resolved `filePath` is constructed from the sanitised `safeName` only.
- **Before:** `const filePath = path.join(__dirname, 'public', filename);`
- **After:**
  ```js
  const safeName = path.basename(filename);
  if (safeName !== filename) return res.status(400).json({ error: 'Invalid filename' });
  const filePath = path.join(__dirname, 'public', safeName);
  ```

### 4. Command Injection (jssecurity:S2076)
- **File:** app/server.js (lines 105–111)
- **Endpoint:** GET /ping?host=
- **Fix:** Replaced `exec()` (shell-interpolated) with `execFile()` (no shell, arguments passed as an array). Added a strict allowlist regex (`/^[a-zA-Z0-9.-]+$/`) that rejects any host value containing shell metacharacters before the command is even spawned. The import on line 7 was updated from `exec` to `execFile`.
- **Before:** `exec(\`ping -c 1 ${host}\`, cb)`
- **After:**
  ```js
  if (!/^[a-zA-Z0-9.-]+$/.test(host)) return res.status(400).json({ error: 'Invalid host' });
  execFile('ping', ['-c', '1', host], cb)
  ```

### 5. npm install – Script Execution Risk (docker:S6505)
- **File:** app/Dockerfile (line 7)
- **Fix:** Added `--ignore-scripts` to the `npm install` invocation. This prevents lifecycle scripts (`preinstall`, `postinstall`, etc.) defined by third-party packages from executing arbitrary shell commands during image build.
- **Before:** `RUN npm install --omit=dev`
- **After:** `RUN npm ci --omit=dev --ignore-scripts`

### 6. npm install – Unlocked Dependency Versions (docker:S8543)
- **File:** app/Dockerfile (lines 6–7)
- **Fix:** Switched from `npm install` (resolves versions at build time, non-deterministic) to `npm ci` (requires and strictly respects `package-lock.json`, reproducible). `package-lock.json` is now copied alongside `package.json` so the lockfile is available inside the build context.
- **Before:** `COPY package.json ./` / `RUN npm install --omit=dev`
- **After:** `COPY package.json package-lock.json ./` / `RUN npm ci --omit=dev --ignore-scripts`

## Total: 6 vulnerabilities fixed
