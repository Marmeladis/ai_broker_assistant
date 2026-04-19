from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(
        "https://www.moex.com/ru/bondization/calendar",
        wait_until="domcontentloaded"
    )
    page.wait_for_timeout(5000)

    body_text = page.locator("body").inner_text()

    print("TITLE:", page.title())
    print("HAS TATN:", "TATN" in body_text)
    print("HAS LKOH:", "LKOH" in body_text)
    print("HAS Татнефть:", "Татнефть" in body_text)
    print("HAS Лукойл:", "Лукойл" in body_text)
    print("HAS Дата покупки под дивиденды:", "Дата покупки под дивиденды" in body_text)
    print()
    print(body_text[:5000])

    browser.close()