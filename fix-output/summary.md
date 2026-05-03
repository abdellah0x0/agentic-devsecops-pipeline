# AI Fix Summary

Issue: #1

## Vulnerabilities Fixed

### 1. SQL Injection (jssecurity:S3649)
- **File:** app/server.js (line 50-53)
- **Endpoint:** POST /login
- **Fix:** Replaced template literal with parameterized query using `?` placeholders and a bound values array
- **Before:** `db.all(\`SELECT * FROM users WHERE username = '${username}' AND password = '${password}'\`, cb)`
- **After:** `db.all('SELECT * FROM users WHERE username = ? AND password = ?', [username, password], cb)`

### 2. XSS — Reflected (jssecurity:S5131)
- **File:** app/server.js (line 70-79)
- **Endpoint:** GET /search?q=
- **Fix:** Added `escapeHtml()` helper to encode `&`, `<`, `>`, `"`, `'` before reflecting user input into HTML response
- **Before:** `<p>You searched for: ${query}</p>`
- **After:** `<p>You searched for: ${escapeHtml(query)}</p>`

### 3. Path Traversal (jssecurity:S2083)
- **File:** app/server.js (line 85-89)
- **Endpoint:** GET /file?name=
- **Fix:** Applied `path.basename()` to strip all directory components from the user-supplied filename and rejected requests where the basename differs from the supplied value
- **Before:** `const filePath = path.join(__dirname, 'public', filename);`
- **After:**
  ```js
  const safeName = path.basename(filename);
  if (safeName !== filename) return res.status(400).json({ error: 'Invalid filename' });
  const filePath = path.join(__dirname, 'public', safeName);
  ```

### 4. Command Injection (jssecurity:S2076)
- **File:** app/server.js (line 102-111)
- **Endpoint:** GET /ping?host=
- **Fix:** Replaced `exec()` with `execFile()` (no shell spawned) and added strict allowlist regex validation rejecting any host containing characters outside `[a-zA-Z0-9.-]`
- **Before:** `exec(\`ping -c 1 ${host}\`, cb)`
- **After:**
  ```js
  if (!/^[a-zA-Z0-9.-]+$/.test(host)) return res.status(400).json({ error: 'Invalid host' });
  execFile('ping', ['-c', '1', host], cb)
  ```

### 5. npm install without --ignore-scripts (docker:S6505)
- **File:** app/Dockerfile (line 7)
- **Fix:** Added `--ignore-scripts` flag to prevent lifecycle scripts in dependencies from executing arbitrary shell code during installation; switched to `npm ci` for deterministic installs
- **Before:** `RUN npm install --omit=dev`
- **After:** `RUN npm ci --omit=dev --ignore-scripts`

### 6. Dependencies without locked versions (docker:S8543)
- **File:** app/Dockerfile (line 6-7)
- **Fix:** Generated `package-lock.json` and added it to the `COPY` instruction so `npm ci` enforces exact resolved versions on every build, eliminating supply-chain drift
- **Before:** `COPY package.json ./`
- **After:** `COPY package.json package-lock.json ./`

## Total: 6 vulnerabilities fixed
