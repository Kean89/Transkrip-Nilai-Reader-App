import hmac
import io
import re
import sqlite3

import pandas as pd
import streamlit as st
from PIL import Image, ImageOps


st.set_page_config(
    page_title="Transkrip Nilai Reader",
    page_icon="logo_transkrip.png",
    layout="wide",
)


USERS = {
    "672023030@student.uksw.edu": {"password": "123456789", "nama": "Julius"},
}

DB_PATH = "transkrip_nilai.db"

st.markdown(
    """
    <style>
    .main { background-color: #121212; }
    .stApp { background-color: #121212; }
    .stButton>button {
        width: 100%; border-radius: 8px; font-weight: bold;
        background: #212121 !important; color: #ffffff !important;
        border: 1px solid #333333 !important; padding: 0.6rem 1rem; transition: 0.3s;
    }
    .stButton>button:hover {
        background: #2d2d2d !important; border-color: #555555 !important;
        transform: translateY(-2px);
    }
    .announcement-box {
        background-color: #e0f2fe; color: #0369a1; padding: 12px 20px;
        border-radius: 6px; border-left: 5px solid #0284c7;
        font-weight: 500; margin-bottom: 15px;
    }
    .success-box {
        background-color: #dcfce7; color: #15803d; padding: 12px 20px;
        border-radius: 6px; border-left: 5px solid #16a34a;
        font-weight: bold; margin-bottom: 15px;
    }
    .warning-box {
        background-color: #fef9c3; color: #854d0e; padding: 15px 20px;
        border-radius: 6px; border-left: 5px solid #ca8a04;
        margin-bottom: 15px; line-height: 1.6;
    }
    .form-header {
        background-color: #1f2937; padding: 10px 15px;
        border-top-left-radius: 8px; border-top-right-radius: 8px;
        font-weight: bold; color: white; border-bottom: 2px solid #374151;
        font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.5px;
    }
    .badge-req { color: #ef4444; font-weight: bold; }
    .btn-custom-submit button {
        background: #00838f !important; color: white !important;
        font-weight: bold !important; border-radius: 4px !important;
        padding: 0.5rem 1.5rem !important;
    }
    .btn-custom-submit button:hover { background: #006064 !important; }
    </style>
""",
    unsafe_allow_html=True,
)



def cek_login(email: str, password: str) -> bool:
    user = USERS.get(email.strip().lower())
    if not user:
        return False
    return hmac.compare_digest(user["password"], password)


def halaman_login():
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown("## 🎓 Transkrip Nilai Reader")
        st.markdown("Silakan login menggunakan email kampus Anda.")
        with st.form("form_login"):
            email = st.text_input("Email", placeholder="nim@student.uksw.edu")
            password = st.text_input("Password", type="password")
            masuk = st.form_submit_button("Login")
        if masuk:
            if cek_login(email, password):
                email_ok = email.strip().lower()
                st.session_state["logged_in"] = True
                st.session_state["user_email"] = email_ok
                st.session_state["user_nama"] = USERS[email_ok]["nama"]
                st.session_state["user_nim"] = email_ok.split("@")[0]
                st.rerun()
            else:
                st.error("❌ Email atau password salah.")


if not st.session_state.get("logged_in"):
    halaman_login()
    st.stop()

USER_NIM = st.session_state["user_nim"]
USER_NAMA = st.session_state["user_nama"]



