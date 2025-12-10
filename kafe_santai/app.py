from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "kafesantai"

# ====== KONEKSI DB ======
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",          # sesuaikan kalau ada password
    database="kafe_santai"
)
cursor = db.cursor(dictionary=True)


# =========================================================
#                    HALAMAN USER
# =========================================================

@app.route("/")
def home():
    kategori = request.args.get("kategori")  # bisa None

    if kategori:
        cursor.execute("SELECT * FROM menu WHERE kategori=%s", (kategori,))
    else:
        cursor.execute("SELECT * FROM menu")

    menu = cursor.fetchall()

    cart = session.get("cart", {})
    total = sum(item["harga"] * item["jumlah"] for item in cart.values())

    return render_template(
        "kafe.html",
        menu=menu,
        cart=cart,
        total=total,
        kategori=kategori
    )


@app.route("/kategori/<nama>")
def kategori(nama):
    return redirect(url_for("home", kategori=nama))


# =========================================================
#                    KERANJANG
# =========================================================

@app.route("/tambah/<int:item_id>")
def tambah(item_id):
    cart = session.get("cart", {})

    cursor.execute("SELECT * FROM menu WHERE id=%s", (item_id,))
    item = cursor.fetchone()
    if not item:
        flash("Item tidak ditemukan!", "error")
        return redirect(url_for("home"))

    key = str(item_id)
    if key in cart:
        cart[key]["jumlah"] += 1
    else:
        cart[key] = {
            "nama": item["nama"],
            "harga": item["harga"],
            "jumlah": 1
        }

    session["cart"] = cart
    flash(f"{item['nama']} ditambahkan ke keranjang ✅", "success")
    return redirect(request.referrer or url_for("home"))


@app.route("/hapus/<int:item_id>")
def hapus(item_id):
    cart = session.get("cart", {})
    key = str(item_id)

    if key in cart:
        cart.pop(key)
        session["cart"] = cart
        flash("Item dihapus dari keranjang 🗑️", "success")

    return redirect(request.referrer or url_for("home"))


# =========================================================
#                    SIMPAN PESANAN
# =========================================================

@app.route("/pesan", methods=["POST"])
def pesan():
    nama = request.form.get("nama")
    telepon = request.form.get("telepon")
    no_meja = request.form.get("no_meja")
    catatan = request.form.get("catatan")

    if not telepon.isdigit() or not no_meja.isdigit():
        flash("No. telepon & No. meja harus berupa angka!", "error")
        return redirect(url_for("home") + "#keranjang")

    cart = session.get("cart", {})
    if not cart:
        flash("Keranjang masih kosong!", "error")
        return redirect(url_for("home"))

    try:
        # simpan header order
        cursor.execute("""
            INSERT INTO orders (nama, telepon, no_meja, catatan)
            VALUES (%s, %s, %s, %s)
        """, (nama, telepon, no_meja, catatan))
        db.commit()

        order_id = cursor.lastrowid

        # simpan detail item
        for menu_id, item in cart.items():
            cursor.execute("""
                INSERT INTO order_items (order_id, menu_id, nama_menu, harga, jumlah)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                order_id,
                int(menu_id),
                item["nama"],
                item["harga"],
                item["jumlah"]
            ))

        db.commit()

        session["cart"] = {}
        flash("Pesanan berhasil disimpan ✅", "success")

    except Exception as e:
        db.rollback()
        flash(f"Terjadi kesalahan saat menyimpan pesanan: {e}", "error")

    return redirect(url_for("home"))


# =========================================================
#                    ADMIN CRUD MENU
# =========================================================

@app.route("/admin/menu")
def admin_menu_list():
    cursor.execute("SELECT * FROM menu ORDER BY kategori, nama")
    menu = cursor.fetchall()
    return render_template("admin/menu_list.html", menu=menu)


@app.route("/admin/menu/tambah", methods=["GET", "POST"])
def admin_menu_add():
    if request.method == "POST":
        nama = request.form["nama"]
        deskripsi = request.form["deskripsi"]
        harga = request.form["harga"]
        kategori = request.form["kategori"]
        gambar = request.form["gambar"].strip()

        harga_clean = harga.replace(".", "").replace(",", "").strip()
        if not harga_clean.isdigit():
            flash("Harga harus angka!", "error")
            return redirect(url_for("admin_menu_add"))

        if gambar and not (gambar.startswith("http://") or gambar.startswith("https://")):
            flash("URL gambar harus diawali http:// atau https://", "error")
            return redirect(url_for("admin_menu_add"))

        cursor.execute("""
            INSERT INTO menu (nama, deskripsi, harga, kategori, gambar)
            VALUES (%s, %s, %s, %s, %s)
        """, (nama, deskripsi, int(harga_clean), kategori, gambar))
        db.commit()

        flash("Menu berhasil ditambahkan ✅", "success")
        return redirect(url_for("admin_menu_list"))

    return render_template("admin/menu_add.html")


@app.route("/admin/menu/edit/<int:menu_id>", methods=["GET", "POST"])
def admin_menu_edit(menu_id):
    cursor.execute("SELECT * FROM menu WHERE id=%s", (menu_id,))
    item = cursor.fetchone()

    if not item:
        flash("Menu tidak ditemukan!", "error")
        return redirect(url_for("admin_menu_list"))

    if request.method == "POST":
        nama = request.form["nama"]
        deskripsi = request.form["deskripsi"]
        harga = request.form["harga"]
        kategori = request.form["kategori"]
        gambar = request.form["gambar"].strip()

        harga_clean = harga.replace(".", "").replace(",", "").strip()
        if not harga_clean.isdigit():
            flash("Harga harus angka!", "error")
            return redirect(url_for("admin_menu_edit", menu_id=menu_id))

        if gambar and not (gambar.startswith("http://") or gambar.startswith("https://")):
            flash("URL gambar harus diawali http:// atau https://", "error")
            return redirect(url_for("admin_menu_edit", menu_id=menu_id))

        cursor.execute("""
            UPDATE menu
            SET nama=%s, deskripsi=%s, harga=%s, kategori=%s, gambar=%s
            WHERE id=%s
        """, (nama, deskripsi, int(harga_clean), kategori, gambar, menu_id))
        db.commit()

        flash("Menu berhasil diupdate ✨", "success")
        return redirect(url_for("admin_menu_list"))

    return render_template("admin/menu_edit.html", item=item)


@app.route("/admin/menu/hapus/<int:menu_id>")
def admin_menu_delete(menu_id):
    cursor.execute("DELETE FROM menu WHERE id=%s", (menu_id,))
    db.commit()
    flash("Menu berhasil dihapus 🗑️", "success")
    return redirect(url_for("admin_menu_list"))


# =========================================================
#                    ADMIN LIHAT PESANAN
# =========================================================

@app.route("/admin/orders")
def admin_orders_list():
    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cursor.fetchall()
    return render_template("admin/orders_list.html", orders=orders)


@app.route("/admin/orders/<int:order_id>")
def admin_orders_detail(order_id):
    cursor.execute("SELECT * FROM orders WHERE id=%s", (order_id,))
    order = cursor.fetchone()

    if not order:
        flash("Pesanan tidak ditemukan!", "error")
        return redirect(url_for("admin_orders_list"))

    cursor.execute("SELECT * FROM order_items WHERE order_id=%s", (order_id,))
    items = cursor.fetchall()
    total = sum(i["harga"] * i["jumlah"] for i in items)

    return render_template(
        "admin/orders_detail.html",
        order=order,
        items=items,
        total=total
    )


# =========================================================
if __name__ == "__main__":
    app.run(debug=True)
