// ============================================================
// APP - DevSecOps Pipeline Testing
// ============================================================

const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const { execFile } = require('child_process');
const fs = require('fs');
const path = require('path');

const escapeHtml = (s) => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const app = express();
const PORT = 3000;

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ============================================================
// Database setup (SQLite in-memory)
// ============================================================
const db = new sqlite3.Database(':memory:');

db.serialize(() => {
  db.run("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, email TEXT)");
  db.run("INSERT INTO users (username, password, email) VALUES ('admin', 'admin123', 'admin@vuln.app')");
  db.run("INSERT INTO users (username, password, email) VALUES ('alice', 'wonderland', 'alice@vuln.app')");
  db.run("INSERT INTO users (username, password, email) VALUES ('bob', 'builder', 'bob@vuln.app')");
});

// ============================================================
// Homepage
// ============================================================
app.get('/', (req, res) => {
  res.send(`
    <h1>Vulnerable App - DevSecOps Demo</h1>
    <p>This app contains 4 intentional vulnerabilities for pipeline testing.</p>
    <ul>
      <li>POST /login - SQL Injection (CWE-89)</li>
      <li>GET  /search?q= - Reflected XSS (CWE-79)</li>
      <li>GET  /file?name= - Path Traversal (CWE-22)</li>
      <li>GET  /ping?host= - Command Injection / RCE (CWE-78)</li>
    </ul>
  `);
});

// ============================================================
// Endpoint: POST /login
// ============================================================
app.post('/login', (req, res) => {
  const { username, password } = req.body;

  db.all('SELECT * FROM users WHERE username = ? AND password = ?', [username, password], (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    if (rows.length > 0) {
      res.json({ success: true, user: rows[0], message: 'Login successful' });
    } else {
      res.status(401).json({ success: false, message: 'Invalid credentials' });
    }
  });
});

// ============================================================
// Endpoint: GET /search?q=
// ============================================================
app.get('/search', (req, res) => {
  const query = req.query.q || '';

  res.send(`
    <html>
      <body>
        <h1>Search Results</h1>
        <p>You searched for: ${escapeHtml(query)}</p>
        <p>No results found.</p>
      </body>
    </html>
  `);
});

// ============================================================
// Endpoint: GET /file?name=
// ============================================================
app.get('/file', (req, res) => {
  const filename = req.query.name || 'readme.txt';
  const safeName = path.basename(filename);
  if (safeName !== filename) return res.status(400).json({ error: 'Invalid filename' });
  const filePath = path.join(__dirname, 'public', safeName);

  fs.readFile(filePath, 'utf8', (err, data) => {
    if (err) {
      return res.status(404).json({ error: 'File not found', path: filePath });
    }
    res.type('text/plain').send(data);
  });
});

// ============================================================
// Endpoint: GET /ping?host=
// ============================================================
app.get('/ping', (req, res) => {
  const host = req.query.host || 'localhost';
  if (!/^[a-zA-Z0-9.-]+$/.test(host)) return res.status(400).json({ error: 'Invalid host' });

  execFile('ping', ['-c', '1', host], (err, stdout, stderr) => {
    if (err) {
      return res.status(500).json({ error: stderr });
    }
    res.type('text/plain').send(stdout);
  });
});

// ============================================================
// Start server
// ============================================================
app.listen(PORT, '0.0.0.0', () => {
  console.log(`app running on http://0.0.0.0:${PORT}`);
});
