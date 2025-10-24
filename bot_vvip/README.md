# Bot Telegram VVIP dengan Mini Apps

Bot Telegram ini dirancang untuk mengelola langganan channel VVIP secara otomatis. Dilengkapi dengan sistem pembayaran, approval, dan dashboard Mini App untuk admin.

## ✨ Fitur Utama

- **Menu User Lengkap**: Tombol `/start` yang dinamis, menampilkan opsi relevan bagi user biasa dan user VVIP.
- **Alur Pembelian VVIP**: Proses pembelian yang mudah, mulai dari pemilihan durasi, pembayaran via QRIS, hingga konfirmasi.
- **Sistem Approval**: Owner dapat menyetujui atau menolak bukti pembayaran langsung dari channel approval khusus.
- **Akses Channel VVIP**: User yang disetujui otomatis mendapatkan akses ke semua channel VVIP.
- **Panel Owner Lengkap**: Serangkaian command untuk mengelola channel, harga, teks, dan URL.
- **Mini Apps Dashboard**: Dashboard web interaktif untuk statistik, manajemen user, dan pengaturan bot (hanya bisa diakses oleh owner).
- **Sistem Otomatis**:
    - **Auto Ban**: Otomatis mengeluarkan member dari channel setelah langganan berakhir.
    - **Notifikasi Expired**: Mengirim pengingat H-5 hingga H-1 sebelum langganan habis.
    - **Auto Backup**: Backup database otomatis setiap 6 jam dan dikirim ke owner.
- **Keamanan**: Proteksi konten channel dan validasi akses dashboard menggunakan Telegram `initData`.

## 📂 Struktur File

```
bot_vvip/
├── bot.py                # File utama bot Telegram
├── database.py           # Handler untuk interaksi database SQLite
├── backup.py             # Handler untuk proses backup & restore
├── mini_app/
│   ├── app.py            # Server Flask untuk Mini App
│   ├── templates/
│   │   └── dashboard.html  # Halaman dashboard
│   ├── static/             # Aset statis (CSS, JS, gambar)
│   └── utils.py          # Fungsi utilitas (e.g., validasi initData)
├── database.db           # Database SQLite
├── backups/              # Folder untuk menyimpan file backup
├── .env                  # File konfigurasi environment variables
├── requirements.txt      # Daftar dependensi Python
└── .gitignore            # File yang diabaikan oleh Git
```

## 🚀 Setup & Instalasi

1.  **Clone repository ini:**
    ```bash
    git clone <url_repository>
    cd bot_vvip
    ```

2.  **Buat dan aktifkan virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependensi yang dibutuhkan:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Konfigurasi Environment Variables:**
    Salin file `.env.example` (jika ada) atau buat file baru bernama `.env` dan isi dengan konfigurasi Anda.
    ```ini
    BOT_TOKEN=your_bot_token
    OWNER_ID=your_owner_id
    APPROVAL_CHANNEL_ID=channel_id
    MINI_APP_URL=http://localhost:5000
    MINI_APP_SECRET=random_secret_key
    BACKUP_PASSWORD=optional_backup_password
    ```

## ▶️ Menjalankan Bot & Mini App

-   **Menjalankan Bot Telegram:**
    ```bash
    python3 bot.py
    ```

-   **Menjalankan Server Mini App:**
    ```bash
    python3 mini_app/app.py
    ```
    Pastikan URL di `.env` (MINI_APP_URL) sesuai dengan alamat server Anda.

## ⚙️ Command Owner

-   `/addchvip [channel_id/username]` - Tambah channel VVIP.
-   `/rmchvip [channel_id/username]` - Hapus channel VVIP.
-   `/setharga [amount]` - Set harga per bulan.
-   `/setqris [telegraph_url]` - Set URL QRIS Telegraph.
-   `/setstarttext [text]` - Set teks `/start` (support markdown & placeholder: `{name}`, `{id}`).
-   `/setapprovalch [channel_id]` - Set channel untuk approval.
-   `/setbantuanurl [url]` - Set URL tombol bantuan.
-   `/protect [on/off]` - Aktifkan/nonaktifkan protect content channel.
-   `/listuser` - List semua user VIP aktif.
-   `/broadcast` - Kirim broadcast.
-   `/dashboard` - Buka Mini Apps Dashboard.
-   `/backup` - Backup manual database.
-   `/restore` - Restore database (reply file .zip backup).
-   `/extend <user_id|@username> <days>` - Perpanjang masa aktif VVIP user.
-   `/reduce <user_id|@username> <days>` - Kurangi masa aktif VVIP user.

