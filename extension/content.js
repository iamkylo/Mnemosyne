/**
 * content.js — Mnemosyne Chrome Extension Content Script
 *
 * Injected into supported AI platform pages. Responsibilities:
 *  1. Detect which AI platform we are on.
 *  2. Observe DOM for new conversation messages (via MutationObserver).
 *  3. Capture user and assistant messages.
 *  4. Send batches to the background service worker for sync.
 *  5. Listen for context injection commands from the popup.
 */

"use strict";

// ─────────────────────────────────────────────────────────────────────────────
// Platform detection
// ─────────────────────────────────────────────────────────────────────────────

const PLATFORMS = {
  "chatgpt.com": {
    name: "ChatGPT",
    messageSelector: "[data-message-author-role]",
    roleAttr: "data-message-author-role",
    textSelector: ".markdown",
    inputSelector: "#prompt-textarea",
  },
  "chat.openai.com": {
    name: "ChatGPT",
    messageSelector: "[data-message-author-role]",
    roleAttr: "data-message-author-role",
    textSelector: ".markdown",
    inputSelector: "#prompt-textarea",
  },
  "gemini.google.com": {
    name: "Gemini",
    messageSelector: ".query-content, .response-container",
    roleAttr: null,
    textSelector: "p, pre",
    inputSelector: "rich-textarea",
  },
  "claude.ai": {
    name: "Claude",
    messageSelector: "[data-testid='human-turn'], [data-testid='ai-turn']",
    roleAttr: "data-testid",
    textSelector: "p, pre",
    inputSelector: '[contenteditable="true"]',
  },
  "www.perplexity.ai": {
    name: "Perplexity",
    messageSelector: ".query-text, .prose",
    roleAttr: null,
    textSelector: "p",
    inputSelector: "textarea",
  },
};

const hostname = window.location.hostname;
const platform = PLATFORMS[hostname] || null;

if (!platform) {
  console.info("[Mnemosyne] Unsupported platform — content script idle.");
}

// ─────────────────────────────────────────────────────────────────────────────
// State
// ─────────────────────────────────────────────────────────────────────────────

let capturedMessages = [];
let lastSyncedCount = 0;
let syncTimer = null;
const SYNC_DEBOUNCE_MS = 3000; // wait 3s of silence before syncing

// ─────────────────────────────────────────────────────────────────────────────
// Message capture
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Scrape all visible messages from the conversation container.
 * Returns an array of { role, content, timestamp } objects.
 */
function scrapeMessages() {
  if (!platform) return [];

  const elements = document.querySelectorAll(platform.messageSelector);
  const messages = [];

  elements.forEach((el) => {
    let role = "user";

    if (platform.roleAttr) {
      const attrValue = el.getAttribute(platform.roleAttr) || "";
      if (attrValue.includes("assistant") || attrValue.includes("ai-turn") || attrValue.includes("response")) {
        role = "assistant";
      }
    } else {
      // Fallback: alternate user/assistant
      const index = Array.from(elements).indexOf(el);
      role = index % 2 === 0 ? "user" : "assistant";
    }

    const textEl = el.querySelector(platform.textSelector) || el;
    const content = textEl.innerText?.trim();

    if (content && content.length > 2) {
      messages.push({
        role,
        content,
        external_id: el.id || `msg-${messages.length}`,
        created_at: new Date().toISOString(),
      });
    }
  });

  return messages;
}

/**
 * Debounced sync — fires 3 seconds after the last DOM mutation.
 */
function scheduleSyncIfNewMessages() {
  const current = scrapeMessages();
  if (current.length <= lastSyncedCount) return;

  clearTimeout(syncTimer);
  syncTimer = setTimeout(() => {
    const newMessages = scrapeMessages();
    if (newMessages.length > lastSyncedCount) {
      capturedMessages = newMessages;
      chrome.runtime.sendMessage({
        type: "MESSAGES_CAPTURED",
        payload: {
          platform: platform.name,
          messages: newMessages,
          url: window.location.href,
          timestamp: Date.now(),
        },
      });
      lastSyncedCount = newMessages.length;
      console.info(`[Mnemosyne] Synced ${newMessages.length} messages to background.`);
    }
  }, SYNC_DEBOUNCE_MS);
}

// ─────────────────────────────────────────────────────────────────────────────
// DOM Observer
// ─────────────────────────────────────────────────────────────────────────────

const observer = new MutationObserver(() => {
  if (platform) scheduleSyncIfNewMessages();
});

observer.observe(document.body, {
  childList: true,
  subtree: true,
  characterData: true,
});

// Initial scrape on load
setTimeout(scheduleSyncIfNewMessages, 2000);

// ─────────────────────────────────────────────────────────────────────────────
// Context injection
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Inject a context string into the AI platform's input field.
 * The user must manually submit — we never auto-submit.
 */
function injectContext(contextText) {
  if (!platform) return false;

  const input = document.querySelector(platform.inputSelector);
  if (!input) {
    console.warn("[Mnemosyne] Input field not found for injection.");
    return false;
  }

  if (input.isContentEditable) {
    input.focus();
    input.innerText = contextText;
    input.dispatchEvent(new Event("input", { bubbles: true }));
  } else {
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
      window.HTMLTextAreaElement.prototype,
      "value"
    )?.set;
    if (nativeInputValueSetter) {
      nativeInputValueSetter.call(input, contextText);
      input.dispatchEvent(new Event("input", { bubbles: true }));
    } else {
      input.value = contextText;
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }
  }

  console.info("[Mnemosyne] Context injected into input field.");
  return true;
}

// ─────────────────────────────────────────────────────────────────────────────
// Message listener (from popup / background)
// ─────────────────────────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "INJECT_CONTEXT") {
    const success = injectContext(message.payload.context);
    sendResponse({ success });
  }

  if (message.type === "GET_CAPTURED_MESSAGES") {
    sendResponse({ messages: capturedMessages });
  }

  if (message.type === "SYNC_CURRENT_MESSAGES") {
    const newMessages = scrapeMessages();
    capturedMessages = newMessages;
    chrome.runtime.sendMessage({
      type: "MESSAGES_CAPTURED",
      payload: {
        platform: platform ? platform.name : "unknown",
        messages: newMessages,
        url: window.location.href,
        timestamp: Date.now(),
      },
    });
    lastSyncedCount = newMessages.length;
    sendResponse({ ok: true });
  }

  return true; // keep channel open for async sendResponse
});

console.info(`[Mnemosyne] Content script active on ${platform?.name || hostname}`);
