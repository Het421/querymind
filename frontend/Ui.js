/**
 * ui.js
 * DOM helpers and rendering functions.
 * No API calls here — only building and updating the DOM.
 */

/* ── UTILS ──────────────────────────────────────────────────────── */

function esc(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function show(id) { document.getElementById(id).classList.remove('hidden'); }
function hide(id) { document.getElementById(id).classList.add('hidden'); }
function el(id)   { return document.getElementById(id); }

function showAlert(id, message, type = 'error') {
  const el_ = el(id);
  el_.textContent = message;
  el_.className = `auth-alert ${type}`;
  el_.classList.remove('hidden');
}

function hideAlert(id) { el(id).classList.add('hidden'); }

/* ── PAGE SWITCHING ─────────────────────────────────────────────── */

function showAuthPage() {
  show('auth-page');
  hide('app-page');
}

function showAppPage(user) {
  hide('auth-page');
  show('app-page');
  const name = user.full_name || user.email || 'User';
  el('user-avatar').textContent  = name.charAt(0).toUpperCase();
  el('user-label').textContent   = name;
}

/* ── AUTH FORM SWITCHING ────────────────────────────────────────── */

function showLoginForm() {
  show('login-form');
  hide('register-form');
  hideAlert('auth-alert');
}

function showRegisterForm() {
  hide('login-form');
  show('register-form');
  hideAlert('auth-alert');
}

/* ── TOPBAR ─────────────────────────────────────────────────────── */

function setTopbar(name, platform) {
  el('topbar-title').textContent   = name;
  el('topbar-platform').textContent = platform.toUpperCase();
}

function clearTopbar() {
  el('topbar-title').textContent    = 'No schema selected';
  el('topbar-platform').textContent = '';
}

/* ── SCHEMA LIST ────────────────────────────────────────────────── */

function renderSchemas(schemas, onSelect) {
  const list = el('schema-list');

  if (!schemas.length) {
    list.innerHTML = '<div class="schema-empty">No schemas yet.<br>Add one to get started.</div>';
    return;
  }

  list.innerHTML = schemas.map(s => `
    <div class="schema-item ${s.is_active ? 'active' : ''}"
         data-id="${s.id}"
         data-name="${esc(s.name)}"
         data-platform="${s.platform}">
      <div class="schema-item-icon">🗄</div>
      <div class="schema-item-info">
        <div class="schema-item-name">${esc(s.name)}</div>
        <div class="schema-item-platform">${s.platform}</div>
      </div>
      ${s.is_active ? '<div class="schema-item-dot"></div>' : ''}
    </div>
  `).join('');

  list.querySelectorAll('.schema-item').forEach(item => {
    item.addEventListener('click', () => {
      const { id, name, platform } = item.dataset;
      onSelect(id, name, platform);
    });
  });
}

/* ── CHAT ───────────────────────────────────────────────────────── */

function showEmptyState(hasSchema) {
  el('chat-inner').innerHTML = `
    <div class="empty-state">
      <h3>${hasSchema ? 'Start the conversation' : 'No schema selected'}</h3>
      <p>${hasSchema
        ? 'Ask anything about your database in plain English.'
        : 'Select a schema from the sidebar or add a new one.'}</p>
      ${hasSchema ? `
      <div class="chips">
        <button class="chip" data-suggestion="Show all tables and their columns">Show all tables and columns</button>
        <button class="chip" data-suggestion="Write a query to count rows in each table">Count rows in each table</button>
        <button class="chip" data-suggestion="Find duplicate records in the database">Find duplicate records</button>
        <button class="chip" data-suggestion="What indexes should I add to improve performance?">Suggest indexes</button>
      </div>` : ''}
    </div>`;
}

function showHistoryDivider() {
  const inner = el('chat-inner');
  const div = document.createElement('div');
  div.className = 'history-divider';
  div.textContent = 'Previous conversation';
  inner.appendChild(div);
}

function clearChat() {
  el('chat-inner').innerHTML = '';
}

function appendUserMsg(text) {
  const inner = el('chat-inner');
  const div = document.createElement('div');
  div.className = 'msg user';
  div.innerHTML = `<div class="msg-bubble">${esc(text)}</div>`;
  inner.appendChild(div);
  scrollToBottom();
}

function appendTyping(id) {
  const inner = el('chat-inner');
  const div = document.createElement('div');
  div.className = 'msg assistant';
  div.id = id;
  div.innerHTML = `
    <div class="msg-body">
      <div class="msg-meta">
        <div class="msg-icon">⚡</div>
      </div>
      <div class="typing-dots">
        <span></span><span></span><span></span>
      </div>
    </div>`;
  inner.appendChild(div);
  scrollToBottom();
}

function removeTyping(id) {
  const item = document.getElementById(id);
  if (item) item.remove();
}

function appendAssistantMsg(sql, explanation, intent) {
  const inner = el('chat-inner');
  const div = document.createElement('div');
  div.className = 'msg assistant';

  const intentTag = intent
    ? `<span class="intent-tag">${esc(intent)}</span>`
    : '';

  let sqlBlock = '';
  if (sql) {
    sqlBlock = `
      <div class="sql-block">
        <div class="sql-block-header">
          <span class="sql-block-label">SQL</span>
          <button class="btn-copy" data-sql="${esc(sql)}">Copy</button>
        </div>
        <pre>${esc(sql)}</pre>
      </div>`;
  }

  let explBlock = '';
  if (explanation) {
    explBlock = `<div class="explanation">${esc(explanation)}</div>`;
  }

  div.innerHTML = `
    <div class="msg-body">
      <div class="msg-meta">
        <div class="msg-icon">⚡</div>
        ${intentTag}
      </div>
      ${sqlBlock}
      ${explBlock}
    </div>`;

  // Attach copy handler
  const copyBtn = div.querySelector('.btn-copy');
  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(sql).then(() => {
        copyBtn.textContent = 'Copied';
        setTimeout(() => copyBtn.textContent = 'Copy', 2000);
      });
    });
  }

  inner.appendChild(div);
  scrollToBottom();
}

function appendErrorMsg(message) {
  const inner = el('chat-inner');
  const div = document.createElement('div');
  div.className = 'msg assistant';
  div.innerHTML = `
    <div class="msg-body">
      <div class="msg-meta">
        <div class="msg-icon">⚡</div>
      </div>
      <div class="msg-error">${esc(message)}</div>
    </div>`;
  inner.appendChild(div);
  scrollToBottom();
}

function scrollToBottom() {
  const area = document.querySelector('.chat-area');
  if (area) setTimeout(() => area.scrollTop = area.scrollHeight, 40);
}

/* ── COMPOSER ───────────────────────────────────────────────────── */

function setComposerEnabled(enabled) {
  const ta  = el('composer-input');
  const btn = el('send-btn');
  ta.disabled  = !enabled;
  btn.disabled = !enabled || !ta.value.trim();
}

function getComposerValue() {
  return el('composer-input').value.trim();
}

function clearComposer() {
  const ta = el('composer-input');
  ta.value = '';
  ta.style.height = 'auto';
  el('send-btn').disabled = true;
}

/* ── MODAL ──────────────────────────────────────────────────────── */

function openModal(id) {
  show(id);
}

function closeModal(id) {
  hide(id);
}