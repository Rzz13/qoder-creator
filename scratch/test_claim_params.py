import asyncio
import json
import uuid
from playwright.async_api import async_playwright

async def test_claim_params():
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
        print(f"Testing payloads for /api/v1/user/claim-trial with UUID={device_uuid}...")

        payloads = [
            {"deviceId": device_uuid},
            {"device_id": device_uuid},
            {"machineId": device_uuid.replace("-", "")},
            {"machine_id": device_uuid.replace("-", "")},
            {"hardwareId": device_uuid},
            {"platform": "linux"},
            {"source": "desktop"},
            {"source": "cli"},
            {"plan": "pro"},
            {"type": "trial"},
            {"deviceId": device_uuid, "source": "cli"},
            {"deviceId": device_uuid, "platform": "linux"},
            {"machineId": device_uuid, "platform": "linux"},
            {"machine_id": device_uuid, "source": "cli"},
            {}
        ]

        res = await page.evaluate(
            """async ({payloads}) => {
                const csrf = window.csrfToken || '';
                const out = [];
                for (const p of payloads) {
                    try {
                        const r = await fetch('/api/v1/user/claim-trial', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRF-TOKEN': csrf,
                                'x-requested-with': 'XMLHttpRequest'
                            },
                            credentials: 'include',
                            body: JSON.stringify(p)
                        });
                        out.push({ payload: p, status: r.status, body: await r.text() });
                    } catch (e) {
                        out.push({ payload: p, err: e.message });
                    }
                }
                return out;
            }""",
            {"payloads": payloads}
        )

        print("\nParam Test Results:")
        for r in res:
            print(f"  Payload: {r.get('payload')} -> Status {r.get('status')}: {r.get('body')}")

        # Check cookies again after test
        cookies = await context.cookies()
        for c in cookies:
            if c["name"] == "user":
                import urllib.parse
                print("\nUpdated user cookie payload:", urllib.parse.unquote(c["value"]))

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_claim_params())
