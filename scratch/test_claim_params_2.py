import asyncio
import json
import uuid
from playwright.async_api import async_playwright

async def test_claim_methods():
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

        device_uuid = str(uuid.uuid4())
        print(f"Testing methods & keys for /api/v1/user/claim-trial...")

        tests = [
            {"method": "GET", "url": "/api/v1/user/claim-trial", "body": None},
            {"method": "POST", "url": "/api/v1/user/claim-trial", "body": {"code": ""}},
            {"method": "POST", "url": "/api/v1/user/claim-trial", "body": {"token": "pt-0nXJtn4hJx5NI8fY3mO5wOwL_01a017f0-cb12-72dc-8d0b-43812f739985"}},
            {"method": "POST", "url": "/api/v1/user/claim-trial", "body": {"plan_id": "pro"}},
            {"method": "POST", "url": "/api/v1/user/claim-trial", "body": {"plan_id": "trial"}},
            {"method": "POST", "url": "/api/v1/user/claim-trial", "body": {"device_info": {"device_id": device_uuid, "platform": "linux"}}},
            {"method": "POST", "url": "/api/v1/user/claim-trial", "body": {"deviceInfo": {"deviceId": device_uuid, "platform": "linux"}}},
            {"method": "POST", "url": "/api/v1/user/claim-trial", "body": {"device": {"id": device_uuid}}},
            {"method": "POST", "url": "/api/v1/user/claim-trial", "body": {"fingerprint": device_uuid}},
        ]

        res = await page.evaluate(
            """async ({tests}) => {
                const csrf = window.csrfToken || '';
                const out = [];
                for (const t of tests) {
                    try {
                        const opts = {
                            method: t.method,
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRF-TOKEN': csrf,
                                'x-requested-with': 'XMLHttpRequest'
                            },
                            credentials: 'include'
                        };
                        if (t.body) opts.body = JSON.stringify(t.body);
                        const r = await fetch(t.url, opts);
                        out.push({ test: t, status: r.status, body: await r.text() });
                    } catch (e) {
                        out.push({ test: t, err: e.message });
                    }
                }
                return out;
            }""",
            {"tests": tests}
        )

        print("\nMethod & Key Test Results:")
        for r in res:
            print(f"  {r.get('test')} -> Status {r.get('status')}: {r.get('body')}")

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_claim_methods())
