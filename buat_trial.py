import json
import os
from playwright.sync_api import sync_playwright

URL = "https://panel.jagoanssh.com/account/create/19?protocol=ssh"
USERNAME = "tid7777"
PASSWORD = "tid7777"


def konversi_cookies(raw_json):
    samesite_map = {
        "lax": "Lax",
        "strict": "Strict",
        "no_restriction": "None",
        "none": "None",
    }
    hasil = []
    for c in json.loads(raw_json):
        item = {
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", True),
            "sameSite": samesite_map.get(str(c.get("sameSite", "lax")).lower(), "Lax"),
        }
        if not c.get("session") and c.get("expirationDate"):
            item["expires"] = int(c["expirationDate"])
        hasil.append(item)
    return hasil


def main():
    cookies_env = os.environ.get("COOKIES_JSON")
    if not cookies_env:
        raise SystemExit("ERROR: Secret COOKIES_JSON belum diisi.")

    cookies = konversi_cookies(cookies_env)
    respon_post = []

    with sync_playwright() as p:
        # Matikan tanda otomatisasi agar tidak mudah dicurigai WAF/Cloudflare
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="id-ID",
            timezone_id="Asia/Jakarta",
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        context.add_cookies(cookies)
        page = context.new_page()

        # Rekam respon POST dari server untuk melihat isi detail error 403
        def tangkap_respon(res):
            if res.request.method == "POST":
                try:
                    isi = res.text()[:800]
                except Exception as e:
                    isi = f"Gagal baca body: {e}"
                respon_post.append(
                    {
                        "url": res.url,
                        "status": res.status,
                        "server": res.headers.get("server", "-"),
                        "cf_mitigated": res.headers.get("cf-mitigated", "-"),
                        "body": isi,
                    }
                )

        page.on("response", tangkap_respon)

        print("Membuka halaman ID3 VVIP...")
        page.goto(URL, wait_until="networkidle", timeout=60000)

        if "login" in page.url.lower():
            page.screenshot(path="hasil_error_login.png", full_page=True)
            browser.close()
            raise SystemExit("GAGAL: Sesi cookie kedaluwarsa, diarahkan ke login.")

        page.wait_for_timeout(1500)

        # 1. Isi username & password tetap: tid7777
        page.locator('input[placeholder*="username" i]').first.fill(USERNAME)
        page.wait_for_timeout(400)
        page.locator('input[placeholder*="password" i]').first.fill(PASSWORD)
        page.wait_for_timeout(400)

        # 2. Klik pilihan durasi "Trial"
        page.get_by_text("Trial", exact=True).first.click()
        page.wait_for_timeout(800)

        # 3. Centang kotak Terms of Service (TOS)
        checkbox = page.locator('input[type="checkbox"]').first
        if checkbox.count() > 0:
            checkbox.check(force=True)
        else:
            page.get_by_text("Terms of Service", exact=False).first.click()

        page.wait_for_timeout(800)
        page.screenshot(path="1_sebelum_submit.png", full_page=True)

        # 4. Klik tombol Create Account Now
        tombol = page.locator('button:has-text("Create Account Now")').first
        tombol.scroll_into_view_if_needed()
        tombol.click()

        page.wait_for_timeout(5000)
        page.wait_for_load_state("networkidle")
        page.screenshot(path="2_sesudah_submit.png", full_page=True)

        print("=== DETAIL RESPON POST ===")
        for r in respon_post:
            print(json.dumps(r, indent=2))

        print("=== RINGKASAN HALAMAN ===")
        print(page.inner_text("body")[:1500])

        browser.close()
        print("Selesai dijalankan.")


if __name__ == "__main__":
    main()
