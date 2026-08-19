import asyncio
import json
import uuid
from playwright.async_api import async_playwright

async def test_device_bind():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("Logging in...")
        await page.goto("https://qoder.com/users/sign-in", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        await page.fill("#basic_email", "indah98@exploreabiansemal.site")
        await page.click("button:has-text('Continue')")
        await page.wait_for_timeout(3000)
        await page.fill("#basic_password", "Oc8lUPixImofM9")
        await page.click("button[type=submit], button:has-text('Continue'), button:has-text('Sign in')")
        await page.wait_for_timeout(5000)

        device_id = str(uuid.uuid4())
        print(f"Testing device registration with device_id={device_id}...")

        res = await page.evaluate(
            """async ({deviceId}) => {
                const csrf = window.csrfToken || '';
                const endpoints = [
                    { url: '/api/v1/devices/bind', body: { device_id: deviceId, platform: 'linux', os: 'ubuntu' } },
                    { url: '/api/v1/devices/register', body: { device_id: deviceId, platform: 'linux' } },
                    { url: '/api/v1/user/claim-trial', body: { device_id: deviceId } },
                    { url: '/api/v1/me/claim-trial', body: { device_id: deviceId } },
                    { url: '/api/v1/trials/claim', body: { device_id: deviceId } },
                    { url: '/api/v1/subscriptions/trial', body: { device_id: deviceId } }
                ];
                const out = [];
                for (const ep of endpoints) {
                    try {
                        const r = await fetch(ep.url, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRF-TOKEN': csrf,
                                'x-requested-with': 'XMLHttpRequest'
                            },
                            credentials: 'include',
                            body: JSON.stringify(ep.body)
                        });
                        out.push({ url: ep.url, status: r.status, body: await r.text() });
                    } catch (e) {
                        out.push({ url: ep.url, err: e.message });
                    }
                }
                return out;
            }""",
            {"deviceId": device_id}
        )

        print("\nAPI Test Results:")
        for r in res:
            print(f"  {r.get('url')} -> Status {r.get('status')}: {r.get('body') or r.get('err')}")

        # Check cookies again after test
        cookies = await context.cookies()
        for c in cookies:
            if c["name"] == "user":
                import urllib.parse
                print("\nUpdated user cookie payload:", urllib.parse.unquote(c["value"]))

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_device_bind())
