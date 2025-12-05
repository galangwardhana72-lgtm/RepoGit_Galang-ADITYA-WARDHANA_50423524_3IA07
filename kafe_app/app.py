from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)

app.secret_key = 'kafe_santai_secret_key'

# --- KONEKSI DATABASE (untuk menyimpan pesanan ke tabel orders) ---
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="kafe_santai"
)
cursor = db.cursor()

# --- DATA MENU (saat ini disimpan di memory, belum dari database) ---
menu_items = [
    {
        "id": 1,
        "nama": "Cafe Latte",
        "kategori": "Kopi",
        "harga": 38000,
        "deskripsi": "Espresso dengan susu steamed yang lembut",
        "gambar": "https://i.pinimg.com/1200x/32/58/39/32583955510da20a6abdb21eb9aa7e7d.jpg"
    },
    {
        "id": 2,
        "nama": "Croissant",
        "kategori": "Makanan",
        "harga": 28000,
        "deskripsi": "Pastry renyah dengan lapisan mentega",
        "gambar": "https://i.pinimg.com/1200x/fb/5a/7b/fb5a7b4a04fe90e7ad03b98c79d6e836.jpg"
    },
    {
        "id": 3,
        "nama": "Club Sandwich",
        "kategori": "Makanan",
        "harga": 45000,
        "deskripsi": "Sandwich lezat dengan isian lengkap",
        "gambar": "https://i.pinimg.com/1200x/e0/a5/f1/e0a5f1cbdf1b36a93e959d39fdc750b8.jpg"
    },
    {
        "id": 4,
        "nama": "Chocolate Cake",
        "kategori": "Dessert",
        "harga": 42000,
        "deskripsi": "Kue cokelat lembut dengan topping manis",
        "gambar": "https://i.pinimg.com/1200x/a5/18/b9/a518b9540ee9ad9556080abbbb8cd036.jpg"
    },

    {
        "id": 5,
        "nama": "Americano",
        "kategori": "Kopi",
        "harga": 30000,
        "deskripsi": "Espresso dicampur dengan air panas untuk rasa ringan",
        "gambar": "https://i.pinimg.com/1200x/ba/27/79/ba27796402ffd51ea7382743077175d1.jpg"
    },
    {
        "id": 6,
        "nama": "Caramel Macchiato",
        "kategori": "Kopi",
        "harga": 42000,
        "deskripsi": "Kopi susu manis dengan sentuhan karamel lembut",
        "gambar": "https://i.pinimg.com/1200x/4a/8b/e1/4a8be1181973982ef71aca416448ff5e.jpg"
    },
    {
        "id": 7,
        "nama": "Mochaccino",
        "kategori": "Kopi",
        "harga": 40000,
        "deskripsi": "Perpaduan espresso, cokelat, dan susu lembut",
        "gambar": "https://i.pinimg.com/736x/f8/56/1e/f8561ea80e14bd1989b4fe87736e1468.jpg"
    },

    {
        "id": 8,
        "nama": "Pasta Carbonara",
        "kategori": "Makanan",
        "harga": 48000,
        "deskripsi": "Pasta creamy dengan saus keju dan smoked beef",
        "gambar": "https://i.pinimg.com/1200x/0d/7f/83/0d7f831ad3e7a6ee3b65927f72783cb4.jpg"
    },
    {
        "id": 9,
        "nama": "French Fries",
        "kategori": "Makanan",
        "harga": 25000,
        "deskripsi": "Kentang goreng renyah disajikan dengan saus spesial",
        "gambar": "https://i.pinimg.com/736x/7b/7a/4a/7b7a4ad672b6146c6c278cf6c596e3da.jpg"
    },

    {
        "id": 10,
        "nama": "Cheesecake",
        "kategori": "Dessert",
        "harga": 45000,
        "deskripsi": "Kue lembut dengan lapisan keju dan krim yang manis",
        "gambar": "https://i.pinimg.com/1200x/b6/17/11/b617119f80f0be27897d512495fdc367.jpg"
    },
    {
        "id": 11,
        "nama": "Pancake",
        "kategori": "Dessert",
        "harga": 30000,
        "deskripsi": "Pancake lembut dengan topping buah",
        "gambar": "https://i.pinimg.com/736x/9d/48/d9/9d48d96c13fef025fc08a7e1786c142f.jpg"
    }
]


