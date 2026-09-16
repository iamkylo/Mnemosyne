/**
 * popup.js — Mnemosyne Extension Popup Controller
 *
 * Manages the popup UI:
 *  - Checks authentication state on open.
 *  - Handles login/logout.
 *  - Loads and selects projects.
 *  - Triggers context retrieval and display.
 *  - Sends context injection command to content script.
 */

"use strict";

// ─────────────────────────────────────────────────────────────────────────────
// DOM refs
// ─────────────────────────────────────────────────────────────────────────────

const $viewLogin   = document.getElementById("view-login");
const $viewMain    = document.getElementById("view-main");
const $formLogin   = document.getElementById("form-login");
const $inputEmail  = document.getElementById("input-email");
const $inputPwd    = document.getElementById("input-password");
const $loginError  = document.getElementById("login-error");
const $btnLogin    = document.getElementById("btn-login");
const $btnLogout   = document.getElementById("btn-logout");

const $authTitle   = document.getElementById("auth-title");
const $formSignup  = document.getElementById("form-signup");
const $inputSignupName = document.getElementById("input-signup-name");
const $inputSignupEmail = document.getElementById("input-signup-email");
const $inputSignupPwd = document.getElementById("input-signup-password");
const $signupError = document.getElementById("signup-error");
const $btnSignup   = document.getElementById("btn-signup");
const $linkToSignup = document.getElementById("link-to-signup");
const $linkToLogin = document.getElementById("link-to-login");

const $selectProject  = document.getElementById("select-project");
const $btnRefreshProj = document.getElementById("btn-refresh-projects");
const $btnNewProject  = document.getElementById("btn-new-project");
const $createForm     = document.getElementById("create-project-form");
const $inputProjName  = document.getElementById("input-project-name");
const $inputProjId    = document.getElementById("input-project-id");
const $btnCreateProj  = document.getElementById("btn-create-project");
const $btnCancelCreate = document.getElementById("btn-cancel-create");
const $createProjError = document.getElementById("create-project-error");
const $syncStatus     = document.getElementById("sync-status");

const $sectionCtx      = document.getElementById("section-context");
const $contextPreview  = document.getElementById("context-preview");
const $btnInject       = document.getElementById("btn-inject");
const $btnCopy         = document.getElementById("btn-copy");
const $btnRefreshCtx   = document.getElementById("btn-refresh-context");

const $capturePlatform = document.getElementById("capture-platform");
const $captureCount    = document.getElementById("capture-count");

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function sendBg(msg) {
  return new Promise((resolve) => chrome.runtime.sendMessage(msg, resolve));
}

function showStatus(text, type = "info") {
  $syncStatus.textContent = text;
  $syncStatus.className = `status-banner ${type}`;
  $syncStatus.style.display = "block";
}

function hideStatus() {
  $syncStatus.style.display = "none";
}

function setLoginError(msg) {
  $loginError.textContent = msg;
  $loginError.style.display = msg ? "block" : "none";
}

function setSignupError(msg) {
  $signupError.textContent = msg;
  $signupError.style.display = msg ? "block" : "none";
}

// ─────────────────────────────────────────────────────────────────────────────
// State transitions
// ─────────────────────────────────────────────────────────────────────────────

function showLogin() {
  $viewLogin.style.display = "block";
  $viewMain.style.display = "none";
  $btnLogout.style.display = "none";
}

function showMain() {
  $viewLogin.style.display = "none";
  $viewMain.style.display = "block";
  $btnLogout.style.display = "inline-block";
}

// ─────────────────────────────────────────────────────────────────────────────
// Initialisation
// ─────────────────────────────────────────────────────────────────────────────

