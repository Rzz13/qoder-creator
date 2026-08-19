import asyncio
from playwright.async_api import async_playwright

async def inspect_authenticated_user():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("Navigating to sign-in...")
        await page.goto("https://qoder.com/users/sign-in", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        # Fill email
        await page.fill("#basic_email", "indah98@exploreabiansemal.site")
        await page.click("button:has-text('Continue')")
        await page.wait_for_timeout(3000)

        # Fill password
        await page.fill("#basic_password", "Oc8lUPixImofM9")
        await page.click("button[type=submit], button:has-text('Continue'), button:has-text('Sign in')")
        await page.wait_for_timeout(6000)

        print("URL after login attempt:", page.url)

        # Check cookies
        cookies = await context.cookies()
        print("Session cookies count:", len(cookies))
        for c in cookies:
            print(f"  Cookie: {c['name']} = {c['value'][:15]}...")

        # Navigate to /dashboard
        await page.goto("https://qoder.com/dashboard", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        text_dashboard = await page.evaluate("() => document.body ? document.body.innerText : ''")
        print("\n--- DASHBOARD TEXT ---")
        print(text_dashboard[:2000])

        # Navigate to /account or /settings
        await page.goto("https://qoder.com/account", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        text_account = await page.evaluate("() => document.body ? document.body.innerText : ''")
        print("\n--- ACCOUNT PAGE TEXT ---")
        print(text_account[:2000])

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_authenticated_user())
