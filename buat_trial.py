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

        def tangkap_respon(res):
            if res.request.method == "POST":
                try:
                    isi = res.text()[:1000]
                except Exception as e:
                    isi = f"Gagal baca body: {e}"
                respon_post.append(
                    {
                        "url": res.url,
                        "status": res.status,
                        "content_type": res.headers.get("content-type", "-"),
                        "server": res.headers.get("server", "-"),
                        "cf_mitigated": res.headers.get("cf-mitigated", "-"),
                        "body": isi,
                    }
                )

        page.on("response", tangkap_respon)

        try:
            print("Membuka halaman ID3 VVIP...", flush=True)
            res_awal = page.goto(URL, wait_until="domcontentloaded", timeout=45000)
            print(f"Status buka halaman: {res_awal.status if res_awal else '-'}", flush=True)
            print(f"URL sekarang: {page.url}", flush=True)

            # Tunggu kolom username muncul (maksimal 20 detik)
            input_user = page.locator('input[placeholder*="username" i]').first
            input_user.wait_for(state="visible", timeout=20000)

            # 1. Isi username & password
            input_user.fill(USERNAME)
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

            # Tunggu 6 detik agar respon POST selesai
            page.wait_for_timeout(6000)
            page.screenshot(path="2_sesudah_submit.png", full_page=True)

        except Exception as e:
            print(f"TERJADI ERROR: {e}", flush=True)
            page.screenshot(path="error_halaman.png", full_page=True)
            raise
        finally:
            print("=== DETAIL RESPON POST ===", flush=True)
            print(json.dumps(respon_post, indent=2), flush=True)
            print("=== RINGKASAN HALAMAN ===", flush=True)
            try:
                print(page.inner_text("body")[:1500], flush=True)
            except Exception:
                pass
            browser.close()
            print("Selesai dijalankan.", flush=True)


if __name__ == "__main__":
    main()
