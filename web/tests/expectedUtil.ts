// SPDX-License-Identifier: Apache-2.0

import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const ROOT = resolve(__dirname, "../../fixtures/expected");

export function loadExpected<T>(name: string): T {
  return JSON.parse(readFileSync(resolve(ROOT, name), "utf8")) as T;
}

export function rationalFloat(entry: { rational?: [number, number]; float64?: number }): number {
  if (entry.rational) return entry.rational[0] / entry.rational[1];
  return entry.float64 ?? Number.NaN;
}
