import { test, expect } from "@playwright/test";

test("register page has submit", async ({ page }) => {
  await page.goto("/register");
  await expect(page.getByRole("button", { name: "Create Account" })).toBeVisible();
});
