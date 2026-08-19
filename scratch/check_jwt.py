import asyncio
import json
import base64
import urllib.parse
from playwright.async_api import async_playwright

async def check_jwt():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://qoder.com/users/sign-in", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        await page.fill("#basic_email", "indah98@exploreabiansemal.site")
        await page.click("button:has-text('Continue')")
        await page.wait_for_timeout(3000)
        await page.fill("#basic_password", "Oc8lUPixImofM9")
        await page.click("button[type=submit], button:has-text('Continue'), button:has-text('Sign in')")
        await page.wait_for_timeout(5000)

        cookies = await context.cookies()
        for c in cookies:
            if c["name"] == "accessToken":
                token = c["value"]
                parts = token.split(".")
                if len(parts) >= 2:
                    payload_b64 = parts[1] + "=="
                    decoded = base64.urlsafe_b64decode(payload_b64).decode("utf-8", errors="ignore")
                    print("accessToken JWT payload:", json.dumps(json.loads(decoded), indent=2))
            elif c["name"] == "user":
                print("user cookie payload:", urllib.parse.unquote(c["value"]))

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_jwt())
