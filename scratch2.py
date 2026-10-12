from playwright.sync_api import sync_playwright

html = "<html dir='rtl'><body style='font-family: Tahoma, Arial; font-size: 40px'><h1>فاتورة 123</h1></body></html>"
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(
        viewport={"width": 794, "height": 400}, device_scale_factor=1.5
    )
    page.set_content(html)
    page.screenshot(path="hello.png")
    browser.close()
    
print("saved hello.png")
