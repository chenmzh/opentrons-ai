// Manual integration check. Default is observation only; flags explicitly opt into
// local inventory discovery and the OT-2 camera. Never issues motion commands.
import { readFile } from "node:fs/promises";
import { chromium } from "@playwright/test";

const credentials = await readFile(
  new URL("../../.local/bootstrap-admin.txt", import.meta.url),
  "utf8",
);
const username = credentials.match(/^Username: (.+)$/m)?.[1];
const password = credentials.match(/^Password: (.+)$/m)?.[1];
if (!username || !password)
  throw new Error("Missing local bootstrap credentials");
const browser = await chromium.launch();
try {
  const page = await browser.newPage({
    ignoreHTTPSErrors: true,
    viewport: { width: 1440, height: 1000 },
  });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("https://127.0.0.1:8443");
  await page.getByLabel("用户名", { exact: true }).fill(username);
  await page.getByLabel("密码", { exact: true }).fill(password);
  await page.getByRole("button", { name: "登录", exact: true }).click();
  await page.getByRole("heading", { name: "实验室状态，一目了然。" }).waitFor();
  const status = await page.evaluate(async () =>
    (await fetch("/api/v1/robot")).json(),
  );
  console.log(
    JSON.stringify({ connected: status.connected, robot: status.health?.name }),
  );
  if (process.argv.includes("--discover")) {
    await page.getByRole("button", { name: "硬件清单", exact: true }).click();
    const discovery = page.waitForResponse((response) =>
      response.url().endsWith("/hardware/discover"),
    );
    await page.getByRole("button", { name: "发现移液器", exact: true }).click();
    if (!(await discovery).ok()) throw new Error("Pipette discovery failed");
  }
  if (process.argv.includes("--capture")) {
    await page.getByRole("button", { name: "相机", exact: true }).click();
    const capture = page.waitForResponse(
      (response) =>
        response.url().endsWith("/captures") &&
        response.request().method() === "POST",
      { timeout: 60000 },
    );
    await page.getByRole("button", { name: "拍摄照片", exact: true }).click();
    const result = await capture;
    if (!result.ok()) throw new Error(`Capture failed: ${result.status()}`);
    console.log(JSON.stringify({ capture: await result.json() }));
    await page.locator(".camera-large img").waitFor();
    await page.screenshot({
      path: "../runs/ui/live-camera-zh.png",
      fullPage: true,
    });
  }
  await page.getByRole("button", { name: "总览", exact: true }).click();
  await page.screenshot({
    path: "../runs/ui/live-overview-zh.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "EN", exact: true }).click();
  await page
    .getByRole("heading", { name: "A clear view of your lab." })
    .waitFor();
  await page.screenshot({
    path: "../runs/ui/live-overview-en.png",
    fullPage: true,
  });
  if (errors.length) throw new Error(errors.join("\n"));
  console.log("Live UI check passed. No browser runtime errors.");
} finally {
  await browser.close();
}
