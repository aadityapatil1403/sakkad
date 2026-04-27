import { describe, it, expect, vi, beforeEach } from "vitest";
import { getHealth, getGallery, uploadCapture, generateCopy, generateImage } from "../lib/api";
import { mockCapture } from "./fixtures";

const BASE_URL = "http://127.0.0.1:8000";

beforeEach(() => {
  vi.stubEnv("VITE_BACKEND_URL", BASE_URL);
  vi.restoreAllMocks();
});

describe("getHealth", () => {
  it("calls /api/health and returns response", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: "ok" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await getHealth();
    expect(result.status).toBe("ok");
    expect(mockFetch).toHaveBeenCalledWith(
      `${BASE_URL}/api/health`,
      expect.objectContaining({
        headers: expect.objectContaining({
          "ngrok-skip-browser-warning": "true",
        }),
      }),
    );
  });
});

describe("getGallery", () => {
  it("calls /api/gallery with ngrok header and returns captures", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [mockCapture],
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await getGallery();
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe(mockCapture.id);
    expect(mockFetch).toHaveBeenCalledWith(
      `${BASE_URL}/api/gallery`,
      expect.objectContaining({
        headers: expect.objectContaining({
          "ngrok-skip-browser-warning": "true",
        }),
      }),
    );
  });

  it("throws ApiError on non-ok response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 503 }),
    );
    await expect(getGallery()).rejects.toMatchObject({ status: 503 });
  });
});

describe("uploadCapture", () => {
  it("sends FormData to /api/capture without manual Content-Type", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockCapture,
    });
    vi.stubGlobal("fetch", mockFetch);

    const file = new File(["img"], "test.jpg", { type: "image/jpeg" });
    await uploadCapture(file);

    const [url, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${BASE_URL}/api/capture`);
    expect(options.body).toBeInstanceOf(FormData);
    // Must NOT manually set Content-Type — browser sets multipart boundary
    expect(
      (options.headers as Record<string, string>)["Content-Type"],
    ).toBeUndefined();
  });

  it("passes session_id in FormData when provided", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockCapture,
    });
    vi.stubGlobal("fetch", mockFetch);

    const file = new File(["img"], "test.jpg", { type: "image/jpeg" });
    await uploadCapture(file, "session-xyz");

    const [, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    const fd = options.body as FormData;
    expect(fd.get("session_id")).toBe("session-xyz");
  });
});

describe("generateCopy", () => {
  it("sends capture_ids and kind to /api/generate", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        kind: "creative_summary",
        text: "Austere material philosophy.",
        fallback_used: false,
        source: { capture_ids: ["id-1"] },
      }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await generateCopy("creative_summary", {
      capture_ids: ["id-1"],
    });
    expect(result.kind).toBe("creative_summary");
    expect(result.text).toBe("Austere material philosophy.");

    const [url, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${BASE_URL}/api/generate`);
    const body = JSON.parse(options.body as string) as Record<string, unknown>;
    expect(body.kind).toBe("creative_summary");
    expect(body.capture_ids).toEqual(["id-1"]);
  });
});

describe("generateImage", () => {
  const mockImageResponse = {
    image_b64: "abc123",
    mime_type: "image/png",
    statement: "Austere material philosophy.",
    taxonomy_influences: [{ label: "Quiet Luxury", score: 0.87 }],
  };

  it("sends statement and capture_ids to /api/generate/image", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockImageResponse,
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await generateImage("Austere material philosophy.", ["id-1", "id-2"]);
    expect(result.image_b64).toBe("abc123");
    expect(result.mime_type).toBe("image/png");

    const [url, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${BASE_URL}/api/generate/image`);
    const body = JSON.parse(options.body as string) as Record<string, unknown>;
    expect(body.statement).toBe("Austere material philosophy.");
    expect(body.capture_ids).toEqual(["id-1", "id-2"]);
  });

  it("includes ngrok header", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockImageResponse,
    });
    vi.stubGlobal("fetch", mockFetch);

    await generateImage("test", ["id-1"]);
    const [, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect((options.headers as Record<string, string>)["ngrok-skip-browser-warning"]).toBe("true");
  });

  it("throws ApiError on non-ok response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 503 }));
    await expect(generateImage("test", ["id-1"])).rejects.toMatchObject({ status: 503 });
  });

  it("preserves mime_type from response", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ ...mockImageResponse, mime_type: "image/jpeg" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await generateImage("test", ["id-1"]);
    expect(result.mime_type).toBe("image/jpeg");
  });
});
