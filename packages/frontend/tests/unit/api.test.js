import { describe, it, expect, vi, beforeEach } from "vitest";
import { createBeing, getBeing, chat, processMessage, getVisualState, sleep, wake } from "../../src/api.js";

// Shared mock setup
let lastFetchUrl;
let lastFetchOpts;
let mockResponse;

beforeEach(() => {
  lastFetchUrl = null;
  lastFetchOpts = null;
  mockResponse = { ok: true, json: async () => ({}) };

  globalThis.fetch = vi.fn(async (url, opts) => {
    lastFetchUrl = url;
    lastFetchOpts = opts;
    return mockResponse;
  });
});

describe("createBeing", () => {
  it("sends POST /beings/ with name and language", async () => {
    mockResponse = {
      ok: true,
      json: async () => ({ being_id: "abc", name: "Luna", language: "pt" }),
    };

    const result = await createBeing("Luna", "pt");

    expect(lastFetchUrl).toBe("/beings/");
    expect(lastFetchOpts.method).toBe("POST");
    expect(JSON.parse(lastFetchOpts.body)).toEqual({
      name: "Luna",
      language: "pt",
    });
    expect(result.being_id).toBe("abc");
  });

  it("defaults language to en", async () => {
    mockResponse = { ok: true, json: async () => ({}) };
    await createBeing("Nova");
    expect(JSON.parse(lastFetchOpts.body).language).toBe("en");
  });
});

describe("getBeing", () => {
  it("sends GET /beings/{id}", async () => {
    mockResponse = {
      ok: true,
      json: async () => ({ being_id: "b1", stage: "sensorimotor" }),
    };

    const result = await getBeing("b1");

    expect(lastFetchUrl).toBe("/beings/b1");
    expect(lastFetchOpts.method).toBeUndefined(); // GET is default
    expect(result.stage).toBe("sensorimotor");
  });
});

describe("chat", () => {
  it("sends POST /beings/{id}/chat with message", async () => {
    mockResponse = {
      ok: true,
      json: async () => ({ response: "...", stage: "sensorimotor" }),
    };

    const result = await chat("b1", "Hello");

    expect(lastFetchUrl).toBe("/beings/b1/chat");
    expect(lastFetchOpts.method).toBe("POST");
    const body = JSON.parse(lastFetchOpts.body);
    expect(body.message).toBe("Hello");
    expect(body.auto_traits).toBe(true);
    expect(result.response).toBe("...");
  });
});

describe("processMessage", () => {
  it("sends POST /beings/{id}/process with role and content", async () => {
    mockResponse = { ok: true, json: async () => ({ working_memory_count: 1 }) };

    await processMessage("b1", "user", "Hi");

    expect(lastFetchUrl).toBe("/beings/b1/process");
    const body = JSON.parse(lastFetchOpts.body);
    expect(body.role).toBe("user");
    expect(body.content).toBe("Hi");
  });
});

describe("getVisualState", () => {
  it("sends GET /beings/{id}/visual", async () => {
    const vs = {
      being_id: "b1",
      cognitive_stage: "sensorimotor",
      hue: 0,
      saturation: 0,
      lightness: 1,
    };
    mockResponse = { ok: true, json: async () => vs };

    const result = await getVisualState("b1");

    expect(lastFetchUrl).toBe("/beings/b1/visual");
    expect(result.cognitive_stage).toBe("sensorimotor");
    expect(result.lightness).toBe(1);
  });
});

describe("error handling", () => {
  it("throws on non-OK responses", async () => {
    mockResponse = {
      ok: false,
      status: 404,
      text: async () => "Not found",
    };

    await expect(getBeing("missing")).rejects.toThrow("API 404: Not found");
  });
});

describe("sleep", () => {
  it("sends POST /beings/{id}/sleep with params", async () => {
    mockResponse = { ok: true, json: async () => ({ is_sleeping: true }) };

    const result = await sleep("b1", { num_rollouts: 500, svd_rank: 8 });

    expect(lastFetchUrl).toBe("/beings/b1/sleep");
    expect(lastFetchOpts.method).toBe("POST");
    const body = JSON.parse(lastFetchOpts.body);
    expect(body.num_rollouts).toBe(500);
    expect(body.svd_rank).toBe(8);
    expect(result.is_sleeping).toBe(true);
  });
});

describe("wake", () => {
  it("sends POST /beings/{id}/wake with timeout", async () => {
    mockResponse = {
      ok: true,
      json: async () => ({
        facts_extracted: 2,
        beliefs_added: 1,
        hypotheses_generated: 5,
        cycles_completed: 3,
      }),
    };

    const result = await wake("b1", 15);

    expect(lastFetchUrl).toBe("/beings/b1/wake");
    expect(lastFetchOpts.method).toBe("POST");
    const body = JSON.parse(lastFetchOpts.body);
    expect(body.timeout).toBe(15);
    expect(result.cycles_completed).toBe(3);
  });
});