async function init() {
  // Check auth
  const { authToken } = await new Promise((r) => chrome.storage.local.get(["authToken"], r));
  if (authToken) {
    showMain();
    await loadProjects();
    await restoreSelectedProject();
    await updateCaptureStatus();
  } else {
    showLogin();
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Projects
// ─────────────────────────────────────────────────────────────────────────────

async function loadProjects() {
  showStatus("Loading projects…", "info");
  const { projects } = await sendBg({ type: "GET_PROJECTS" });
  $selectProject.innerHTML = '<option value="">— Select a project —</option>';
  (projects || []).forEach((proj) => {
    const opt = document.createElement("option");
    opt.value = proj.id;
    opt.textContent = proj.name;
    opt.dataset.project = JSON.stringify(proj);
    $selectProject.appendChild(opt);
  });
  hideStatus();
}

async function restoreSelectedProject() {
  const { project } = await sendBg({ type: "GET_SELECTED_PROJECT" });
  if (project) {
    $selectProject.value = project.id;
    await loadContext(project);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Context
// ─────────────────────────────────────────────────────────────────────────────

async function loadContext(project) {
  showStatus("Retrieving memory context…", "info");
  $sectionCtx.style.display = "none";

  const { context } = await sendBg({
    type: "RETRIEVE_CONTEXT",
    payload: { query: `resume work on ${project.name}` },
  });

  if (context && context.context) {
    $contextPreview.value = context.context;
    $sectionCtx.style.display = "block";
    showStatus(`Context ready — ${context.memories?.length || 0} memories loaded`, "success");
    setTimeout(hideStatus, 3000);
  } else {
    $contextPreview.value = "";
    showStatus("No memory context found for this project yet.", "info");
    setTimeout(hideStatus, 3000);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Capture status
// ─────────────────────────────────────────────────────────────────────────────

async function updateCaptureStatus() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;

  try {
    const response = await chrome.tabs.sendMessage(tab.id, { type: "GET_CAPTURED_MESSAGES" });
    if (response && response.messages) {
      const hostname = new URL(tab.url).hostname;
      $capturePlatform.textContent = `Platform: ${hostname}`;
      $captureCount.textContent = `Messages captured: ${response.messages.length}`;
    }
  } catch {
    $capturePlatform.textContent = "Platform: not an AI page";
    $captureCount.textContent = "Messages captured: 0";
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Event handlers
// ─────────────────────────────────────────────────────────────────────────────

$linkToSignup.addEventListener("click", (e) => {
  e.preventDefault();
  $formLogin.style.display = "none";
  $formSignup.style.display = "block";
  $authTitle.textContent = "Sign up for Mnemosyne";
  setLoginError("");
  setSignupError("");
});

$linkToLogin.addEventListener("click", (e) => {
  e.preventDefault();
  $formSignup.style.display = "none";
  $formLogin.style.display = "block";
  $authTitle.textContent = "Sign in to Mnemosyne";
  setLoginError("");
  setSignupError("");
});

$formSignup.addEventListener("submit", async (e) => {
  e.preventDefault();
  setSignupError("");
  $btnSignup.disabled = true;
  $btnSignup.textContent = "Signing up…";

  const { ok, error } = await sendBg({
    type: "REGISTER",
    payload: { 
      email: $inputSignupEmail.value, 
      password: $inputSignupPwd.value,
      full_name: $inputSignupName.value || undefined
    },
  });

  $btnSignup.disabled = false;
  $btnSignup.textContent = "Sign Up";

  if (ok) {
    showMain();
    await loadProjects();
    await updateCaptureStatus();
  } else {
    setSignupError(error || "Registration failed. Check your details.");
  }
});

$formLogin.addEventListener("submit", async (e) => {
  e.preventDefault();
  setLoginError("");
  $btnLogin.disabled = true;
  $btnLogin.textContent = "Signing in…";

  const { ok, error } = await sendBg({
    type: "LOGIN",
    payload: { email: $inputEmail.value, password: $inputPwd.value },
  });

  $btnLogin.disabled = false;
  $btnLogin.textContent = "Sign In";

  if (ok) {
    showMain();
    await loadProjects();
    await updateCaptureStatus();
  } else {
    setLoginError(error || "Login failed. Check your credentials.");
  }
});

$btnLogout.addEventListener("click", async () => {
  await sendBg({ type: "LOGOUT" });
  showLogin();
});

$btnRefreshProj.addEventListener("click", loadProjects);

// ── Create project toggle ──

$btnNewProject.addEventListener("click", () => {
  $createForm.style.display = $createForm.style.display === "none" ? "block" : "none";
  $inputProjName.value = "";
  $inputProjId.value = "";
  $createProjError.style.display = "none";
  if ($createForm.style.display === "block") $inputProjName.focus();
});

$btnCancelCreate.addEventListener("click", () => {
  $createForm.style.display = "none";
});

// Auto-generate slug from name
$inputProjName.addEventListener("input", () => {
  if (!$inputProjId.dataset.manual) {
    $inputProjId.value = $inputProjName.value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
  }
});

$inputProjId.addEventListener("input", () => {
  $inputProjId.dataset.manual = "true";
});

$btnCreateProj.addEventListener("click", async () => {
  const name = $inputProjName.value.trim();
  const id = $inputProjId.value.trim() || name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  if (!name) {
    $createProjError.textContent = "Project name is required.";
    $createProjError.style.display = "block";
    return;
  }

  $btnCreateProj.disabled = true;
  $btnCreateProj.textContent = "Creating…";
  $createProjError.style.display = "none";

  const { ok, data, error } = await sendBg({
    type: "CREATE_PROJECT",
    payload: { id, name },
  });

  $btnCreateProj.disabled = false;
  $btnCreateProj.textContent = "Create";

  if (ok && data) {
    $createForm.style.display = "none";
    await loadProjects();
    // Auto-select the newly created project
    $selectProject.value = data.id;
    await sendBg({ type: "SELECT_PROJECT", payload: { project: data } });
    await loadContext(data);
    showStatus(`Project "${data.name}" created!`, "success");
    setTimeout(hideStatus, 3000);
  } else {
    $createProjError.textContent = error || "Failed to create project.";
    $createProjError.style.display = "block";
  }
});

$selectProject.addEventListener("change", async () => {
  const selected = $selectProject.options[$selectProject.selectedIndex];
  if (!selected.dataset.project) return;
  const project = JSON.parse(selected.dataset.project);
  await sendBg({ type: "SELECT_PROJECT", payload: { project } });
  await loadContext(project);

  // Force sync current page messages
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.tabs.sendMessage(tabs[0].id, { type: "SYNC_CURRENT_MESSAGES" }).catch(() => {});
    }
  });
});

$btnRefreshCtx.addEventListener("click", async () => {
  const { project } = await sendBg({ type: "GET_SELECTED_PROJECT" });
  if (project) await loadContext(project);
});

$btnInject.addEventListener("click", async () => {
  let context = $contextPreview.value;

  // If context is empty, try to refresh it first
  if (!context) {
    const selected = $selectProject.options[$selectProject.selectedIndex];
    if (selected && selected.dataset.project) {
      const project = JSON.parse(selected.dataset.project);
      
      // Try to force sync any un-synced messages from the active tab first
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab) {
        try {
          const resp = await chrome.tabs.sendMessage(tab.id, { type: "GET_CAPTURED_MESSAGES" });
          if (resp && resp.messages && resp.messages.length > 0) {
            showStatus("Syncing local messages to backend...", "info");
            await sendBg({ type: "MESSAGES_CAPTURED", payload: { messages: resp.messages, url: tab.url } });
          }
        } catch (e) {
          // ignore if not a supported page
        }
      }

      showStatus("Fetching latest context...", "info");
      await loadContext(project);
      context = $contextPreview.value;
    }
  }

  if (!context) {
    showStatus("No context available. Chat to capture memories, then try again.", "error");
    setTimeout(hideStatus, 4000);
    return;
  }

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;

  try {
    const response = await chrome.tabs.sendMessage(tab.id, {
      type: "INJECT_CONTEXT",
      payload: { context },
    });
    if (response?.success) {
      showStatus("Context injected! Review and submit.", "success");
      setTimeout(hideStatus, 4000);
    } else {
      showStatus("Could not inject — navigate to an AI chat page first.", "error");
    }
  } catch {
    showStatus("Injection failed — open a supported AI page first.", "error");
  }
});

$btnCopy.addEventListener("click", async () => {
  const context = $contextPreview.value;
  if (context) {
    await navigator.clipboard.writeText(context);
    const orig = $btnCopy.textContent;
    $btnCopy.textContent = "✓ Copied";
    setTimeout(() => ($btnCopy.textContent = orig), 2000);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Boot
// ─────────────────────────────────────────────────────────────────────────────

init();
