/**
 * app.js
 * Application logic — wires API calls to UI updates.
 * Imports: api.js, ui.js (loaded before this in HTML)
 */

/* ── STATE ──────────────────────────────────────────────────────── */
let activeSchemaId   = null;
let activeSchemaName = null;
let isSending        = false;
let selectedPlatform = 'postgresql';
let activeTab        = 'tab-paste';

/* ── BOOT ───────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const user = getUser();
  if (user && getToken()) {
    showAppPage(user);
    loadSchemas();
  } else {
    showAuthPage();
  }

  bindComposer();
  bindSchemaModal();
});

/* ── AUTH HANDLERS ───────────────────────────────────────────────── */
async function handleLogin() {
  const email    = el('login-email').value.trim();
  const password = el('login-password').value;
  hideAlert('auth-alert');

  if (!email || !password) {
    showAlert('auth-alert', 'Please enter your email and password.');
    return;
  }

  const btn = el('login-btn');
  btn.disabled = true;
  btn.textContent = 'Signing in…';

  try {
    const user = await apiLogin(email, password);
    showAppPage(user);
    loadSchemas();
  } catch (err) {
    showAlert('auth-alert', err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Sign in';
  }
}

async function handleRegister() {
  const name     = el('reg-name').value.trim();
  const email    = el('reg-email').value.trim();
  const password = el('reg-password').value;
  hideAlert('auth-alert');

  if (!name || !email || !password) {
    showAlert('auth-alert', 'Please fill in all fields.');
    return;
  }

  const btn = el('register-btn');
  btn.disabled = true;
  btn.textContent = 'Creating account…';

  try {
    await apiRegister(name, email, password);
    showAlert('auth-alert', 'Account created. Please sign in.', 'success');
    showLoginForm();
  } catch (err) {
    showAlert('auth-alert', err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Create account';
  }
}

function handleLogout() {
  clearToken();
  activeSchemaId   = null;
  activeSchemaName = null;
  showAuthPage();
  clearChat();
  clearTopbar();
}

/* ── SCHEMAS ─────────────────────────────────────────────────────── */
async function loadSchemas() {
  try {
    const schemas = await apiGetSchemas();
    renderSchemas(schemas, handleSchemaSelect);

    // Auto-load active schema
    const active = schemas.find(s => s.is_active);
    if (active && active.id !== activeSchemaId) {
      activeSchemaId   = active.id;
      activeSchemaName = active.name;
      setTopbar(active.name, active.platform);
      await loadHistory(active.id);
    } else if (!active) {
      showEmptyState(false);
    }
  } catch (err) {
    console.error('Failed to load schemas:', err);
  }
}

async function handleSchemaSelect(id, name, platform) {
  if (id === activeSchemaId) return;
  try {
    await apiActivateSchema(id);
    activeSchemaId   = id;
    activeSchemaName = name;
    setTopbar(name, platform);
    await loadSchemas();
    await loadHistory(id);
  } catch (err) {
    console.error('Failed to activate schema:', err);
  }
}

/* ── HISTORY ─────────────────────────────────────────────────────── */
async function loadHistory(schemaId) {
  clearChat();
  try {
    const messages = await apiGetHistory(schemaId);

    if (!Array.isArray(messages) || messages.length === 0) {
      showEmptyState(true);
      return;
    }

    showHistoryDivider();

    messages.forEach(msg => {
      if (msg.role === 'user') {
        appendUserMsg(msg.message);
      } else {
        appendAssistantMsg(msg.sql_output, msg.message, null);
      }
    });
  } catch (err) {
    showEmptyState(true);
  }
}

async function handleClearHistory() {
  if (!activeSchemaId) return;
  if (!confirm(`Clear all chat history for "${activeSchemaName}"?\nThis cannot be undone.`)) return;

  try {
    await apiClearHistory(activeSchemaId);
    showEmptyState(true);
  } catch (err) {
    alert('Failed to clear history: ' + err.message);
  }
}

/* ── CHAT ────────────────────────────────────────────────────────── */
function bindComposer() {
  const input = el('composer-input');
  const btn   = el('send-btn');

  input.addEventListener('input', () => {
    // Auto-resize
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    btn.disabled = !input.value.trim() || isSending;
  });

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!btn.disabled) handleSend();
    }
  });

  // Suggestion chips — delegated
  el('chat-inner').addEventListener('click', e => {
    const chip = e.target.closest('[data-suggestion]');
    if (chip) {
      input.value = chip.dataset.suggestion;
      input.dispatchEvent(new Event('input'));
      handleSend();
    }
  });
}

async function handleSend() {
  const text = getComposerValue();
  if (!text || !activeSchemaId || isSending) return;

  // Remove empty state if present
  const empty = el('chat-inner').querySelector('.empty-state');
  if (empty) empty.remove();

  isSending = true;
  clearComposer();

  appendUserMsg(text);

  const typingId = 'typing-' + Date.now();
  appendTyping(typingId);

  try {
    const data = await apiChat(text, activeSchemaId);
    removeTyping(typingId);
    appendAssistantMsg(
      data.sql_output       || null,
      data.explanation      || data.message || null,
      data.intent           || null
    );
  } catch (err) {
    removeTyping(typingId);
    appendErrorMsg(err.message);
  } finally {
    isSending = false;
    el('send-btn').disabled = !el('composer-input').value.trim();
  }
}

/* ── SCHEMA MODAL ────────────────────────────────────────────────── */
function bindSchemaModal() {
  // Platform buttons
  document.querySelectorAll('.platform-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.platform-btn')
        .forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedPlatform = btn.dataset.platform;

      const portMap = { postgresql: 5432, mysql: 3306, sqlite: 0, sqlserver: 1433 };
      const portEl  = el('modal-db-port');
      if (portEl) portEl.value = portMap[selectedPlatform] || 5432;
    });
  });

  // Tab switching
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      activeTab = btn.dataset.tab;
      el(activeTab).classList.add('active');
    });
  });
}

function openSchemaModal() {
  hide('modal-error');
  openModal('schema-modal');
}

function closeSchemaModal() {
  closeModal('schema-modal');
  // Reset fields
  el('modal-schema-name').value = '';
  el('modal-ddl').value         = '';
  hide('modal-error');
}

async function handleSaveSchema() {
  const name  = el('modal-schema-name').value.trim();
  const errEl = el('modal-error');
  hide('modal-error');

  if (!name) {
    errEl.textContent = 'Please enter a schema name.';
    show('modal-error');
    return;
  }

  const saveBtn = el('modal-save-btn');
  saveBtn.disabled = true;
  saveBtn.textContent = 'Saving…';

  try {
    if (activeTab === 'tab-paste') {
      const ddl = el('modal-ddl').value.trim();
      if (!ddl) throw new Error('Please paste your CREATE TABLE statements.');
      await apiCreateSchema(name, selectedPlatform, ddl);

    } else {
      const host = el('modal-db-host').value.trim() || 'localhost';
      const port = el('modal-db-port').value || '5432';
      const db   = el('modal-db-name').value.trim();
      const user = el('modal-db-user').value.trim();
      const pass = el('modal-db-pass').value;
      if (!db || !user) throw new Error('Please fill in database name and username.');
      await apiConnectDB(name, selectedPlatform, host, port, db, user, pass);
    }

    closeSchemaModal();
    await loadSchemas();
  } catch (err) {
    errEl.textContent = err.message;
    show('modal-error');
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = 'Save';
  }
}