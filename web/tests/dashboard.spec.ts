// SPDX-License-Identifier: Apache-2.0

import { expect, test } from "@playwright/test";

const BASE = "/annotation-qa-workbench/";
const MOTA_B = 2 / 3;
const IDF1_C = 2 / 3;
const MEAN_IOU_A = 32619964 / 39538911;

test.describe("dashboard", () => {
  test("honesty strings and title", async ({ page }) => {
    await page.goto(BASE);
    await expect(page).toHaveTitle(/synthetic data/i);
    await expect(page.getByTestId("honesty-line").first()).toContainText("Synthetic data only");
    await expect(page.getByText(/does not use real robot images/)).toBeVisible();
    await expect(page.getByTestId("alpha-shift-caveat")).toBeVisible();
  });

  test("prev and next frame controls", async ({ page }) => {
    await page.goto(BASE);
    await page.getByTestId("frame-next").click();
    await expect(page.getByTestId("frame-index")).toHaveText("1");
    await page.getByTestId("frame-prev").click();
    await expect(page.getByTestId("frame-index")).toHaveText("0");
  });

  test("pairwise scores visible", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("pairwise-scores")).toBeVisible();
    await expect(page.getByTestId("pairwise-ab-mota")).not.toContainText("n/a");
  });

  test("draw GT robot box on You tab IoU 1", async ({ page }) => {
    await page.goto(BASE);
    await page.getByTestId("tab-You").click();
    const canvas = page.getByTestId("annotator-canvas");
    const box = await canvas.boundingBox();
    if (!box) throw new Error("no canvas");
    await page.mouse.move(box.x + 25, box.y + 65);
    await page.mouse.down();
    await page.mouse.move(box.x + 55, box.y + 95);
    await page.mouse.up();
    await page.getByTestId("box-form").locator('input[type="number"]').nth(0).fill("20");
    await page.getByTestId("box-form").locator('input[type="number"]').nth(1).fill("60");
    await page.getByTestId("box-form").locator('input[type="number"]').nth(2).fill("40");
    await page.getByTestId("box-form").locator('input[type="number"]').nth(3).fill("40");
    await page.getByTestId("box-form").locator("select").selectOption("robot");
    await page.getByTestId("box-form").locator('input[type="number"]').nth(4).fill("1");
    const raw = await page.getByTestId("live-robot-iou").getAttribute("data-score-raw");
    expect(Number(raw)).toBeCloseTo(1, 9);
  });

  test("annotator A mean IoU", async ({ page }) => {
    await page.goto(BASE);
    await page.getByTestId("tab-A").click();
    const raw = await page.getByTestId("score-motp_mean_iou").getAttribute("data-score-raw");
    expect(Number(raw)).toBeCloseTo(MEAN_IOU_A, 9);
  });

  test("B MOTA and C IDF1", async ({ page }) => {
    await page.goto(BASE);
    await page.getByTestId("tab-B").click();
    let raw = await page.getByTestId("score-mota").getAttribute("data-score-raw");
    expect(Number(raw)).toBeCloseTo(MOTA_B, 9);
    await page.getByTestId("tab-C").click();
    raw = await page.getByTestId("score-idf1").getAttribute("data-score-raw");
    expect(Number(raw)).toBeCloseTo(IDF1_C, 9);
  });

  test("empty You shows n/a", async ({ page }) => {
    await page.goto(BASE);
    await page.getByTestId("tab-You").click();
    await expect(page.getByTestId("score-precision")).toContainText("n/a");
    await expect(page.getByTestId("score-kappa")).toContainText("n/a");
    await expect(page.getByTestId("score-motp_mean_iou")).toContainText("n/a");
    await expect(page.getByTestId("score-mota")).toContainText("0.000000");
  });

  test("frame isolation", async ({ page }) => {
    await page.goto(BASE);
    await page.getByTestId("tab-You").click();
    const canvas = page.getByTestId("annotator-canvas");
    const box = await canvas.boundingBox();
    if (!box) throw new Error("no canvas");
    await page.mouse.move(box.x + 30, box.y + 30);
    await page.mouse.down();
    await page.mouse.move(box.x + 80, box.y + 80);
    await page.mouse.up();
    await expect(page.getByTestId("canvas-box-count")).toHaveAttribute("data-count", "1");
    await page.getByTestId("frame-next").click();
    await expect(page.getByTestId("canvas-box-count")).toHaveAttribute("data-count", "0");
  });

  test("locked GT tab does not accept draw", async ({ page }) => {
    await page.goto(BASE);
    await page.getByTestId("tab-GT").click();
    const before = await page.getByTestId("canvas-box-count").getAttribute("data-count");
    const canvas = page.getByTestId("annotator-canvas");
    const box = await canvas.boundingBox();
    if (!box || before === null) throw new Error("setup");
    await page.mouse.move(box.x + 10, box.y + 10);
    await page.mouse.down();
    await page.mouse.move(box.x + 50, box.y + 50);
    await page.mouse.up();
    await expect(page.getByTestId("canvas-box-count")).toHaveAttribute("data-count", before);
  });

  test("edit resize delete updates scores", async ({ page }) => {
    await page.goto(BASE);
    await page.getByTestId("tab-You").click();
    const canvas = page.getByTestId("annotator-canvas");
    const box = await canvas.boundingBox();
    if (!box) throw new Error("no canvas");
    await page.mouse.move(box.x + 20, box.y + 60);
    await page.mouse.down();
    await page.mouse.move(box.x + 60, box.y + 100);
    await page.mouse.up();
    await page.getByTestId("box-form").locator('input[type="number"]').nth(2).fill("5");
    await page.getByTestId("delete-box").click();
    await expect(page.getByTestId("score-mota")).toContainText("0.000000");
  });

  test("CI report panel uses JSON", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("ci-report")).toBeVisible();
    const raw = await page.getByTestId("ci-report-b-mota").getAttribute("data-score-raw");
    expect(Number(raw)).toBeCloseTo(MOTA_B, 6);
  });

  test("missing report error", async ({ page }) => {
    await page.goto(`${BASE}?reportUrl=${encodeURIComponent("/annotation-qa-workbench/missing-report.json")}`);
    await expect(page.getByTestId("ci-report-error")).toBeVisible();
  });

  test("malformed report error", async ({ page }) => {
    await page.goto(
      `${BASE}?reportUrl=${encodeURIComponent("/annotation-qa-workbench/test-reports/malformed.json")}`,
    );
    await expect(page.getByTestId("ci-report-error")).toBeVisible();
  });

  test("sample report rejected in production build", async ({ page }) => {
    await page.goto(
      `${BASE}?reportUrl=${encodeURIComponent("/annotation-qa-workbench/sample_report.json")}`,
    );
    await expect(page.getByTestId("ci-report-error")).toBeVisible();
  });

  test("screenshot for docs", async ({ page }) => {
    await page.goto(BASE);
    await page.getByTestId("tab-A").click();
    await page.screenshot({ path: "test-results/demo.png", fullPage: true });
  });
});
