import { describe, it, expect, vi } from "vitest";

// Mock Firebase SDK calls
vi.mock("firebase/app", () => ({
  initializeApp: vi.fn(() => ({})),
}));

vi.mock("firebase/auth", () => ({
  getAuth: vi.fn(() => ({})),
  signInWithEmailAndPassword: vi.fn(() => Promise.resolve({ user: { uid: "test_user_123" } })),
  createUserWithEmailAndPassword: vi.fn(() => Promise.resolve({ user: { uid: "test_user_123" } })),
  signOut: vi.fn(() => Promise.resolve()),
  onAuthStateChanged: vi.fn(),
  GoogleAuthProvider: vi.fn(),
}));

vi.mock("firebase/firestore", () => ({
  getFirestore: vi.fn(() => ({})),
  doc: vi.fn(() => ({})),
  setDoc: vi.fn(() => Promise.resolve()),
  collection: vi.fn(() => ({})),
  addDoc: vi.fn(() => Promise.resolve({ id: "mock_doc_id" })),
}));

vi.mock("firebase/analytics", () => ({
  getAnalytics: vi.fn(() => ({})),
  logEvent: vi.fn(),
  isSupported: vi.fn(() => Promise.resolve(true)),
}));

vi.mock("firebase/storage", () => ({
  getStorage: vi.fn(() => ({})),
}));

vi.mock("firebase/remote-config", () => ({
  getRemoteConfig: vi.fn(() => ({})),
}));

vi.mock("firebase/app-check", () => ({
  initializeAppCheck: vi.fn(() => ({})),
  ReCaptchaEnterpriseProvider: vi.fn(),
}));

import { loginWithEmail, registerWithEmail } from "../auth";
import { syncUserProfile, syncTelemetrySummary } from "../firestore";

describe("Firebase Auth Service Tests", () => {
  it("should successfully login user with email", async () => {
    const user = await loginWithEmail("test@example.com", "password123");
    expect(user.uid).toBe("test_user_123");
  });

  it("should successfully signup user with email", async () => {
    const user = await registerWithEmail("test@example.com", "password123");
    expect(user.uid).toBe("test_user_123");
  });
});

describe("Firebase Firestore Service Tests", () => {
  it("should sync user profile without errors", async () => {
    await expect(syncUserProfile("test_user_123", { name: "John Doe" })).resolves.not.toThrow();
  });

  it("should sync telemetry summary and return document id", async () => {
    const docId = await syncTelemetrySummary("test_user_123", { avg_bpm: 72 });
    expect(docId).toBe("mock_doc_id");
  });
});
