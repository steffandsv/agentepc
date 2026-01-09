from playwright.sync_api import sync_playwright, expect

def verify_panel():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the panel
        page.goto("http://localhost:8000")

        # Verify title
        expect(page).to_have_title("Agent Control Panel")

        # Verify Task Control section
        expect(page.get_by_text("Task Control")).to_be_visible()

        # Verify Start/Stop buttons
        start_btn = page.locator("#start-btn")
        stop_btn = page.locator("#stop-btn")
        expect(start_btn).to_be_visible()
        expect(start_btn).to_be_enabled()
        expect(stop_btn).to_be_visible()
        expect(stop_btn).to_be_disabled()

        # Type a task
        page.locator("#task-input").fill("Go to google.com and search for AI")

        # Take a screenshot
        page.screenshot(path="verification/panel_initial.png")

        browser.close()

if __name__ == "__main__":
    verify_panel()
