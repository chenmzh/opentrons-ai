import { expect, test, type Page } from "@playwright/test";

async function mockApi(page: Page, role = "admin") {
  let loggedIn = false;
  const hardware: Record<string, unknown>[] = [];
  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname.replace("/api/v1", "");
    const method = route.request().method();
    let data: unknown = {};
    let status = 200;
    if (path === "/login") {
      if (route.request().postDataJSON().password === "wrong") {
        status = 401;
        data = { detail: "login_failed" };
      } else {
        loggedIn = true;
        data = { username: "scientist", role, csrf: "test" };
      }
    } else if (path === "/me") {
      status = loggedIn ? 200 : 401;
      data = loggedIn
        ? { username: "scientist", role, csrf: "test" }
        : { detail: "unauthorized" };
    } else if (path === "/robot")
      data = {
        connected: true,
        checked_at: "2026-09-14T12:00:00Z",
        address: "http://robot.invalid:31950",
        health: { name: "test-robot", api_version: "26.6.0" },
        pipettes: {
          left: {
            name: "p300_multi_gen2",
            model: "p300_multi_v2.1",
            id: "pipette-1",
          },
          right: { name: null, model: null, id: null },
        },
        camera: { cameraEnabled: true },
        modules: { modules: [] },
      };
    else if (path === "/hardware" && method === "POST") {
      hardware.push({
        ...route.request().postDataJSON(),
        id: "hardware-1",
        status: "pending",
        revision: 1,
      });
      data = { id: "hardware-1" };
      status = 201;
    } else if (path === "/hardware/import") {
      for (const item of route.request().postDataJSON().items)
        hardware.push({
          ...item,
          id: "hardware-" + hardware.length,
          status: "pending",
          revision: 1,
        });
      data = { ids: hardware.map((h) => h.id) };
      status = 201;
    } else if (path.endsWith("/approve")) {
      hardware[0].status = "approved";
      hardware[0].approved_by = "scientist";
      data = { ok: true };
    } else if (path === "/hardware") data = hardware;
    else if (path === "/captures" && method === "POST") {
      status = 503;
      data = { detail: "camera_disabled" };
    } else if (path === "/captures" || path === "/audit") data = [];
    else if (path === "/users") data = [{ username: "scientist", role }];
    else if (path === "/logout") {
      loggedIn = false;
      data = { ok: true };
    }
    await route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify(data),
    });
  });
}

async function signIn(page: Page) {
  await page.goto("/");
  await page.getByLabel("用户名", { exact: true }).fill("scientist");
  await page.getByLabel("密码", { exact: true }).fill("correct-password");
  await page.getByRole("button", { name: "登录", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "实验室状态，一目了然。" }),
  ).toBeVisible();
}

test("Chinese/English switch covers navigation, persists, and preserves equipment names", async ({
  page,
}) => {
  await mockApi(page);
  await signIn(page);
  await expect(page.getByText("p300_multi_gen2")).toBeVisible();
  await page.screenshot({ path: "../runs/ui/overview-zh.png", fullPage: true });
  await page.getByRole("button", { name: "EN", exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(
    page.getByRole("heading", { name: "A clear view of your lab." }),
  ).toBeVisible();
  await expect(page.getByText("p300_multi_gen2")).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Hardware", exact: true }),
  ).toBeVisible();
  await page.screenshot({ path: "../runs/ui/overview-en.png", fullPage: true });
});

test("catalog add, explicit approval and CSV import work in both languages", async ({
  page,
}) => {
  await mockApi(page);
  await signIn(page);
  await page.getByRole("button", { name: "硬件清单", exact: true }).click();
  await page
    .getByRole("button", { name: "添加硬件", exact: true })
    .first()
    .click();
  await page.getByLabel("名称", { exact: true }).fill("测试板");
  await page.getByLabel("型号 / 加载名称").fill("plate_test");
  await page.getByRole("button", { name: "保存条目" }).click();
  await expect(page.getByRole("cell", { name: "测试板" })).toBeVisible();
  await page.getByRole("button", { name: "EN", exact: true }).click();
  await page
    .getByRole("button", { name: "Approve catalog entry", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toContainText(
    "does not qualify the equipment",
  );
  await page.getByRole("button", { name: "Confirm approval" }).click();
  await expect(
    page.getByRole("cell", { name: /Catalog approved/ }),
  ).toBeVisible();
  await page.locator("input[type=file]").setInputFiles({
    name: "inventory.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      'name,category,model,serial,notes\r\n"Tips, 300",tiprack,test_tips,,"local stock"\r\n',
    ),
  });
  await expect(page.getByRole("cell", { name: /Tips, 300/ })).toBeVisible();
});

test("camera failure is informational and does not change robot status", async ({
  page,
}) => {
  await mockApi(page);
  await signIn(page);
  await page.getByRole("button", { name: "相机", exact: true }).click();
  await page.getByRole("button", { name: "拍摄照片", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("机器人拒绝拍照");
  await page.getByRole("button", { name: "EN", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText(
    "The robot rejected the capture",
  );
  await page.getByRole("button", { name: "Overview", exact: true }).click();
  await expect(page.getByText("Connected", { exact: true })).toBeVisible();
  await expect(
    page.getByText("Protocol execution is not enabled in this release."),
  ).toBeVisible();
});

test("viewer gets observation controls only and small viewport has no horizontal overflow", async ({
  page,
}) => {
  await mockApi(page, "viewer");
  await page.setViewportSize({ width: 390, height: 844 });
  await signIn(page);
  await expect(page.getByRole("button", { name: "拍摄照片" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "团队与记录" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "退出登录" })).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.getByRole("button", { name: "硬件清单", exact: true }).click();
  await expect(page.getByRole("button", { name: "添加硬件" })).toHaveCount(0);
});

test("login errors translate without losing the form", async ({ page }) => {
  await mockApi(page);
  await page.goto("/");
  await page.getByLabel("用户名", { exact: true }).fill("scientist");
  await page.getByLabel("密码", { exact: true }).fill("wrong");
  await page.getByRole("button", { name: "登录", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("用户名或密码错误");
  await page.getByRole("button", { name: "EN", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText(
    "Incorrect username or password",
  );
  await expect(page.getByLabel("Username", { exact: true })).toHaveValue(
    "scientist",
  );
});
