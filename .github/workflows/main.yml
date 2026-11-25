import json
import os
from patchright.sync_api import sync_playwright

DAFTAR_AKUN = [
    {
        "nama": "ID_9",
        "url": "https://panel.jagoanssh.com/account/create/9?protocol=ssh",
        "username": "has7777",
        "password": "has7777",
    },
    {
        "nama": "ID3_19",
        "url": "https://panel.jagoanssh.com/account/create/19?protocol=ssh",
        "username": "sin7777",
        "password": "sin7777",
    },
]


def konversi_cookies(raw_json):
    samesite_map = {
        "lax": "Lax",
        "strict": "Strict",
        "no_restriction": "None",
        "none": "None",
    }
    hasil = []
    for c in json.loads(raw_json):
        if c["name"].upper() == "XSRF-TOKEN":
            continue
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


def buat_satu_akun(page, akun):
    nama = akun["nama"]
    url = akun["url"]
    username = akun["username"]
    password = akun["password"]
    respon_panel = []

    def tangkap_respon(res):
        if res.request.method == "POST" and "/cdn-cgi/" not in res.url:
            try:
                isi = res.text()[:800]
            except Exception as e:
                isi = f"Gagal baca body: {e}"
            respon_panel.append(
                {
                    "url": res.url,
                    "status": res.status,
                    "body": isi,
                }
            )

    page.on("response", tangkap_respon)

    try:
        print(f"\n========== MEMPROSES {nama} ({username}) ==========", flush=True)
        res_awal = page.goto(url, wait_until="domcontentloaded", timeout=45000)
        print(f"[{nama}] Status buka halaman: {res_awal.status if res_awal else '-'}", flush=True)

        # Tunggu form muncul (termasuk melewati verifikasi Cloudflare jika ada)
        input_user = page.locator('input[placeholder*="username" i]').first
        input_user.wait_for(state="visible", timeout=25000)

        # 1. Isi username & password
        page.wait_for_timeout(800)
        input_user.fill(username)
        page.wait_for_timeout(500)
        page.locator('input[placeholder*="password" i]').first.fill(password)
        page.wait_for_timeout(500)

        # 2. Klik pilihan durasi "Trial"
        page.get_by_text("Trial", exact=True).first.click()
        page.wait_for_timeout(1000)

        # 3. Centang kotak Terms of Service (TOS)
        checkbox = page.locator('input[type="checkbox"]').first
        if checkbox.count() > 0:
            checkbox.check(force=True)
        else:
            page.get_by_text("Terms of Service", exact=False).first.click()

        page.wait_for_timeout(800)
        page.screenshot(path=f"{nama}_1_sebelum.png", full_page=True)

        # 4. Klik tombol Create Account Now
        tombol = page.locator('button:has-text("Create Account Now")').first
        tombol.scroll_into_view_if_needed()
        tombol.click()

        # Tunggu respon server selesai
        page.wait_for_timeout(8000)
        page.screenshot(path=f"{nama}_2_sesudah.png", full_page=True)

        print(f"[{nama}] Respon POST panel:", flush=True)
        print(json.dumps(respon_panel, indent=2), flush=True)
        print(f"[{nama}] Cuplikan teks halaman:", flush=True)
        print(page.inner_text("body")[:1000], flush=True)
        return True

    except Exception as e:
        print(f"[{nama}] TERJADI ERROR: {e}", flush=True)
        try:
            page.screenshot(path=f"{nama}_error.png", full_page=True)
        except Exception:
            pass
        return False

    finally:
        page.remove_listener("response", tangkap_respon)


def main():
    cookies_env = os.environ.get("COOKIES_JSON")
    if not cookies_env:
        raise SystemExit("ERROR: Secret COOKIES_JSON belum diisi.")

    cookies = konversi_cookies(cookies_env)
    ringkasan = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="id-ID",
            timezone_id="Asia/Jakarta",
        )
        context.add_cookies(cookies)
        page = context.new_page()

        for i, akun in enumerate(DAFTAR_AKUN):
            sukses = buat_satu_akun(page, akun)
            ringkasan[akun["nama"]] = "SELESAI" if sukses else "ERROR"

            # Jeda 3 detik sebelum pindah ke server berikutnya
            if i < len(DAFTAR_AKUN) - 1:
                page.wait_for_timeout(3000)

        browser.close()

    print("\n=== RINGKASAN EKSEKUSI ===", flush=True)
    for nama, status in ringkasan.items():
        print(f"- {nama}: {status}", flush=True)


if __name__ == "__main__":
    main()
