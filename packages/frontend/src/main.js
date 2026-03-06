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

// -- Setup flow (create) ---------------------------------------------------
const setupOverlay = document.getElementById("setup-overlay");
const setupForm = document.getElementById("setup-form");

// Tab switching
document.getElementById("setup-tabs").addEventListener("click", (e) => {
  const tab = e.target.closest(".tab");
  if (!tab) return;
  document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.add("hidden"));
  tab.classList.add("active");
  document.getElementById(`tab-${tab.dataset.tab}`).classList.remove("hidden");
});

setupForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const nameInput = document.getElementById("being-name-input");
  const langSelect = document.getElementById("language-select");
  const name = nameInput.value.trim();
  const language = langSelect.value;
  if (!name) return;

  const btn = setupForm.querySelector("button");
  btn.disabled = true;
  btn.textContent = "Creating…";

  try {
    const info = await api.createBeing(name, language);
    beingId = info.being_id;
    beingName = info.name;

    setupOverlay.classList.add("hidden");
    startScene(info);
  } catch (err) {
    alert(`Failed to create Being: ${err.message}`);
    btn.disabled = false;
    btn.textContent = "Give birth ✦";
  }
});

// -- Setup flow (load existing) --------------------------------------------

const loadForm = document.getElementById("load-form");

loadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const idInput = document.getElementById("being-id-input");
  const id = idInput.value.trim();
  if (!id) return;

  const btn = loadForm.querySelector("button");
  btn.disabled = true;
  btn.textContent = "Connecting…";

  try {
    const info = await api.getBeing(id);
    beingId = info.being_id;
    beingName = info.name;

    setupOverlay.classList.add("hidden");
    startScene(info);
  } catch (err) {
    alert(`Being not found: ${err.message}`);
    btn.disabled = false;
    btn.textContent = "Connect ↗";
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

  // Initialise sleep button
  initSleepButton(info.is_sleeping);

  // Copy-ID button
  const copyBtn = document.getElementById("copy-id-btn");
  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      navigator.clipboard.writeText(beingId).then(() => {
        copyBtn.textContent = "✓";
        setTimeout(() => { copyBtn.textContent = "⎘"; }, 1500);
      });
    });
  }

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

// -- Sleep button ----------------------------------------------------------

function initSleepButton(initialSleeping = false) {
  const btn = document.getElementById("sleep-btn");
  if (!btn) return;

  let isSleeping = initialSleeping;
  if (isSleeping) {
    btn.classList.add("sleeping");
    btn.title = "Wake up the Being";
  }

  // Create toast element
  const toast = document.createElement("div");
  toast.id = "sleep-toast";
  document.body.appendChild(toast);

  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 3500);
  }

  btn.addEventListener("click", async () => {
    if (!beingId) return;
    btn.disabled = true;

    if (!isSleeping) {
      // Awake → Sleep: consolidate + start continuous AIXI dreaming
      btn.classList.add("sleeping");
      btn.title = "Starting sleep…";

      try {
        await api.consolidate(beingId);
        await api.sleep(beingId, { num_rollouts: 500, svd_rank: 8 });
        isSleeping = true;
        showToast("💤 Being is now dreaming… (AIXI running continuously)");
        btn.title = "Wake up the Being";
      } catch (err) {
        showToast(`⚠ Sleep failed: ${err.message}`);
        btn.classList.remove("sleeping");
      }
    } else {
      // Sleeping → Wake: stop AIXI and retrieve results
      btn.title = "Waking up…";

      try {
        const result = await api.wake(beingId);
        isSleeping = false;
        btn.classList.remove("sleeping");

        showToast(
          `☀ Awake · ${result.cycles_completed} cycles · ${result.facts_extracted} facts · ${result.beliefs_added} beliefs`
        );

        // Refresh visual state — personality evolved during sleep
        await refreshVisualState();
        btn.title = "Put the Being to sleep (consolidate + dream)";
      } catch (err) {
        showToast(`⚠ Wake failed: ${err.message}`);
      }
    }

    btn.disabled = false;
  });
}
