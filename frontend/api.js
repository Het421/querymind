/**
 * api.js
 * All communication with the FastAPI backend lives here.
 * No fetch() calls anywhere else in the app.
 */

const API_BASE = 'http://localhost:8000';

/* ── TOKEN STORAGE ─────────────────────────────────────────────── */

function getToken() {
  return sessionStorage.getItem('token');
}

function setToken(token) {
  sessionStorage.setItem('token', token);
}

function clearToken() {
  sessionStorage.removeItem('token');
  sessionStorage.removeItem('user');
}

function getUser() {
  const raw = sessionStorage.getItem('user');
  return raw ? JSON.parse(raw) : null;
}

function setUser(user) {
  sessionStorage.setItem('user', JSON.stringify(user));
}

/* ── BASE REQUEST ───────────────────────────────────────────────── */

async function request(method, path, body = null, useAuth = true) {
  const headers = { 'Content-Type': 'application/json' };
  if (useAuth) {
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(`${API_BASE}${path}`, opts);
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.detail || `Request failed (${res.status})`);
  }
  return data;
}

async function requestForm(path, formData) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    body: formData
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

/* ── AUTH ───────────────────────────────────────────────────────── */

async function apiLogin(email, password) {
  const form = new FormData();
  form.append('username', email);
  form.append('password', password);
  const data = await requestForm('/auth/login', form);
  setToken(data.access_token);
  setUser(data.user);
  return data.user;
}

async function apiRegister(fullName, email, password) {
  return request('POST', '/auth/register', {
    full_name: fullName,
    email,
    password
  }, false);
}

/* ── SCHEMAS ────────────────────────────────────────────────────── */

async function apiGetSchemas() {
  return request('GET', '/schemas/');
}

async function apiCreateSchema(name, platform, schemaContent) {
  return request('POST', '/schemas/', {
    name,
    platform,
    schema_content: schemaContent,
    source: 'manual'
  });
}

async function apiActivateSchema(schemaId) {
  return request('PATCH', `/schemas/${schemaId}/activate`);
}

async function apiConnectDB(name, platform, host, port, database, username, password) {
  return request('POST', '/mcp/connect', {
    name, platform, host,
    port: parseInt(port, 10),
    database, username, password
  });
}

/* ── HISTORY ────────────────────────────────────────────────────── */

async function apiGetHistory(schemaId) {
  return request('GET', `/history/schema/${schemaId}`);
}

async function apiClearHistory(schemaId) {
  const token = getToken();
  const res = await fetch(`${API_BASE}/history/schema/${schemaId}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Failed to clear history');
  }
}

/* ── CHAT ───────────────────────────────────────────────────────── */

async function apiChat(message, schemaId) {
  return request('POST', '/chat/', {
    message,
    schema_id: schemaId
  });
}