## ☁️ Deploy ke VPS (Ubuntu dengan systemd)

Agar bot dan mini app berjalan 24/7, gunakan `systemd` untuk menjalankannya sebagai service.

### 1. Persiapan di VPS

-   Pastikan Anda sudah melakukan semua langkah di bagian **Setup & Instalasi**.
-   Pastikan `OWNER_ID` dan `BOT_TOKEN` di file `.env` sudah benar.
-   Ubah `MINI_APP_URL` di `.env` menjadi URL publik VPS Anda, contoh: `http://123.45.67.89:5000`.

### 2. Buat Service untuk Bot Telegram

1.  **Buat file service systemd:**
    ```bash
    sudo nano /etc/systemd/system/bot_vvip.service
    ```

2.  **Isi dengan konfigurasi berikut:**
    *(Sesuaikan `WorkingDirectory` dan `ExecStart` dengan path absolut ke project Anda)*

    ```ini
    [Unit]
    Description=Telegram VVIP Bot
    After=network.target

    [Service]
    # Ganti 'your_user' dengan username non-root Anda
    User=your_user
    Group=your_user
    WorkingDirectory=/home/your_user/bot_vvip
    ExecStart=/home/your_user/bot_vvip/venv/bin/python3 bot.py
    Restart=always
    RestartSec=5s

    [Install]
    WantedBy=multi-user.target
    ```

### 3. Buat Service untuk Mini App

1.  **Buat file service systemd:**
    ```bash
    sudo nano /etc/systemd/system/mini_app.service
    ```

2.  **Isi dengan konfigurasi berikut:**
    *(Sesuaikan `WorkingDirectory` dan `ExecStart`)*

    ```ini
    [Unit]
    Description=VVIP Bot Mini App (Flask)
    After=network.target

    [Service]
    # Ganti 'your_user' dengan username non-root Anda
    User=your_user
    Group=your_user
    WorkingDirectory=/home/your_user/bot_vvip
    ExecStart=/home/your_user/bot_vvip/venv/bin/python3 mini_app/app.py
    Restart=always
    RestartSec=5s

    [Install]
    WantedBy=multi-user.target
    ```

### 4. Jalankan dan Aktifkan Services

1.  **Reload daemon systemd:**
    ```bash
    sudo systemctl daemon-reload
    ```

2.  **Mulai kedua service:**
    ```bash
    sudo systemctl start bot_vvip.service
    sudo systemctl start mini_app.service
    ```

3.  **Aktifkan agar otomatis berjalan saat reboot:**
    ```bash
    sudo systemctl enable bot_vvip.service
    sudo systemctl enable mini_app.service
    ```

4.  **Cek status service:**
    ```bash
    sudo systemctl status bot_vvip.service
    sudo systemctl status mini_app.service
    ```
    Pastikan statusnya `active (running)`.

### 5. (Opsional) Konfigurasi Nginx sebagai Reverse Proxy

Untuk keamanan dan kemudahan akses (misalnya menggunakan domain), disarankan menggunakan Nginx.

1.  **Install Nginx:**
    ```bash
    sudo apt update
    sudo apt install nginx
    ```

2.  **Buat file konfigurasi Nginx:**
    ```bash
    sudo nano /etc/nginx/sites-available/mini_app
    ```

3.  **Isi dengan konfigurasi berikut:**
    *(Ganti `your_domain.com` dengan domain atau IP VPS Anda)*

    ```nginx
    server {
        listen 80;
        server_name your_domain.com;

        location / {
            proxy_pass http://127.0.0.1:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    ```

4.  **Aktifkan konfigurasi:**
    ```bash
    sudo ln -s /etc/nginx/sites-available/mini_app /etc/nginx/sites-enabled
    sudo nginx -t  # Test konfigurasi
    sudo systemctl restart nginx
    ```
    Sekarang Mini App Anda bisa diakses melalui port 80 (HTTP) tanpa perlu menuliskan port `:5000`. Jangan lupa mengubah `MINI_APP_URL` di `.env` menjadi `http://your_domain.com`.
