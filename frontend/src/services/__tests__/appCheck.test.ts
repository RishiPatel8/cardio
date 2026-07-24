import { describe, it, expect, vi } from "vitest";

// Mock App Check calls
vi.mock("firebase/app-check", () => ({
  getToken: vi.fn((appCheckInstance) => {
    if (appCheckInstance === "mock_fail") {
      return Promise.reject(new Error("Token fetch failure"));
    }
    return Promise.resolve({ token: "mock_app_check_token_xyz" });
  })
}));

// Mock firebase import
vi.mock("../firebase", () => ({
  appCheck: "mock_instance"
}));

import { getAppCheckToken } from "../appCheck";

describe("Firebase App Check Service Tests", () => {
  it("should successfully retrieve the active App Check token representation", async () => {
    const token = await getAppCheckToken();
    expect(token).toBe("mock_app_check_token_xyz");
  });
});
