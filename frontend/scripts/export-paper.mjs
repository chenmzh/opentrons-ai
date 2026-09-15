// Offline export only: does not start the console or contact the robot.
import { chromium } from "@playwright/test";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
const [input, output] = process.argv.slice(2);
if (!input || !output) {
  throw new Error(
    "Usage: node frontend/scripts/export-paper.mjs INPUT.html OUTPUT.pdf",
  );
}
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.goto(pathToFileURL(resolve(input)).href);
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({
    path: resolve(output),
    format: "A4",
    printBackground: true,
    preferCSSPageSize: true,
    displayHeaderFooter: true,
    headerTemplate: "<span></span>",
    footerTemplate:
      '<div style="width:100%;text-align:center;font-size:8px;color:#777"><span class="pageNumber"></span> / <span class="totalPages"></span></div>',
  });
  console.log(`PDF written: ${resolve(output)}`);
} finally {
  await browser.close();
}
