import asyncio
from playwright.async_api import async_playwright

async def authorize_device():
    url = "https://qoder.com/device/selectAccounts?challenge=uawq2Jnv-KgMdXHBDgDPZrfUkC8gmbo6pUxPbvZKxMk&challenge_method=S256&nonce=64939f82-2f5c-45e6-9985-be275e2d4abd&machine_id=ac5214de-32e2-4198-8e83-e6ac6a35d7c3&client_id=e883ade2-e6e3-4d6d-adf7-f92ceff5fdcb"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("Logging in to Qoder...")
        await page.goto("https://qoder.com/users/sign-in", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        await page.fill("#basic_email", "indah98@exploreabiansemal.site")
        await page.click("button:has-text('Continue')")
        await page.wait_for_timeout(3000)
        await page.fill("#basic_password", "Oc8lUPixImofM9")
        await page.click("button[type=submit], button:has-text('Continue'), button:has-text('Sign in')")
        await page.wait_for_timeout(5000)

        print("Navigating to Device Authorization URL...")
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)

        print("Current URL:", page.url)

        # Click Authorize / Confirm / Select Account button
        buttons = await page.query_selector_all("button, a")
        for b in buttons:
            text = (await b.inner_text()).strip()
            print(f"Found button: '{text}'")
            if any(k in text.lower() for k in ["authorize", "confirm", "allow", "continue", "select", "indah98"]):
                print(f"Clicking: '{text}'...")
                await b.click()
                await page.wait_for_timeout(4000)

        await page.screenshot(path="scratch/authorize_result.png")
        print("Screenshot saved to scratch/authorize_result.png")

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(authorize_device())