@app.route('/kategori/<nama>')
def kategori(nama):
    """
    Halaman kategori:
    - Menampilkan menu yang hanya sesuai kategori (Kopi / Makanan / Dessert).
    - Tetap membawa data keranjang & total untuk panel kanan.
    """
    cart = session.get('cart', {})
    total = sum(item['harga'] * item['jumlah'] for item in cart.values()) if cart else 0

    # Filter menu berdasarkan kategori yang dipilih
    filtered = [m for m in menu_items if m['kategori'] == nama]

    return render_template(
        'kafe.html',
        menu=filtered,
        cart=cart,
        total=total,
        kategori=nama   # dipakai di template untuk menandai tombol kategori aktif
    )


@app.route('/')
def home():
    cart = session.get('cart', {})
    total = sum(item['harga'] * item['jumlah'] for item in cart.values()) if cart else 0

    return render_template(
        'kafe.html',
        menu=menu_items,
        cart=cart,
        total=total,
        kategori=None    # tidak ada filter kategori → tombol 'Semua' aktif
    )


@app.route("/tambah/<int:item_id>")
def tambah(item_id):
    cart = session.get("cart", {})
    item_id_str = str(item_id)  # key di session gunakan string

    if item_id_str not in cart:
        # Cari item di list menu_items berdasarkan id
        for item in menu_items:
            if item["id"] == item_id:
                cart[item_id_str] = {
                    "nama": item["nama"],
                    "harga": item["harga"],
                    "jumlah": 1
                }
                break
    else:
        cart[item_id_str]["jumlah"] += 1

    # Simpan kembali ke session
    session["cart"] = cart

    # Balik ke halaman sebelumnya; jika tidak ada, fallback ke home
    return redirect(request.referrer or url_for('home'))


@app.route("/hapus/<int:item_id>")
def hapus(item_id):
    """
    Hapus 1 jenis item dari keranjang berdasarkan id.
    """
    cart = session.get("cart", {})
    cart.pop(str(item_id), None)    # aman meskipun id tidak ada
    session["cart"] = cart

    # Balik ke halaman sebelumnya; jika tidak ada, fallback ke home
    return redirect(request.referrer or url_for('home'))


@app.route('/pesan', methods=['POST'])
def pesan():
    """
    Proses form pemesanan:
    - Ambil data nama, telepon, no_meja, catatan.
    - Simpan ke database.
    - Kosongkan keranjang.
    - Tampilkan flash message sukses / error.
    """
    nama = request.form['nama']
    telepon = request.form['telepon']
    no_meja = request.form['no_meja']
    catatan = request.form.get('catatan', '')

    # Validasi: No. Telepon & No. Meja harus hanya angka
    if not telepon.isdigit() or not no_meja.isdigit():
        flash("❌ No. Telepon dan No. Meja harus berupa angka.", "error")
        return redirect(url_for('home'))


    # Simpan pesanan ke database
    try:
        cursor.execute(
            "INSERT INTO orders (nama, telepon, no_meja, catatan) VALUES (%s, %s, %s, %s)",
            (nama, telepon, no_meja, catatan)
        )
        db.commit()
    except Exception as e:
        # Kalau ada error DB, log ke console dan kirim flash error ke user
        print("Database error:", e)
        flash("❌ Terjadi kesalahan saat menyimpan pesanan.", "error")
        return redirect(url_for('home'))

    # Hapus keranjang setelah berhasil pesan
    session.pop('cart', None)

    # Kirim flash message sukses
    flash(f"✅ Terima kasih, {nama}! Pesanan kamu sudah disimpan.", "success")

    # Redirect untuk mencegah error 405 saat user refresh
    return redirect(url_for('home'))


if __name__ == '__main__':
    # debug=True mempermudah melihat error saat development
    app.run(debug=True)
