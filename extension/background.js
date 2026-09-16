/**
 * background.js — Mnemosyne Background Service Worker
 *
 * Handles:
 *  1. Storing and retrieving authentication token.
 *  2. Receiving captured messages from content scripts.
 *  3. Syncing messages to the Mnemosyne backend.
 *  4. Notifying the user of sync status.
 *  5. Serving context retrieval requests from the popup.
 */

"use strict";

// ─────────────────────────────────────────────────────────────────────────────
// Configuration
// ─────────────────────────────────────────────────────────────────────────────

const DEFAULT_API_URL = "https://mnemosyne-fyv5.onrender.com/api/v1";

// ─────────────────────────────────────────────────────────────────────────────
// Storage helpers
// ─────────────────────────────────────────────────────────────────────────────

async function getStorage(keys) {
  return new Promise((resolve) => chrome.storage.local.get(keys, resolve));
}

async function setStorage(data) {
  return new Promise((resolve) => chrome.storage.local.set(data, resolve));
}

async function getAuthToken() {
  const { authToken } = await getStorage(["authToken"]);
  return authToken || null;
}

async function getApiUrl() {
  const { apiUrl } = await getStorage(["apiUrl"]);
  return apiUrl || DEFAULT_API_URL;
}

async function getSelectedProject() {
  const { selectedProject } = await getStorage(["selectedProject"]);
  return selectedProject || null;
}

// ─────────────────────────────────────────────────────────────────────────────
// API client
// ─────────────────────────────────────────────────────────────────────────────

async function apiRequest(path, options = {}) {
  const baseUrl = await getApiUrl();
  const token = await getAuthToken();

  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `HTTP ${response.status}`);
  }

  return response.json();
}

// ─────────────────────────────────────────────────────────────────────────────
// Sync messages to backend
// ─────────────────────────────────────────────────────────────────────────────

async function syncMessagesToBackend(messages, tabUrl, platformName) {
  const project = await getSelectedProject();
  if (!project) {
    console.warn("[Mnemosyne] No project selected — skipping sync.");
    return;
  }

  const hashBuffer = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(tabUrl));
  const hash = Array.from(new Uint8Array(hashBuffer)).map(b => b.toString(16).padStart(2, "0")).join("").slice(0, 24);
  const conversationId = `ext-${hash}`;

  try {
    await apiRequest("/memory/ingest", {
      method: "POST",
      body: JSON.stringify({
        project_id: project.id,
        conversation_id: conversationId,
        messages: messages.map((msg) => ({
          role: msg.role,
          content: msg.content,
          external_id: msg.external_id,
          created_at: msg.created_at,
          metadata: {},
        })),
        metadata: {
          source_url: tabUrl,
          via: "chrome_extension",
          platform: platformName || "Unknown",
        },
      }),
    });

    console.info(`[Mnemosyne] Synced ${messages.length} messages for project ${project.id}`);
    await showNotification("Memory synced", `${messages.length} messages stored for "${project.name}"`);
  } catch (err) {
    console.error("[Mnemosyne] Sync failed:", err.message);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Retrieve context from backend
// ─────────────────────────────────────────────────────────────────────────────

async function retrieveContext(query) {
  const project = await getSelectedProject();
  if (!project) return null;

  try {
    const result = await apiRequest("/retrieval", {
      method: "POST",
      body: JSON.stringify({
        project_id: project.id,
        query: query || "resume project context",
        top_k: 10,
      }),
    });
    return result.data;
  } catch (err) {
    console.error("[Mnemosyne] Retrieval failed:", err.message);
    return null;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Notifications
// ─────────────────────────────────────────────────────────────────────────────

async function showNotification(title, message) {
  chrome.notifications.create({
    type: "basic",
    iconUrl: "icons/icon48.png",
    title: `Mnemosyne — ${title}`,
    message,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Login
// ─────────────────────────────────────────────────────────────────────────────

async function register(email, password, full_name) {
  const baseUrl = await getApiUrl();
  const response = await fetch(`${baseUrl}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.message || "Registration failed");
  }
  return response.json();
}

async function login(email, password) {
  const baseUrl = await getApiUrl();
  const response = await fetch(`${baseUrl}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.message || "Login failed");
  }

  const data = await response.json();
  const token = data.data?.access_token;
  if (token) {
    await setStorage({ authToken: token });
  }
  return data;
}

// ─────────────────────────────────────────────────────────────────────────────
// Projects
// ─────────────────────────────────────────────────────────────────────────────

async function fetchProjects() {
  try {
    const result = await apiRequest("/projects");
    return result.data || [];
  } catch (err) {
    console.error("[Mnemosyne] Failed to fetch projects:", err.message);
    return [];
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Message listener
// ─────────────────────────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const handle = async () => {
    switch (message.type) {
      case "MESSAGES_CAPTURED":
        await syncMessagesToBackend(
          message.payload.messages,
          message.payload.url,
          message.payload.platform
        );
        sendResponse({ ok: true });
        break;

      case "RETRIEVE_CONTEXT":
        const context = await retrieveContext(message.payload?.query);
        sendResponse({ context });
        break;

      case "REGISTER":
        try {
          await register(message.payload.email, message.payload.password, message.payload.full_name);
          const result = await login(message.payload.email, message.payload.password);
          sendResponse({ ok: true, data: result });
        } catch (err) {
          sendResponse({ ok: false, error: err.message });
        }
        break;

      case "LOGIN":
        try {
          const result = await login(message.payload.email, message.payload.password);
          sendResponse({ ok: true, data: result });
        } catch (err) {
          sendResponse({ ok: false, error: err.message });
        }
        break;

      case "CREATE_PROJECT":
        try {
          const createResult = await apiRequest("/projects", {
            method: "POST",
            body: JSON.stringify(message.payload),
          });
          sendResponse({ ok: true, data: createResult.data });
        } catch (err) {
          sendResponse({ ok: false, error: err.message });
        }
        break;

      case "GET_PROJECTS":
        const projects = await fetchProjects();
        sendResponse({ projects });
        break;

      case "SELECT_PROJECT":
        await setStorage({ selectedProject: message.payload.project });
        sendResponse({ ok: true });
        break;

      case "GET_SELECTED_PROJECT":
        const project = await getSelectedProject();
        sendResponse({ project });
        break;

      case "SET_API_URL":
        await setStorage({ apiUrl: message.payload.apiUrl });
        sendResponse({ ok: true });
        break;

      case "LOGOUT":
        await setStorage({ authToken: null, selectedProject: null });
        sendResponse({ ok: true });
        break;

      default:
        sendResponse({ ok: false, error: "Unknown message type" });
    }
  };

  handle().catch((err) => {
    console.error("[Mnemosyne] Handler error:", err);
    sendResponse({ ok: false, error: err.message });
  });

  return true; // keep message channel open
});

console.info("[Mnemosyne] Background service worker started.");
