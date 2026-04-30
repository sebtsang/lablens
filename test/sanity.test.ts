import { describe, it, expect } from "vitest";

describe("sanity", () => {
  it("CI runs and assertions work", () => {
    expect(1 + 1).toBe(2);
  });
});
