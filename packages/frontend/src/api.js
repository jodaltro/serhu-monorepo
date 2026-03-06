/**
 * API client for the SerHu REST API.
 *
 * All functions talk to the FastAPI server (proxied through Vite in dev,
 * or same-origin in production).
 */

const BASE = import.meta.env.VITE_API_BASE ?? "";

/**
 * @typedef {Object} BeingInfo
 * @property {string} being_id
 * @property {string} name
 * @property {string} language
 * @property {string} stage
 * @property {number} cognitive_age
 * @property {string} erikson_conflict
 * @property {number} interaction_count
 * @property {boolean} is_sleeping
 */

/**
 * @typedef {Object} ChatResult
 * @property {string} response
 * @property {string} being_id
 * @property {string} stage
 * @property {number} cognitive_age
 */

/**
 * @typedef {Object} VisualState
 * @property {string} being_id
 * @property {string} cognitive_stage
 * @property {number} cognitive_age
 * @property {number} hue
 * @property {number} saturation
 * @property {number} lightness
 * @property {number} alpha
 * @property {number} roundness
 * @property {number} complexity
 * @property {number} symmetry
 * @property {number} scale
 * @property {number} spikiness
 * @property {number} organic_noise
 * @property {number} pulse_rate
 * @property {number} movement_speed
 * @property {number} center_attraction
 * @property {number} glow_intensity
 * @property {number} roughness
 */

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return res.json();
}

/**
 * Create a new Being (tabula rasa).
 * @param {string} name
 * @param {string} language
 * @returns {Promise<BeingInfo>}
 */
export function createBeing(name, language = "en") {
  return request("/beings/", {
    method: "POST",
    body: JSON.stringify({ name, language }),
  });
}

/**
 * Get a Being's summary.
 * @param {string} beingId
 * @returns {Promise<BeingInfo>}
 */
export function getBeing(beingId) {
  return request(`/beings/${beingId}`);
}

/**
 * Chat with a Being (requires LLM on backend).
 * @param {string} beingId
 * @param {string} message
 * @returns {Promise<ChatResult>}
 */
export function chat(beingId, message) {
  return request(`/beings/${beingId}/chat`, {
    method: "POST",
    body: JSON.stringify({ message, auto_traits: true }),
  });
}

/**
 * Process a message manually (without LLM).
 * @param {string} beingId
 * @param {string} role
 * @param {string} content
 * @returns {Promise<Object>}
 */
export function processMessage(beingId, role, content) {
  return request(`/beings/${beingId}/process`, {
    method: "POST",
    body: JSON.stringify({ role, content }),
  });
}

/**
 * Get the visual morphogenesis state.
 * @param {string} beingId
 * @returns {Promise<VisualState>}
 */
export function getVisualState(beingId) {
  return request(`/beings/${beingId}/visual`);
}

/**
 * Consolidate working memory to long-term storage (twilight phase).
 * @param {string} beingId
 * @returns {Promise<Object>}
 */
export function consolidate(beingId) {
  return request(`/beings/${beingId}/consolidate`, { method: "POST" });
}

/**
 * Start continuous AIXI dreaming (runs until wake is called).
 * @param {string} beingId
 * @param {object} [opts]
 * @param {number} [opts.num_rollouts=1000]
 * @param {number} [opts.svd_rank=8]
 * @param {number|null} [opts.seed=null]
 * @returns {Promise<{ is_sleeping: boolean }>}
 */
export function sleep(beingId, { num_rollouts = 1000, svd_rank = 8, seed = null } = {}) {
  return request(`/beings/${beingId}/sleep`, {
    method: "POST",
    body: JSON.stringify({ num_rollouts, svd_rank, seed }),
  });
}

/**
 * Wake the Being from continuous sleep and retrieve accumulated results.
 * @param {string} beingId
 * @param {number} [timeout=30]
 * @returns {Promise<{ facts_extracted: number, beliefs_added: number, hypotheses_generated: number, cycles_completed: number }>}
 */
export function wake(beingId, timeout = 30) {
  return request(`/beings/${beingId}/wake`, {
    method: "POST",
    body: JSON.stringify({ timeout }),
  });
}