def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS mahasiswa_profil (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT, nim TEXT, jurusan TEXT, universitas TEXT, ipk TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS mata_kuliah (
            id INTEGER PRIMARY KEY AUTOINCREMENT, mahasiswa_id INTEGER,
            kode_mk TEXT, nama_mk TEXT, sks TEXT, nilai TEXT,
            FOREIGN KEY (mahasiswa_id) REFERENCES mahasiswa_profil(id) ON DELETE CASCADE
        )""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS pendaftaran_ttu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nim TEXT, nama TEXT, prodi TEXT, peminatan TEXT,
            ttu_ambil TEXT, status TEXT, judul TEXT,
            pembimbing1 TEXT, pembimbing2 TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS pendaftaran_review (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nim TEXT, nama TEXT, prodi TEXT, peminatan TEXT,
            judul TEXT, pembimbing1 TEXT, pembimbing2 TEXT,
            reviewer1 TEXT, reviewer2 TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS pendaftaran_yudisium (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS pendaftaran_sarasehan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status_pendaftaran TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS permohonan_surat_kp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instansi TEXT, alamat TEXT, ditujukan TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS pendaftaran_kp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nim TEXT, nama TEXT, matakuliah_kp TEXT, tempat_kp TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.commit()
    conn.close()


init_db()


def _jalankan(sql: str, params: tuple = (), pesan_error: str = "Gagal menyimpan data"):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(sql, params)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"{pesan_error}: {e}")
        return False


def simpan_ke_database(mhs: dict, mk_list: list[dict]):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO mahasiswa_profil (nama, nim, jurusan, universitas, ipk) VALUES (?,?,?,?,?)",
            (mhs.get("nama", "-"), mhs.get("nim", "-"), mhs.get("jurusan", "-"),
             mhs.get("universitas", "-"), str(mhs.get("ipk", "-"))),
        )
        mhs_id = cur.lastrowid
        cur.executemany(
            "INSERT INTO mata_kuliah (mahasiswa_id, kode_mk, nama_mk, sks, nilai) VALUES (?,?,?,?,?)",
            [(mhs_id, m["kode"], m["nama_mk"], str(m["sks"]), str(m["nilai"])) for m in mk_list],
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan ke database: {e}")
        return False


def simpan_ttu(nim, nama, prodi, peminatan, ttu_list, status, judul, pemb1, pemb2):
    return _jalankan(
        """INSERT INTO pendaftaran_ttu
           (nim, nama, prodi, peminatan, ttu_ambil, status, judul, pembimbing1, pembimbing2)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (nim, nama, prodi, peminatan, ", ".join(ttu_list), status, judul, pemb1, pemb2),
        "Gagal menyimpan data TTU",
    )


def simpan_review(nim, nama, prodi, peminatan, judul, pemb1, pemb2, rev1, rev2):
    return _jalankan(
        """INSERT INTO pendaftaran_review
           (nim, nama, prodi, peminatan, judul, pembimbing1, pembimbing2, reviewer1, reviewer2)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (nim, nama, prodi, peminatan, judul, pemb1, pemb2, rev1, rev2),
        "Gagal menyimpan data Review",
    )


def simpan_yudisium():
    return _jalankan("INSERT INTO pendaftaran_yudisium DEFAULT VALUES",
                     pesan_error="Gagal menyimpan data Yudisium")


def simpan_sarasehan(status):
    return _jalankan("INSERT INTO pendaftaran_sarasehan (status_pendaftaran) VALUES (?)",
                     (status,), "Gagal menyimpan data Sarasehan")


def simpan_surat_kp(instansi, alamat, ditujukan):
    return _jalankan(
        "INSERT INTO permohonan_surat_kp (instansi, alamat, ditujukan) VALUES (?,?,?)",
        (instansi, alamat, ditujukan), "Gagal menyimpan surat KP",
    )


def simpan_kp(nim, nama, mk_list, tempat):
    return _jalankan(
        "INSERT INTO pendaftaran_kp (nim, nama, matakuliah_kp, tempat_kp) VALUES (?,?,?,?)",
        (nim, nama, ", ".join(mk_list), tempat), "Gagal menyimpan pendaftaran KP",
    )


# =====================================================================
# ANALISIS TRANSKRIP LOKAL (TANPA API / AI)
# =====================================================================
GRADE = r"(?:A-|AB|A|B\+|B-|BC|B|C\+|C|D\+|D|E|T)"
RE_KODE = re.compile(
    rf"^\s*(?:\d{{1,3}}[.)]?\s+)?"
    rf"(?P<kode>[A-Z]{{2,6}}[ \-]?\d{{2,5}}[A-Z]?)\s+"
    rf"(?P<nama>.+?)\s+(?P<sks>\d{{1,2}})\s+(?P<nilai>{GRADE})(?=\s|$)"
)
RE_NOKODE = re.compile(
    rf"^\s*(?:\d{{1,3}}[.)]?\s+)?"
    rf"(?P<nama>[A-Za-z][A-Za-z0-9 &/,.()\-]+?)\s+(?P<sks>\d{{1,2}})\s+(?P<nilai>{GRADE})(?=\s|$)"
)
SKIP_PREFIX = ("jumlah", "total", "ipk", "indeks", "semester", "sks", "program", "nama", "nim")

BOBOT = {"A": 4.0, "A-": 3.75, "AB": 3.5, "B+": 3.5, "B": 3.0, "B-": 2.75,
         "BC": 2.5, "C+": 2.5, "C": 2.0, "D+": 1.5, "D": 1.0, "E": 0.0}


def ocr_gambar(img: Image.Image) -> str:
    """OCR lokal dengan Tesseract. Gambar diperkecil & dijadikan grayscale agar cepat."""
    import pytesseract

    img = ImageOps.exif_transpose(img).convert("L")
    img = ImageOps.autocontrast(img)
    maks = 2200
    if max(img.size) > maks:
        rasio = maks / max(img.size)
        img = img.resize((int(img.width * rasio), int(img.height * rasio)))
    try:
        return pytesseract.image_to_string(img, lang="ind+eng", config="--oem 1 --psm 6")
    except pytesseract.TesseractError:
        return pytesseract.image_to_string(img, lang="eng", config="--oem 1 --psm 6")


def ekstrak_teks(file_bytes: bytes, ext: str) -> str:
    if ext in ("png", "jpg", "jpeg"):
        return ocr_gambar(Image.open(io.BytesIO(file_bytes)))

    import pdfplumber

    teks = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if len(t.strip()) < 30:  # kemungkinan hasil scan -> OCR
                t = ocr_gambar(page.to_image(resolution=200).original)
            teks.append(t)
    return "\n".join(teks)


def _cari(pola: str, teks: str, flags=re.IGNORECASE) -> str:
    m = re.search(pola, teks, flags)
    return m.group(1).strip() if m else "-"


def parse_profil(teks: str) -> dict:
    universitas = "-"
    for line in teks.splitlines()[:15]:
        if re.search(r"universitas|institut|politeknik|sekolah tinggi", line, re.IGNORECASE):
            universitas = line.strip()
            break
    return {
        "nama": _cari(r"\bNama(?:\s+Mahasiswa)?\s*[:\-]\s*([^\n]+)", teks),
        "nim": _cari(r"\b(?:NIM|N\.I\.M)\s*[:\-]?\s*(\d{6,12})", teks),
        "jurusan": _cari(r"(?:Program\s+Studi|Prodi|Jurusan)\s*[:\-]\s*([^\n]+)", teks),
        "universitas": universitas,
        "ipk": _cari(r"(?:IPK|Indeks\s+Prestasi\s+Kumulatif|GPA)[^\d\n]{0,30}(\d[.,]\d{1,2})", teks).replace(",", "."),
    }


def parse_matakuliah(teks: str) -> list[dict]:
    hasil = []
    for line in teks.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if len(line) < 6:
            continue
        m = RE_KODE.match(line)
        kode = None
        if m:
            kode = m.group("kode")
        else:
            m = RE_NOKODE.match(line)
        if not m:
            continue
        nama = m.group("nama").strip(" .-")
        if nama.lower().startswith(SKIP_PREFIX):
            continue
        hasil.append({
            "kode": kode or "-",
            "nama_mk": nama,
            "sks": m.group("sks"),
            "nilai": m.group("nilai"),
        })
    return hasil


def hitung_ipk(mk_list: list[dict]) -> str:
    total_sks, total_mutu = 0, 0.0
    for mk in mk_list:
        bobot = BOBOT.get(str(mk["nilai"]).upper())
        try:
            sks = int(mk["sks"])
        except (ValueError, TypeError):
            continue
        if bobot is None:
            continue
        total_sks += sks
        total_mutu += sks * bobot
    return f"{total_mutu / total_sks:.2f}" if total_sks else "-"


@st.cache_data(show_spinner=False)
def analisis_transkrip(file_bytes: bytes, ext: str) -> dict:
    """Hasil di-cache: file yang sama tidak akan diproses ulang."""
    teks = ekstrak_teks(file_bytes, ext)
    profil = parse_profil(teks)
    mk = parse_matakuliah(teks)
    if profil["ipk"] == "-" and mk:
        profil["ipk"] = hitung_ipk(mk) + " (dihitung otomatis)"
    return {"mahasiswa": profil, "mata_kuliah": mk}



st.session_state.setdefault("active_view", "HOME")
st.session_state.setdefault("sarasehan_registered", False)
st.session_state.setdefault("analisis_id", 0)

with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/graduation-cap.png", width=100)
    st.title("👤 Akun")
    st.write(f"**{USER_NAMA}**")
    st.caption(st.session_state["user_email"])
    if st.button("🚪 Logout", key="btn_logout"):
        for k in ("logged_in", "user_email", "user_nama", "user_nim", "hasil_analisis"):
            st.session_state.pop(k, None)
        st.rerun()

    st.markdown("---")
    st.markdown("### 📌 Petunjuk Penggunaan")
    st.markdown("""
    1. Unggah transkrip nilai (**PDF**, **PNG**, **JPG**, **JPEG**).
    2. Klik **Mulai Analisis Transkrip**.
    3. Periksa / koreksi tabel hasil jika perlu.
    4. Simpan ke database atau unduh **CSV**.
    """)
    st.markdown("---")
    st.caption("Dibuat dengan ❤️ menggunakan Streamlit")



btn_col1, btn_col2, btn_col3, _ = st.columns([1.2, 1.8, 2.2, 4])
with btn_col1:
    if st.button("🏠 HOME", key="btn_home_nav"):
        st.session_state["active_view"] = "HOME"
        st.rerun()
with btn_col2:
    if st.button("💼 Kerja Praktek (KP)", key="btn_kp_nav"):
        st.session_state["active_view"] = "KP"
        st.rerun()
with btn_col3:
    if st.button("🏆 Tugas Talenta Unggul (TTU)", key="btn_ttu_nav"):
        st.session_state["active_view"] = "TTU"
        st.rerun()

st.markdown("---")



if st.session_state["active_view"] == "HOME":
    st.title("Transkrip Nilai Reader")
    st.markdown(
        "Ekstrak data mahasiswa dan daftar mata kuliah dari transkrip nilai "
        "langsung di komputer Anda, tanpa API Key dan tanpa menunggu server AI."
    )
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "📂 Unggah File Transkrip Nilai (PDF / Gambar)",
        type=["pdf", "png", "jpg", "jpeg"],
    )

    if uploaded_file is not None:
        ext = uploaded_file.name.split(".")[-1].lower()
        file_bytes = uploaded_file.getvalue()

        col_preview, col_result = st.columns([1, 1.2], gap="large")

        with col_preview:
            st.markdown("### 📄 Preview Dokumen")
            if ext in ("png", "jpg", "jpeg"):
                st.image(Image.open(io.BytesIO(file_bytes)),
                         caption=f"File: {uploaded_file.name}", use_container_width=True)
            else:
                st.success(f"📄 File PDF berhasil diunggah: **{uploaded_file.name}**")

        with col_result:
            st.markdown("### ⚙️ Kontrol & Hasil Analisis")

            if st.button("🔍 Mulai Analisis Transkrip Sekarang"):
                with st.spinner("Membaca transkrip..."):
                    try:
                        st.session_state["hasil_analisis"] = analisis_transkrip(file_bytes, ext)
                        st.session_state["analisis_id"] += 1
                    except ImportError as e:
                        st.error(
                            f"❌ Library belum terpasang: {e}. Jalankan: "
                            "`pip install pdfplumber pytesseract`"
                        )
                    except Exception as e:
                        if "tesseract" in str(e).lower():
                            st.error(
                                "❌ Tesseract OCR belum terpasang di komputer ini. File PDF digital "
                                "tetap bisa dibaca, tetapi gambar/scan butuh Tesseract."
                            )
                        else:
                            st.error(f"❌ Terjadi kesalahan saat memproses dokumen: {e}")

            hasil = st.session_state.get("hasil_analisis")
            if hasil:
                aid = st.session_state["analisis_id"]
                mhs = hasil["mahasiswa"]

                st.markdown("---")
                if not hasil["mata_kuliah"]:
                    st.warning(
                        "⚠️ Tidak ada mata kuliah yang terdeteksi. Pastikan dokumen jelas, "
                        "atau tambahkan baris secara manual pada tabel di bawah."
                    )
                else:
                    st.success(f"✨ Ekstraksi selesai: {len(hasil['mata_kuliah'])} mata kuliah terdeteksi.")

                st.markdown("#### 👤 Profil Mahasiswa (bisa diedit)")
                c1, c2 = st.columns(2)
                with c1:
                    nama_v = st.text_input("Nama", mhs["nama"], key=f"p_nama_{aid}")
                    nim_v = st.text_input("NIM", mhs["nim"], key=f"p_nim_{aid}")
                    jur_v = st.text_input("Jurusan", mhs["jurusan"], key=f"p_jur_{aid}")
                with c2:
                    uni_v = st.text_input("Universitas", mhs["universitas"], key=f"p_uni_{aid}")
                    ipk_v = st.text_input("IPK Kumulatif", mhs["ipk"], key=f"p_ipk_{aid}")

                st.markdown("#### 📚 Daftar Mata Kuliah (bisa diedit)")
                df = pd.DataFrame(hasil["mata_kuliah"], columns=["kode", "nama_mk", "sks", "nilai"])
                df.columns = ["Kode MK", "Nama Mata Kuliah", "SKS", "Nilai"]
                df_edit = st.data_editor(
                    df, num_rows="dynamic", use_container_width=True,
                    hide_index=True, key=f"editor_{aid}",
                )

                col_s, col_d = st.columns(2)
                with col_s:
                    if st.button("💾 Simpan ke Database", key="btn_simpan_transkrip"):
                        mk_list = [
                            {"kode": str(r["Kode MK"]), "nama_mk": str(r["Nama Mata Kuliah"]),
                             "sks": str(r["SKS"]), "nilai": str(r["Nilai"])}
                            for _, r in df_edit.iterrows()
                        ]
                        profil = {"nama": nama_v, "nim": nim_v, "jurusan": jur_v,
                                  "universitas": uni_v, "ipk": ipk_v}
                        if simpan_ke_database(profil, mk_list):
                            st.success("💾 Data berhasil disimpan ke database lokal!")
                with col_d:
                    st.download_button(
                        "📥 Unduh Data Mata Kuliah (.CSV)",
                        data=df_edit.to_csv(index=False).encode("utf-8"),
                        file_name="transkrip_extracted.csv",
                        mime="text/csv",
                    )



elif st.session_state["active_view"] == "TTU":

    tab1, tab2, tab3 = st.tabs(["📋 Daftar TTU", "🔍 Daftar Review", "🎓 Daftar Yudisium"])

    with tab1:
        st.markdown("### SEMESTER GANJIL 2026-2027")
        st.markdown("## PENDAFTARAN TUGAS TALENTA UNGGUL")
        st.markdown(
            '<div class="announcement-box">ℹ️ Pendaftaran Tugas Talenta Unggul Dibuka Sampai Minggu, 10 September 2026</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="form-header">FORM PENDAFTARAN TUGAS TALENTA UNGGUL SEMESTER GANJIL 2026-2027</div>', unsafe_allow_html=True)

        with st.container():
            st.write("")
            col_nim, col_nama = st.columns(2)
            with col_nim:
                nim = st.text_input("NIM", value=USER_NIM)
            with col_nama:
                nama = st.text_input("Nama", value=USER_NAMA)

            col_prodi, col_peminatan = st.columns(2)
            with col_prodi:
                prodi = st.text_input("Program Studi", value="S1 TEKNIK INFORMATIKA")
            with col_peminatan:
                peminatan = st.text_input("Peminatan", placeholder="peminatan/bidang dari topik anda...")

            col_ttu_ambil, col_status = st.columns(2)
            with col_ttu_ambil:
                st.markdown("**Tugas Talenta Unggul Yang Akan Diambil** <span class='badge-req'>⚠️</span>", unsafe_allow_html=True)
                ttu1 = st.checkbox("Tugas Talenta Unggul 1")
                ttu2 = st.checkbox("Tugas Talenta Unggul 2")
                ttu3 = st.checkbox("Tugas Talenta Unggul 3")
            with col_status:
                st.markdown("**Status Tugas Talenta Unggul**", unsafe_allow_html=True)
                status_ttu = st.selectbox("Status", ["Baru", "Lanjut"], label_visibility="collapsed")

            st.markdown("**Judul Tugas Talenta Unggul** <span class='badge-req'>⚠️</span>", unsafe_allow_html=True)
            judul_ttu = st.text_input("Judul", placeholder="isi judul tugas talenta unggul anda. jika belum ada, isi -", label_visibility="collapsed")

            col_pemb1, col_pemb2 = st.columns(2)
            with col_pemb1:
                st.markdown("**Usulan Pembimbing 1**", unsafe_allow_html=True)
                pemb1 = st.text_input("Pembimbing 1", placeholder="isi usulan pembimbing anda...", label_visibility="collapsed")
            with col_pemb2:
                st.markdown("**Usulan Pembimbing 2**", unsafe_allow_html=True)
                pemb2 = st.text_input("Pembimbing 2", placeholder="isi usulan pembimbing anda...", label_visibility="collapsed")

            col_doc, col_transkrip = st.columns(2)
            with col_doc:
                st.markdown("📄 **Dokumen Tugas Talenta Unggul (PDF/Ms.Word)** <span class='badge-req'>⚠️ Max 15MB</span>", unsafe_allow_html=True)
                st.file_uploader("Upload Dokumen", type=["pdf", "doc", "docx"], label_visibility="collapsed", key="doc_ttu")
            with col_transkrip:
                st.markdown("🖼️ **Scan Transkrip Nilai** <span class='badge-req'>⚠️ Max 5MB</span>", unsafe_allow_html=True)
                st.file_uploader("Upload Transkrip", type=["pdf", "png", "jpg", "jpeg"], label_visibility="collapsed", key="transkrip_ttu")

            st.markdown("---")
            col_btn, _ = st.columns([1, 3])
            with col_btn:
                btn_daftar = st.button("DAFTAR", key="btn_submit_ttu")

            if btn_daftar:
                if not judul_ttu or judul_ttu == "-":
                    st.warning("⚠️ Mohon isi Judul Tugas Talenta Unggul terlebih dahulu!")
                else:
                    selected_ttu = [t for t, on in [
                        ("Tugas Talenta Unggul 1", ttu1),
                        ("Tugas Talenta Unggul 2", ttu2),
                        ("Tugas Talenta Unggul 3", ttu3),
                    ] if on]
                    if simpan_ttu(nim, nama, prodi, peminatan, selected_ttu, status_ttu, judul_ttu, pemb1, pemb2):
                        st.success("✅ Pendaftaran Tugas Talenta Unggul Berhasil Dikirim dan Disimpan ke Database!")

    with tab2:
        st.markdown("### SEMESTER GANJIL 2026-2027")
        st.markdown("## PENDAFTARAN REVIEW")
        st.markdown(
            '<div class="announcement-box">ℹ️ Pendaftaran Review Dibuka Sampai Minggu, 3 Desember 2026</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="form-header">FORM PENDAFTARAN REVIEW</div>', unsafe_allow_html=True)

        with st.container():
            st.write("")
            col_r_nim, col_r_nama = st.columns(2)
            with col_r_nim:
                r_nim = st.text_input("NIM", value=USER_NIM, key="r_nim")
            with col_r_nama:
                r_nama = st.text_input("Nama", value=USER_NAMA, key="r_nama")

            col_r_prodi, col_r_peminatan = st.columns(2)
            with col_r_prodi:
                r_prodi = st.text_input("Program Studi", value="S1 TEKNIK INFORMATIKA", key="r_prodi")
            with col_r_peminatan:
                r_peminatan = st.text_input("Peminatan", value="web, webservice, php", key="r_peminatan")

            st.markdown("**Judul Tugas Akhir**", unsafe_allow_html=True)
            r_judul = st.text_input(
                "Judul Tugas Akhir",
                value="Perancangan Website Sistem Informasi Tugas Akhir Dengan Teknologi SOAP Web Services",
                label_visibility="collapsed", key="r_judul",
            )

            col_r_pemb1, col_r_pemb2 = st.columns(2)
            with col_r_pemb1:
                st.markdown("**Pembimbing 1**", unsafe_allow_html=True)
                r_pemb1 = st.text_input("Pembimbing 1", value="Dr. Kristoko Dwi Hartomo, M.Kom.", label_visibility="collapsed", key="r_pemb1")
            with col_r_pemb2:
                st.markdown("**Pembimbing 2**", unsafe_allow_html=True)
                r_pemb2 = st.text_input("Pembimbing 2", value="Belum Ada Data", label_visibility="collapsed", key="r_pemb2")

            col_r_rev1, col_r_rev2 = st.columns(2)
            with col_r_rev1:
                st.markdown("**Reviewer 1**", unsafe_allow_html=True)
                r_rev1 = st.text_input("Reviewer 1", value="Christine Dewi, S.Kom., M.Cs.", label_visibility="collapsed", key="r_rev1")
            with col_r_rev2:
                st.markdown("**Reviewer 2**", unsafe_allow_html=True)
                r_rev2 = st.text_input("Reviewer 2", value="Belum Ada Data", label_visibility="collapsed", key="r_rev2")

            col_r_doc, col_r_transkrip = st.columns(2)
            with col_r_doc:
                st.markdown("📄 **Dokumen Akhir (PDF/Ms.Word)** <span class='badge-req'>⚠️ *Ukuran file max 15MB</span>", unsafe_allow_html=True)
                st.file_uploader("Upload Dokumen Akhir", type=["pdf", "doc", "docx"], label_visibility="collapsed", key="r_doc_file")
            with col_r_transkrip:
                st.markdown("🖼️ **Scan Transkrip Nilai** <span class='badge-req'>⚠️ *Ukuran file max 5MB</span>", unsafe_allow_html=True)
                st.file_uploader("Upload Scan Transkrip", type=["pdf", "png", "jpg", "jpeg"], label_visibility="collapsed", key="r_transkrip_file")

            st.markdown("---")
            col_r_btn, _ = st.columns([1.5, 3])
            with col_r_btn:
                st.markdown('<div class="btn-custom-submit">', unsafe_allow_html=True)
                btn_daftar_review = st.button("DAFTAR REVIEW", key="btn_submit_review")
                st.markdown('</div>', unsafe_allow_html=True)

            if btn_daftar_review:
                if simpan_review(r_nim, r_nama, r_prodi, r_peminatan, r_judul, r_pemb1, r_pemb2, r_rev1, r_rev2):
                    st.success("✅ Pendaftaran Review Berhasil Dikirim dan Disimpan ke Database!")

    with tab3:
        st.markdown("### SEMESTER GANJIL 2026-2027")
        st.markdown("## PENDAFTARAN YUDISIUM")
        st.markdown('<div class="form-header">DAFTAR YUDISIUM</div>', unsafe_allow_html=True)

        with st.container():
            st.write("")
            st.markdown('<div class="success-box">Yudisium Akan Dilakukan Pada Jumat, 14 Desember 2026</div>', unsafe_allow_html=True)
            st.markdown('<div class="announcement-box">ℹ️ Pendaftaran Yudisium Dibuka Sampai Rabu, 12 Desember 2026</div>', unsafe_allow_html=True)
            st.write("")

            col_y_btn, _ = st.columns([1.8, 3])
            with col_y_btn:
                st.markdown('<div class="btn-custom-submit">', unsafe_allow_html=True)
                btn_daftar_yudisium = st.button("DAFTAR YUDISIUM", key="btn_submit_yudisium")
                st.markdown('</div>', unsafe_allow_html=True)

            if btn_daftar_yudisium:
                if simpan_yudisium():
                    st.success("✅ Pendaftaran Yudisium Berhasil Dikirim dan Disimpan ke Database!")



elif st.session_state["active_view"] == "KP":

    tab_kp1, tab_kp2, tab_kp3, tab_kp4, tab_kp5 = st.tabs([
        "👥 1. Daftar Sarasehan",
        "🏢 2. List Tempat KP",
        "📢 3. Pengumuman",
        "📄 4. Surat Permohonan",
        "📋 5. Daftar KP",
    ])

    with tab_kp1:
        st.markdown("### SEMESTER GANJIL 2026-2027")
        st.markdown("## DAFTAR SARASEHAN")
        st.markdown('<div class="form-header">Daftar Sarasehan</div>', unsafe_allow_html=True)

        with st.container():
            st.write("")
            if not st.session_state["sarasehan_registered"]:
                st.markdown(
                    '<div class="announcement-box">Pendaftaran Sarasehan Akan Ditutup Pada <b>SENIN, 15 OKTOBER 2026</b></div>',
                    unsafe_allow_html=True,
                )
                st.write("")
                col_s_btn, _ = st.columns([2, 3])
                with col_s_btn:
                    btn_daftar_sarasehan = st.button("DAFTAR SARASEHAN!", key="btn_submit_sarasehan")
                if btn_daftar_sarasehan:
                    if simpan_sarasehan("Terdaftar"):
                        st.session_state["sarasehan_registered"] = True
                        st.rerun()
            else:
                st.markdown('<div class="success-box">Sukses daftar Sarasehan!</div>', unsafe_allow_html=True)
                st.markdown(
                    """
                    <div class="warning-box">
                        Sarasehan akan diadakan pada :<br>
                        <b>Hari/Tanggal : Senin, 19 Oktober 2026</b><br>
                        <b>Waktu : 13:00-selesai</b><br>
                        <b>Tempat : AUDITORIUM</b>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                col_reset, _ = st.columns([1.5, 3])
                with col_reset:
                    if st.button("🔄 Batalkan / Reset Pendaftaran", key="btn_reset_sarasehan"):
                        st.session_state["sarasehan_registered"] = False
                        st.rerun()

    with tab_kp2:
        st.subheader("🏢 List Tempat Kerja Praktek (KP)")
        st.write("Daftar perusahaan atau instansi mitra yang menerima Kerja Praktek:")
        df_tempat_kp = pd.DataFrame([
            {"No": 1, "Nama Perusahaan": "PT Solusi Teknologi Indonesia", "Kota": "Semarang", "Kuota": "3 Mahasiswa", "Status": "Tersedia"},
            {"No": 2, "Nama Perusahaan": "Dinas Komunikasi dan Informatika", "Kota": "Salatiga", "Kuota": "2 Mahasiswa", "Status": "Tersedia"},
            {"No": 3, "Nama Perusahaan": "Alfacart (Tangerang)", "Kota": "Tangerang", "Kuota": "5 Mahasiswa", "Status": "Tersedia"},
        ])
        st.dataframe(df_tempat_kp, use_container_width=True, hide_index=True)

    with tab_kp3:
        st.subheader("📢 Pengumuman Kerja Praktek")
        st.markdown(
            """
            <div class="announcement-box">
                ℹ️ <b>Pengumuman Pelaksanaan KP Semester Ganjil 2026-2027:</b><br>
                1. Batas akhir pengajuan surat permohonan KP adalah tanggal 30 November 2026.<br>
                2. Mahasiswa wajib telah menyelesaikan pendaftaran sarasehan sebelum mengunggah laporan KP.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with tab_kp4:
        st.subheader("📄 Pengajuan Surat Permohonan KP")
        with st.form("form_surat_kp"):
            instansi_input = st.text_input("Nama Instansi / Perusahaan Tujuan", placeholder="Masukkan nama perusahaan...")
            alamat_input = st.text_area("Alamat Lengkap Perusahaan", placeholder="Masukkan alamat lengkap...")
            ditujukan_input = st.text_input("Ditujukan Kepada (Jabatan/HRD)", placeholder="Contoh: HRD Manager / Kepala Divisi IT")
            if st.form_submit_button("Kirim Pengajuan Surat"):
                if simpan_surat_kp(instansi_input, alamat_input, ditujukan_input):
                    st.success("✅ Pengajuan surat permohonan KP berhasil dikirim!")

    with tab_kp5:
        st.subheader("📋 Pendaftaran Kerja Praktek (KP)")
        with st.form("form_pendaftaran_kp"):
            nim_kp = st.text_input("NIM Mahasiswa", value=USER_NIM)
            nama_kp = st.text_input("Nama Lengkap", value=USER_NAMA)

            st.markdown("**Mata Kuliah Pendukung / Terkait KP:**")
            mk_kp1 = st.checkbox("Pemrograman Web")
            mk_kp2 = st.checkbox("Sistem Basis Data")
            mk_kp3 = st.checkbox("Rekayasa Perangkat Lunak")

            tempat_kp = st.text_input("Nama Tempat / Instansi KP")

            if st.form_submit_button("Daftar KP Sekarang"):
                selected_mk_kp = [n for n, on in [
                    ("Pemrograman Web", mk_kp1),
                    ("Sistem Basis Data", mk_kp2),
                    ("Rekayasa Perangkat Lunak", mk_kp3),
                ] if on]
                if simpan_kp(nim_kp, nama_kp, selected_mk_kp, tempat_kp):
                    st.success("✅ Pendaftaran KP Berhasil Disimpan!")
