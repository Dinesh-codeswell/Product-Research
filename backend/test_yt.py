import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    try:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = context.new_page()
        
        timedtext_data = []

        def on_response(response):
            if "timedtext" in response.url:
                print("INTERCEPTED timedtext:", response.url, "Status:", response.status)
                try:
                    text = response.text()
                    timedtext_data.append(text)
                    print("Timedtext length:", len(text))
                except Exception as e:
                    print("Error reading response:", e)

        page.on("response", on_response)
        
        print("Navigating to YouTube video...")
        page.goto("https://www.youtube.com/watch?v=T-Osaiyy8rk", wait_until="domcontentloaded", timeout=15000)
        time.sleep(3)
        
        # Check if transcript button is on the page
        # In YouTube, clicking "...more" then "Show transcript"
        # Or look for transcript engagement panel
        print("Page title:", page.title())
        
        # Look for transcript button
        more_btn = page.locator("button#expand, tp-yt-paper-button#expand")
        if more_btn.count() > 0:
            print("Found expand button, clicking...")
            more_btn.first.click()
            time.sleep(1)
            
        transcript_btn = page.locator("button:has-text('Show transcript'), ytd-button-renderer:has-text('Transcript')")
        if transcript_btn.count() > 0:
            print("Found transcript button, clicking...")
            transcript_btn.first.click()
            time.sleep(3)
            
        print("Intercepted timedtext responses:", len(timedtext_data))
        browser.close()
    except Exception as e:
        print("Playwright exception:", e)
