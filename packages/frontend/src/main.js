/**
 * SerHu Frontend — main entry point.
 *
 * Ties together the Three.js scene, the Being renderer, the chat UI,
 * and the API client. The flow is:
 *
 * 1. User creates a Being via the setup form.
 * 2. Three.js scene initialises with a cosmic starfield.
 * 3. Being appears as a white glowing point (tabula rasa).
 * 4. User sends text → API returns Being's response + updates visual state.
 * 5. Being's 3D form evolves in real-time based on personality morphogenesis.
 */

import { initScene } from "./scene.js";
import { createBeing as createBeingMesh } from "./being.js";
import { initChat, updateHeader } from "./chat.js";
import * as api from "./api.js";

// -- State -----------------------------------------------------------------
let beingId = null;
let beingName = "";
let being = null; // { update, animate, mesh }
let sceneCtx = null; // { scene, camera, renderer }

// -- Setup flow ------------------------------------------------------------
const setupOverlay = document.getElementById("setup-overlay");
const setupForm = document.getElementById("setup-form");

setupForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const nameInput = document.getElementById("being-name-input");
  const langSelect = document.getElementById("language-select");
  const name = nameInput.value.trim();
  const language = langSelect.value;
  if (!name) return;

  // Disable form while creating
  const btn = setupForm.querySelector("button");
  btn.disabled = true;
  btn.textContent = "Creating…";

  try {
    const info = await api.createBeing(name, language);
    beingId = info.being_id;
    beingName = info.name;

    // Hide setup, start scene
    setupOverlay.classList.add("hidden");
    startScene(info);
  } catch (err) {
    alert(`Failed to create Being: ${err.message}`);
    btn.disabled = false;
    btn.textContent = "Give birth ✦";
  }
});

// -- Scene bootstrap -------------------------------------------------------

async function startScene(info) {
  const container = document.getElementById("canvas-container");

  // Initialise Three.js
  sceneCtx = initScene(container);
  being = createBeingMesh(sceneCtx.scene);

  // Fetch initial visual state and apply
  try {
    const vs = await api.getVisualState(beingId);
    being.update(vs);
    updateHeader(beingName, vs.cognitive_stage);
  } catch {
    // If API fails, Being just stays as default white point
    updateHeader(beingName, info.stage);
  }

  // Initialise chat
  initChat({
    onSend: async (message) => {
      // Try chat first (LLM), fall back to process
      try {
        return await api.chat(beingId, message);
      } catch {
        // No LLM available: use manual process and return placeholder
        await api.processMessage(beingId, "user", message);
        return { response: "✦" };
      }
    },
    onAfterSend: refreshVisualState,
  });

  // Start render loop
  const clock = { start: performance.now() / 1000 };
  function loop() {
    requestAnimationFrame(loop);
    const time = performance.now() / 1000 - clock.start;
    being.animate(time);
    sceneCtx.renderer.render(sceneCtx.scene, sceneCtx.camera);
  }
  loop();
}

// -- Visual state refresh --------------------------------------------------

async function refreshVisualState() {
  if (!beingId || !being) return;
  try {
    const vs = await api.getVisualState(beingId);
    being.update(vs);
    updateHeader(beingName, vs.cognitive_stage);
  } catch {
    // Silently ignore — Being keeps last known state
  }
}
