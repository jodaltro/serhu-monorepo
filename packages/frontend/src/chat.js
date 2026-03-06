/**
 * Chat UI controller — manages the text interaction between user and Being.
 *
 * The user sends text messages, the Being responds (through the API),
 * and the visual state is refreshed after each interaction so the
 * Being's 3D form evolves in real-time.
 */

/**
 * Initialize the chat panel.
 *
 * @param {object} options
 * @param {(message: string) => Promise<{ response: string }>} options.onSend
 *   Called when the user submits a message. Must return the Being's response.
 * @param {() => void} options.onAfterSend
 *   Called after a successful send/response cycle (e.g. to refresh visual state).
 */
export function initChat({ onSend, onAfterSend }) {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const messages = document.getElementById("chat-messages");
  const submitBtn = form.querySelector("button");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    // Show user message
    appendMessage(messages, text, "user");
    input.value = "";
    submitBtn.disabled = true;

    try {
      const result = await onSend(text);
      // Show Being's response
      appendMessage(messages, result.response, "being");
      onAfterSend?.();
    } catch (err) {
      appendMessage(messages, `⚠ ${err.message}`, "being");
    } finally {
      submitBtn.disabled = false;
      input.focus();
    }
  });
}

/**
 * Update the header badge with stage info.
 * @param {string} name
 * @param {string} stage
 */
export function updateHeader(name, stage) {
  const nameEl = document.getElementById("being-name");
  const stageEl = document.getElementById("being-stage");
  if (nameEl) nameEl.textContent = name;
  if (stageEl) stageEl.textContent = stage;
}

/**
 * Append a message bubble to the chat.
 * @param {HTMLElement} container
 * @param {string} text
 * @param {"user"|"being"} role
 */
function appendMessage(container, text, role) {
  const el = document.createElement("div");
  el.className = `msg ${role}`;
  el.textContent = text;
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
}
