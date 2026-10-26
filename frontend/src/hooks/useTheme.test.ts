import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { useTheme } from "./useTheme";

describe("useTheme", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  it("defaults to 'system' when nothing is stored", () => {
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("system");
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
  });

  it("reads a previously stored theme on mount", () => {
    localStorage.setItem("apoe-theme", "dark");
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("dark");
  });

  it("ignores a corrupted/unexpected stored value and falls back to system", () => {
    localStorage.setItem("apoe-theme", "not-a-real-theme");
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("system");
  });

  it("setTheme updates state, persists to localStorage, and sets the DOM attribute", () => {
    const { result } = renderHook(() => useTheme());

    act(() => result.current.setTheme("dark"));

    expect(result.current.theme).toBe("dark");
    expect(localStorage.getItem("apoe-theme")).toBe("dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("switching back to 'system' removes the DOM attribute", () => {
    const { result } = renderHook(() => useTheme());

    act(() => result.current.setTheme("light"));
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");

    act(() => result.current.setTheme("system"));
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
  });
});
