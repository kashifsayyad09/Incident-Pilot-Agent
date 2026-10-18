import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Globals are off, so testing-library's automatic cleanup is not registered.
afterEach(() => cleanup());
