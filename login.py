import os
import pickle
import csv
from playwright.sync_api import sync_playwright
from time import sleep
from datetime import datetime
import random
from fake_useragent import UserAgent

# Inisialisasi UserAgent
ua = UserAgent()

def save_cookies(page, email):
    cookies = page.context.cookies()
    with open(f'cookies/{email}.pkl', 'wb') as file:
        pickle.dump(cookies, file)
    print(f"{email} : Cookie di simpan {email}.pkl'")

def delete_old_cookies(email):
    cookie_file = f'cookies/{email}.pkl'
    if os.path.exists(cookie_file):
        os.remove(cookie_file)
        print(f"Cookies lama untuk {email} dihapus.")

def type_like_human(page, element, text):
    """Mengisi elemen dengan teks seolah-olah diketik oleh manusia"""
    for char in text:
        element.type(char)
        sleep(random.uniform(0.1, 0.3))  # Penundaan acak antara 100ms hingga 300ms

def login(page, email, password):
    page.goto("https://www.pinterest.com/login/")
    sleep(2)

    email_field = page.locator('input[name="id"]')
    password_field = page.locator('input[name="password"]')
    
    # Ketik email dan password seolah-olah manusia yang mengetik
    type_like_human(page, email_field, email)
    type_like_human(page, password_field, password)
    
    page.locator('//button[@type="submit"]').click()

    sleep(5)

def check_account_disabled(page, email):
    try:
        # Periksa apakah elemen role="alertdialog" ada
        alert_dialog = page.locator("//*[@role='alertdialog']")
        # Jika ada, ambil teks dari elemen <h1> di dalam alert dialog
        h1_text = alert_dialog.locator("h1").text_content()
        return f"Login gagal: {h1_text}"
    except:
        return None

def update_csv_status(email, status):
    # Membaca file CSV dan memperbarui kolom 'Keterangan'
    with open('akun.csv', mode='r') as file:
        reader = csv.reader(file)
        rows = list(reader)

    # Mencari email dan mengupdate status login di kolom 'Keterangan'
    for row in rows:
        if row[0] == email:
            if row[2] == "":  # Hanya update jika kolom 'Keterangan' kosong
                row[2] = status
                break

    # Menyimpan kembali file CSV dengan data yang sudah diperbarui
    with open('akun.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)    

def main():
    try:
        if not os.path.exists('cookies'):
            os.makedirs('cookies')

        with open('akun.csv', mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            accounts = list(reader)

        total_accounts = len(accounts)
        processed_accounts = 0

        with sync_playwright() as p:
            for account in accounts:
                email, password, keterangan = account

                # Periksa apakah kolom 'Keterangan' sudah terisi, jika ya, lanjutkan ke akun berikutnya
                if keterangan != "":
                    print(f"Skipping {email}, sudah ada keterangan.")
                    processed_accounts += 1
                    continue

                # Hapus cookies lama sebelum login
                delete_old_cookies(email)

                # Pilih user agent palsu (desktop) menggunakan fake_useragent
                user_agent = ua.random
                
                # Pastikan user agent bukan mobile
                while 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent:
                    user_agent = ua.random

                browser = p.chromium.launch(headless=True)  # Set to False to see the browser
                context = browser.new_context(user_agent=user_agent)
                page = context.new_page()

                # Mulai proses login
                print(f"==================================================")
                print(f"{email} : Sedang Di Proses")
                login(page, email, password)

                # Periksa apakah login gagal (account disabled)
                status = check_account_disabled(page, email)
                if status:
                    # Jika login gagal, perbarui CSV dengan alasan kegagalan
                    update_csv_status(email, status)
                    print(f"{email} : {status}")
                else:
                    # Jika login berhasil, perbarui CSV dengan status login berhasil
                    update_csv_status(email, "Login Berhasil")
                    print(f"{email} : Berhasil Login")
                    sleep(5)
                    # Simpan cookies hanya jika login berhasil
                    save_cookies(page, email)
                    sleep(5)

                # Jeda 60 detik sebelum melanjutkan ke akun berikutnya
                browser.close()                
                print(f"Jeda 60 detik sebelum login akun berikutnya...")
                sleep(60)                

                processed_accounts += 1
                # Notifikasi setelah setiap akun diproses
                print(f"{processed_accounts}/{total_accounts} akun diproses.")

        # Notifikasi setelah semua akun selesai diproses
        print("Semua akun telah selesai diproses!")

        # Menunggu pengguna menekan tombol Enter sebelum keluar
        input("Tekan Enter untuk keluar...")

    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    main()
