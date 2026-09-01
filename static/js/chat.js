(() => {
  const listEl = document.getElementById("conversation-list");
  const messagesEl = document.getElementById("messages");
  const emptyState = document.getElementById("empty-state");
  const chatTitle = document.getElementById("chat-title");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("message-input");
  const sendBtn = document.getElementById("send-btn");
  const newChatBtn = document.getElementById("new-chat-btn");
  const template = document.getElementById("message-template");
  const toggleBtns = document.querySelectorAll(".toggle-btn");

  let activeId = null;
  let loading = false;

  async function api(path, options = {}) {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    if (res.status === 204) return null;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || res.statusText);
    return data;
  }

  function setSourceToggle(sourceType) {
    toggleBtns.forEach((btn) => {
      const val = btn.dataset.source || "";
      btn.classList.toggle("active", val === (sourceType || ""));
    });
  }

  function renderCitationCard(c) {
    const card = document.createElement("div");
    card.className = "citation-card";
    const pages =
      c.page_end && c.page_end !== c.page_start
        ? `${c.page_start}–${c.page_end}`
        : c.page_start;
    const categoryBadge = c.doc_category
      ? `<span class="doc-category">${escapeHtml(c.doc_category)}</span>`
      : "";
    card.innerHTML = `
      <div class="doc-title">${escapeHtml(c.document_title)} ${categoryBadge}</div>
      <div class="meta">p. ${pages} · ${escapeHtml(c.source_file)}</div>
      <div class="quote">"${escapeHtml(c.quote || "")}"</div>
    `;
    return card;
  }

  function escapeHtml(text) {
    const d = document.createElement("div");
    d.textContent = text || "";
    return d.innerHTML;
  }

  function appendMessage(msg) {
    emptyState.style.display = "none";
    const node = template.content.cloneNode(true);
    const wrap = node.querySelector(".message");
    wrap.classList.add(msg.role);
    if (msg.role === "assistant" && msg.answer?.refused) {
      wrap.classList.add("refused");
    }
    node.querySelector(".bubble").textContent = msg.content;

    const citationsEl = node.querySelector(".citations");
    const citations = msg.citations || msg.answer?.citations || [];
    citations.forEach((c) => citationsEl.appendChild(renderCitationCard(c)));

    messagesEl.appendChild(node);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function clearMessages() {
    messagesEl.querySelectorAll(".message, .loading").forEach((el) => el.remove());
    emptyState.style.display = "";
  }

  function showLoading() {
    const el = document.createElement("div");
    el.className = "loading";
    el.id = "loading-indicator";
    el.innerHTML = '<div class="spinner"></div><span>Oakley is thinking…</span>';
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function hideLoading() {
    document.getElementById("loading-indicator")?.remove();
  }

  async function loadConversations() {
    const convs = await api("/api/conversations");
    listEl.innerHTML = "";
    convs.forEach((c) => {
      const li = document.createElement("li");
      li.className = "conversation-item" + (c.id === activeId ? " active" : "");
      li.dataset.id = c.id;
      li.innerHTML = `
        <span class="title">${escapeHtml(c.title)}</span>
        <button type="button" class="delete-btn" title="Delete">×</button>
      `;
      li.querySelector(".title").addEventListener("click", () => selectConversation(c.id));
      li.querySelector(".delete-btn").addEventListener("click", (e) => {
        e.stopPropagation();
        deleteConversation(c.id);
      });
      listEl.appendChild(li);
    });
  }

  async function selectConversation(id) {
    activeId = id;
    const data = await api(`/api/conversations/${id}`);
    chatTitle.textContent = data.title;
    setSourceToggle(data.source_type);
    clearMessages();
    if (!data.messages.length) {
      emptyState.style.display = "";
    } else {
      data.messages.forEach(appendMessage);
    }
    await loadConversations();
  }

  async function newConversation() {
    const conv = await api("/api/conversations", { method: "POST", body: "{}" });
    activeId = conv.id;
    chatTitle.textContent = conv.title;
    setSourceToggle(null);
    clearMessages();
    await loadConversations();
    input.focus();
  }

  async function deleteConversation(id) {
    if (!confirm("Delete this conversation?")) return;
    await api(`/api/conversations/${id}`, { method: "DELETE" });
    if (activeId === id) {
      activeId = null;
      clearMessages();
      chatTitle.textContent = "New conversation";
      const convs = await api("/api/conversations");
      if (convs.length) await selectConversation(convs[0].id);
      else await newConversation();
    }
    await loadConversations();
  }

  async function updateSource(sourceType) {
    if (!activeId) return;
    const body = JSON.stringify({ source_type: sourceType || null });
    const conv = await api(`/api/conversations/${activeId}`, { method: "PATCH", body });
    setSourceToggle(conv.source_type);
  }

  async function sendMessage() {
    if (loading || !input.value.trim()) return;
    if (!activeId) await newConversation();

    const content = input.value.trim();
    input.value = "";
    appendMessage({ role: "user", content });
    loading = true;
    sendBtn.disabled = true;
    showLoading();

    try {
      const result = await api(`/api/conversations/${activeId}/messages`, {
        method: "POST",
        body: JSON.stringify({ content }),
      });
      hideLoading();
      appendMessage(result.assistant_message);
      await loadConversations();
      const conv = await api(`/api/conversations/${activeId}`);
      chatTitle.textContent = conv.title;
    } catch (err) {
      hideLoading();
      appendMessage({
        role: "assistant",
        content: `Error: ${err.message}`,
        answer: { refused: true },
      });
    } finally {
      loading = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    void sendMessage();
  });

  input.addEventListener(
    "keydown",
    (e) => {
      const isEnter = e.key === "Enter" || e.code === "Enter" || e.code === "NumpadEnter";
      if (!isEnter || e.shiftKey || e.isComposing) return;
      e.preventDefault();
      e.stopPropagation();
      void sendMessage();
    },
    true
  );

  toggleBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const source = btn.dataset.source || null;
      updateSource(source);
    });
  });

  newChatBtn.addEventListener("click", newConversation);

  (async function init() {
    try {
      const health = await api("/api/health");
      if (!health.gemini_configured) {
        emptyState.innerHTML = "<p>GEMINI_API_KEY not configured. Add it to your local .env file.</p>";
      } else if (!health.indexed_chunks) {
        emptyState.innerHTML = "<p>No indexed documents. Run <code>oakley ingest</code> in your terminal first.</p>";
      }
    } catch (_) { /* ignore */ }

    const convs = await api("/api/conversations");
    if (convs.length) await selectConversation(convs[0].id);
    else await newConversation();
  })();
})();
