import asyncio
from playwright.async_api import async_playwright

async def verify_theme_icons():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 800})
        await page.goto("http://localhost:8501", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # 1. Capture Light mode button
        btn = page.locator(".st-key-d_theme_toggle_btn button")
        await btn.wait_for(state="visible", timeout=10000)
        box = await btn.bounding_box()
        print(f"Light mode button box: {box}")

        # Capture navbar header
        header = page.locator(".st-key-dmx_master_header_card")
        await header.screenshot(path="light_mode_header_verified.png")
        await btn.screenshot(path="light_mode_moon_verified.png")

        # 2. Click to toggle to Dark Mode
        await btn.click()
        await page.wait_for_timeout(3000)

        # Capture Dark mode button
        btn_dark = page.locator(".st-key-d_theme_toggle_btn button")
        box_dark = await btn_dark.bounding_box()
        print(f"Dark mode button box: {box_dark}")
        await header.screenshot(path="dark_mode_header_verified.png")
        await btn_dark.screenshot(path="dark_mode_sun_verified.png")

        # 3. Click again to return to Light mode
        await btn_dark.click()
        await page.wait_for_timeout(2500)
        await browser.close()

asyncio.run(verify_theme_icons())
