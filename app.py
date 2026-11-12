import hmac
import io
import re
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps

st.set_page_config(
    page_title="Transkrip Nilai Reader",
    page_icon="🎓",
    layout="wide",
)

# --- INISIALISASI SESSION STATE DI AWAL ---
st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("active_view", "HOME")
st.session_state.setdefault("sarasehan_registered", False)
st.session_state.setdefault("analisis_id", 0)

USERS = {
    "672023030@student.uksw.edu": {"password": "123456", "nama": "Julius"},
}
DB_PATH = "transkrip_nilai.db"

KURIKULUM_2026_DATA = [
    {"kode": "MU114", "nama": "Pancasila", "sks": 2, "kategori": "MKDU Wajib Negara"},
    {"kode": "MU115", "nama": "Kewarganegaraan", "sks": 2, "kategori": "MKDU Wajib Negara"},
    {"kode": "MU117", "nama": "Pendidikan Agama", "sks": 2, "kategori": "MKDU Wajib Negara"},
    {"kode": "MU116", "nama": "Bahasa Indonesia", "sks": 2, "kategori": "MKDU Wajib Negara"},
    {"kode": "MU118", "nama": "Pengembangan Kepribadian Entrepreneurial", "sks": 3, "kategori": "MKDU Wajib Universitas"},
    {"kode": "MU119", "nama": "Kewirausahaan", "sks": 3, "kategori": "MKDU Wajib Universitas"},
    {"kode": "TC511", "nama": "Matematika Diskrit", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC521", "nama": "Aljabar Linier dan Matrix", "sks": 2, "kategori": "MK Wajib Prodi"},
    {"kode": "TC532", "nama": "Statistika dan Probabilitas", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC513", "nama": "Dasar-Dasar Pemrograman", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC534", "nama": "Algoritma dan Struktur Data", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC613", "nama": "Pemrograman Berorientasi Obyek", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC612", "nama": "Pemrograman Web", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC631", "nama": "Sistem Operasi", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC615", "nama": "Arsitektur dan Organisasi Komputer", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC535", "nama": "Interaksi Manusia dan Komputer", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC512", "nama": "Pengantar Teknologi Informasi", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC515", "nama": "Sistem Basis Data", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC533", "nama": "Jaringan Komputer", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC531", "nama": "Teori Bahasa dan Automata", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC611", "nama": "Kecerdasan Buatan", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC634", "nama": "Keamanan Data", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC632", "nama": "Rekayasa Perangkat Lunak", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC810", "nama": "Etika Profesi", "sks": 2, "kategori": "MK Wajib Prodi"},
    {"kode": "TC514", "nama": "Bahasa Inggris", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC722", "nama": "Penulisan Karya Ilmiah", "sks": 2, "kategori": "MK Wajib Prodi"},
    {"kode": "TC633", "nama": "Metode Penelitian", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC635", "nama": "Machine Learning", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC733", "nama": "Deep Learning", "sks": 3, "kategori": "MK Konsentrasi Data Science"},
    {"kode": "TC739", "nama": "Riset Operasi", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC616", "nama": "Sistem Basis Data Non-Relasional", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC617", "nama": "Bahasa Inggris Profesi", "sks": 2, "kategori": "MK Wajib Prodi"},
    {"kode": "TC618", "nama": "Pemrograman Lanjut (web service)", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC619", "nama": "Kalkulus", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC620", "nama": "Pemrograman Visual (UI/UX)", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC621", "nama": "Rekayasa Kecerdasan Buatan", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC751", "nama": "Perancangan dan Manajemen Jaringan", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC752", "nama": "Virtualisasi dan Infrastruktur Cloud", "sks": 3, "kategori": "MK Konsentrasi Network"},
    {"kode": "TC764", "nama": "Jaringan Quantum", "sks": 3, "kategori": "MK Konsentrasi Network"},
    {"kode": "TC754", "nama": "Routing dan Switching 1", "sks": 3, "kategori": "MK Konsentrasi Network"},
    {"kode": "TC765", "nama": "Pemrograman Jaringan", "sks": 3, "kategori": "MK Konsentrasi Network"},
    {"kode": "TC756", "nama": "Jaringan Nirkabel", "sks": 3, "kategori": "MK Konsentrasi Network"},
    {"kode": "TC758", "nama": "Algoritma Jaringan", "sks": 3, "kategori": "MK Konsentrasi Network"},
    {"kode": "TC759", "nama": "Pemodelan dan Simulasi Jaringan", "sks": 3, "kategori": "MK Konsentrasi Network"},
    {"kode": "TC760", "nama": "Routing dan Switching 2", "sks": 3, "kategori": "MK Konsentrasi Network"},
    {"kode": "TC762", "nama": "Keamanan Siber", "sks": 3, "kategori": "MK Konsentrasi Network"},
    {"kode": "TC784", "nama": "Vehicular Communication", "sks": 3, "kategori": "MK Konsentrasi Network"},
    {"kode": "TC785", "nama": "Arsitektur dan Desain Sistem Jaringan", "sks": 3, "kategori": "MK Konsentrasi Network"},
    {"kode": "TC622", "nama": "Keamanan Siber Lanjut", "sks": 3, "kategori": "MK Konsentrasi Network"},
    {"kode": "TC368", "nama": "Kapita Selekta Network Engineering", "sks": 3, "kategori": "MK Konsentrasi Network"},
    {"kode": "TC712", "nama": "Pemrograman Mobile", "sks": 3, "kategori": "MK Konsentrasi Software"},
    {"kode": "TC713", "nama": "UI/UX", "sks": 3, "kategori": "MK Konsentrasi Software"},
    {"kode": "TC714", "nama": "Software Quality Assurance", "sks": 3, "kategori": "MK Wajib Prodi"},
    {"kode": "TC715", "nama": "Manajemen Proyek", "sks": 3, "kategori": "MK Konsentrasi Software"},
    {"kode": "TC716", "nama": "Web Services", "sks": 3, "kategori": "MK Konsentrasi Software"},
    {"kode": "TC719", "nama": "Pemrograman Berorientasi Platform", "sks": 3, "kategori": "MK Konsentrasi Software"},
    {"kode": "TC720", "nama": "Grafika Komputer", "sks": 3, "kategori": "MK Konsentrasi Software"},
    {"kode": "TC367", "nama": "Kapita Selekta Software Engineering", "sks": 3, "kategori": "MK Konsentrasi Software"},
    {"kode": "TC623", "nama": "Pemrograman IoT", "sks": 3, "kategori": "MK Konsentrasi Software"},
    {"kode": "TC711", "nama": "Pemrograman Cloud dan Enterprise", "sks": 3, "kategori": "MK Konsentrasi Software"},
    {"kode": "TC724", "nama": "Pemrograman Mobile Lanjut", "sks": 3, "kategori": "MK Konsentrasi Software"},
    {"kode": "TC731", "nama": "Metodologi Data Science", "sks": 3, "kategori": "MK Konsentrasi Data Science"},
    {"kode": "TC732", "nama": "Teknik Optimalisasi", "sks": 3, "kategori": "MK Konsentrasi Data Science"},
    {"kode": "TC735", "nama": "Analisis Data Exploratif", "sks": 3, "kategori": "MK Konsentrasi Data Science"},
    {"kode": "TC737", "nama": "Pemrosesan Bahasa Alami", "sks": 3, "kategori": "MK Konsentrasi Data Science"},
    {"kode": "TC738", "nama": "Komputasi Terdistribusi", "sks": 3, "kategori": "MK Konsentrasi Data Science"},
    {"kode": "TC369", "nama": "Kapita Selekta Data Science", "sks": 3, "kategori": "MK Konsentrasi Data Science"},
    {"kode": "TC786", "nama": "Computer Vision and Application", "sks": 3, "kategori": "MK Konsentrasi Data Science"},
    {"kode": "TC787", "nama": "Computational Journalism", "sks": 3, "kategori": "MK Konsentrasi Data Science"},
    {"kode": "TC725", "nama": "Image Processing", "sks": 3, "kategori": "MK Konsentrasi Data Science"},
    {"kode": "TC788", "nama": "Bio-Informatic", "sks": 3, "kategori": "MK Konsentrasi Data Science"},
    {"kode": "TC789", "nama": "Teknologi Blockchain", "sks": 3, "kategori": "MK Konsentrasi Data Science"},
    {"kode": "TC790", "nama": "Pendidikan dan Teknologi Kebencanaan", "sks": 3, "kategori": "MK Konsentrasi Data Science"},
    {"kode": "TC141", "nama": "Proyek Smart City", "sks": 3, "kategori": "MK Pilihan"},
    {"kode": "TC142", "nama": "Matematika Data Science", "sks": 3, "kategori": "MK Pilihan"},
    {"kode": "TC734", "nama": "Pemodelan Spasial", "sks": 3, "kategori": "MK Pilihan"},
    {"kode": "TC522", "nama": "Matematika Diskrit Lanjut", "sks": 3, "kategori": "MK Pilihan"},
    {"kode": "TC851", "nama": "Tugas Talenta Unggul 1", "sks": 3, "kategori": "KP + TTU"},
    {"kode": "TC852", "nama": "Tugas Talenta Unggul 2", "sks": 3, "kategori": "KP + TTU"},
    {"kode": "TC853", "nama": "Tugas Talenta Unggul 3", "sks": 2, "kategori": "KP + TTU"},
    {"kode": "TC821", "nama": "Kerja Praktek", "sks": 5, "kategori": "KP + TTU"},
    {"kode": "TC822", "nama": "Laporan Kerja Praktek", "sks": 5, "kategori": "KP + TTU"},
]

st.markdown("""
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
    </style>
""", unsafe_allow_html=True)

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
            email = st.text_input("Email", value="672023030@student.uksw.edu", placeholder="nim@student.uksw.edu")
            password = st.text_input("Password", type="password", value="123456")
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
    c.execute("""CREATE TABLE IF NOT EXISTS mahasiswa_profil (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT, nim TEXT, jurusan TEXT, universitas TEXT, ipk TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    c.execute("""CREATE TABLE IF NOT EXISTS mata_kuliah (
            id INTEGER PRIMARY KEY AUTOINCREMENT, mahasiswa_id INTEGER,
            kode_mk TEXT, nama_mk TEXT, sks TEXT, nilai TEXT,
            FOREIGN KEY (mahasiswa_id) REFERENCES mahasiswa_profil(id) ON DELETE CASCADE
        )""")
    c.execute("""CREATE TABLE IF NOT EXISTS kurikulum_2026 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kode_mk TEXT UNIQUE, nama_mk TEXT, sks INTEGER, kategori TEXT
        )""")
    c.execute("""CREATE TABLE IF NOT EXISTS pendaftaran_ttu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nim TEXT, nama TEXT, prodi TEXT, peminatan TEXT,
            ttu_ambil TEXT, status TEXT, judul TEXT,
            pembimbing1 TEXT, pembimbing2 TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    c.execute("""CREATE TABLE IF NOT EXISTS pendaftaran_review (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nim TEXT, nama TEXT, prodi TEXT, peminatan TEXT,
            judul TEXT, pembimbing1 TEXT, pembimbing2 TEXT,
            reviewer1 TEXT, reviewer2 TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    c.execute("""CREATE TABLE IF NOT EXISTS pendaftaran_yudisium (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    c.execute("""CREATE TABLE IF NOT EXISTS pendaftaran_sarasehan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status_pendaftaran TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    c.execute("""CREATE TABLE IF NOT EXISTS permohonan_surat_kp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instansi TEXT, alamat TEXT, ditujukan TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    c.execute("""CREATE TABLE IF NOT EXISTS pendaftaran_kp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nim TEXT, nama TEXT, matakuliah_kp TEXT, tempat_kp TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    c.executemany("""
        INSERT OR IGNORE INTO kurikulum_2026 (kode_mk, nama_mk, sks, kategori)
        VALUES (:kode, :nama, :sks, :kategori)
    """, KURIKULUM_2026_DATA)
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
        cur.execute("INSERT INTO mahasiswa_profil (nama, nim, jurusan, universitas, ipk) VALUES (?,?,?,?,?)",
            (mhs.get("nama", "-"), mhs.get("nim", "-"), mhs.get("jurusan", "-"),
             mhs.get("universitas", "-"), str(mhs.get("ipk", "-"))))
        mhs_id = cur.lastrowid
        cur.executemany("INSERT INTO mata_kuliah (mahasiswa_id, kode_mk, nama_mk, sks, nilai) VALUES (?,?,?,?,?)",
            [(mhs_id, m["kode"], m["nama_mk"], str(m["sks"]), str(m["nilai"])) for m in mk_list])
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan ke database: {e}")
        return False

def simpan_ttu(nim, nama, prodi, peminatan, ttu_list, status, judul, pemb1, pemb2):
    return _jalankan("""INSERT INTO pendaftaran_ttu
           (nim, nama, prodi, peminatan, ttu_ambil, status, judul, pembimbing1, pembimbing2)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (nim, nama, prodi, peminatan, ", ".join(ttu_list), status, judul, pemb1, pemb2),
        "Gagal menyimpan data TTU")

def simpan_review(nim, nama, prodi, peminatan, judul, pemb1, pemb2, rev1, rev2):
    return _jalankan("""INSERT INTO pendaftaran_review
           (nim, nama, prodi, peminatan, judul, pembimbing1, pembimbing2, reviewer1, reviewer2)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (nim, nama, prodi, peminatan, judul, pemb1, pemb2, rev1, rev2),
        "Gagal menyimpan data Review")

def simpan_yudisium():
    return _jalankan("INSERT INTO pendaftaran_yudisium DEFAULT VALUES", pesan_error="Gagal menyimpan data Yudisium")

def simpan_sarasehan(status):
    return _jalankan("INSERT INTO pendaftaran_sarasehan (status_pendaftaran) VALUES (?)", (status,), "Gagal menyimpan data Sarasehan")

def simpan_surat_kp(instansi, alamat, ditujukan):
    return _jalankan("INSERT INTO permohonan_surat_kp (instansi, alamat, ditujukan) VALUES (?,?,?)",
        (instansi, alamat, ditujukan), "Gagal menyimpan surat KP")

def simpan_kp(nim, nama, mk_list, tempat):
    return _jalankan("INSERT INTO pendaftaran_kp (nim, nama, matakuliah_kp, tempat_kp) VALUES (?,?,?,?)",
        (nim, nama, ", ".join(mk_list), tempat), "Gagal menyimpan pendaftaran KP")

GRADE = r"(?:A-|AB|A|B\+|B-|BC|B|C\+|C|D\+|D|E|T)"
BOBOT = {"A": 4.0, "A-": 3.75, "AB": 3.5, "B+": 3.5, "B": 3.0, "B-": 2.75,
         "BC": 2.5, "C+": 2.5, "C": 2.0, "D+": 1.5, "D": 1.0, "E": 0.0}

def ocr_gambar(img: Image.Image) -> str:
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

def ekstrak_teks_dan_tabel(file_bytes: bytes, ext: str) -> tuple[str, list]:
    if ext in ("png", "jpg", "jpeg"):
        try:
            return ocr_gambar(Image.open(io.BytesIO(file_bytes))), []
        except Exception as e:
            return f"Error OCR: {e}", []
           
    import pdfplumber
    teks_gabung = []
    semua_tabel = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                teks_gabung.append(t)
                tables = page.extract_tables()
                if tables:
                    for tbl in tables:
                        semua_tabel.extend(tbl)
    except Exception as e:
        teks_gabung.append(f"Error PDF: {e}")
       
    return "\n".join(teks_gabung), semua_tabel

def _cari(pola: str, teks: str, flags=re.IGNORECASE) -> str:
    m = re.search(pola, teks, flags)
    return m.group(1).strip() if m else "-"

def parse_profil(teks: str) -> dict:
    universitas = "-"
    for line in teks.splitlines()[:15]:
        if re.search(r"universitas|institut|politeknik|sekolah tinggi", line, re.IGNORECASE):
            universitas = line.strip()
            break
    nama = _cari(r"\bNAMA\s*[:\-]?\s*([A-Z\s.,']+)", teks, flags=0)
    if nama == "-":
        nama = _cari(r"\bNama(?:\s+Mahasiswa)?\s*[:\-]\s*([^\n]+)", teks)
    nim = _cari(r"\b(?:NIM|N\.I\.M)\s*[:\-]?\s*(\d{6,12})", teks)
    jurusan = _cari(r"(?:Jur/Progdi|Program\s+Studi|Prodi|Jurusan)\s*[:\-]?\s*([^\n]+)", teks)
    if "TEKNIK INFORMATIK" in jurusan.upper():
        jurusan = "S1 Teknik Informatika"

    return {
        "nama": nama.strip(),
        "nim": nim,
        "jurusan": jurusan,
        "universitas": universitas,
        "ipk": _cari(r"(?:IPK|Indeks\s+Prestasi\s+Kumulatif|GPA|\bIP\b)[^\d\n]{0,30}(\d[.,]\d{1,2})", teks).replace(",", "."),
    }

def parse_matakuliah_pro(teks: str, tables: list) -> list[dict]:
    hasil = []
    seen = set()
    pola_uksw = re.compile(
        r"(\d+)\.\s+([A-Z0-9\s\(\)\-\/&.,']+?)\s+([A-Z]{2,4}\d{3})\s+(\d)\s+\d/\d{2}\s+(AB|A-|A|B\+|B-|BC|B|C\+|C|D\+|D|E|T)\s+\d+(?:\.\d+)?"
    )
    semua_sumber = [teks]
    if tables:
        for row in tables:
            semua_sumber.append(" ".join([str(c).replace("\n", " ") for c in row if c]))
    for sumber in semua_sumber:
        for m in pola_uksw.finditer(sumber):
            no_urut = int(m.group(1))
            nama_mk = m.group(2).strip()
            kode = m.group(3).strip()
            sks = m.group(4).strip()
            grade = m.group(5).strip()
            for k in KURIKULUM_2026_DATA:
                if k["kode"] == kode:
                    nama_mk = k["nama"]
                    break
            key = (no_urut, kode)
            if key not in seen:
                seen.add(key)
                hasil.append({
                    "no": no_urut,
                    "kode": kode,
                    "nama_mk": nama_mk,
                    "sks": sks,
                    "nilai": grade
                })
    if hasil:
        hasil.sort(key=lambda x: x.get("no", 999))
        return [{"kode": h["kode"], "nama_mk": h["nama_mk"], "sks": h["sks"], "nilai": h["nilai"]} for h in hasil]
    for kur in KURIKULUM_2026_DATA:
        if kur["kode"] in teks or kur["nama"].lower() in teks.lower():
            pos = teks.find(kur["kode"])
            if pos == -1:
                pos = teks.lower().find(kur["nama"].lower())
            if pos != -1:
                snippet = teks[pos:pos+120]
                m_grade = re.search(rf"\b({GRADE})\b", snippet)
                if m_grade:
                    grade = m_grade.group(1)
                    key = (kur["kode"], kur["nama"])
                    if key not in seen:
                        seen.add(key)
                        hasil.append({
                            "kode": kur["kode"],
                            "nama_mk": kur["nama"],
                            "sks": str(kur["sks"]),
                            "nilai": grade
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
    teks, tables = ekstrak_teks_dan_tabel(file_bytes, ext)
    profil = parse_profil(teks)
    mk = parse_matakuliah_pro(teks, tables)
    if profil["ipk"] == "-" and mk:
        profil["ipk"] = hitung_ipk(mk) + " (dihitung otomatis)"
    return {"mahasiswa": profil, "mata_kuliah": mk, "raw_teks": teks}

def buat_ringkasan_kurikulum(mk_list: list[dict], jurusan_pilih: str, peminatan_pilih: str) -> dict:
    passed_codes = {m["kode"] for m in mk_list if str(m["nilai"]).upper() not in ("E", "T", "-")}
    passed_names = {m["nama_mk"].lower() for m in mk_list if str(m["nilai"]).upper() not in ("E", "T", "-")}
   
    kategori_total = {}
    kategori_lulus = {}
    detail_status = []
   
    for kur in KURIKULUM_2026_DATA:
        kat = kur["kategori"]
        if "Teknik Informatika" in jurusan_pilih or "IT" in jurusan_pilih.upper():
            if "Data Science" in peminatan_pilih:
                if "Konsentrasi Network" in kat or "Konsentrasi Software" in kat:
                    continue
            elif "Software" in peminatan_pilih:
                if "Konsentrasi Network" in kat or "Konsentrasi Data Science" in kat:
                    continue
            elif "Network" in peminatan_pilih:
                if "Konsentrasi Software" in kat or "Konsentrasi Data Science" in kat:
                    continue
                   
        kategori_total[kat] = kategori_total.get(kat, 0) + 1
        matched = (kur["kode"] in passed_codes) or (kur["nama"].lower() in passed_names)
        if matched:
            kategori_lulus[kat] = kategori_lulus.get(kat, 0) + 1
            val_nilai = next((m["nilai"] for m in mk_list if m["kode"] == kur["kode"] or m["nama_mk"].lower() == kur["nama"].lower()), "A")
            detail_status.append(f"Mata kuliah **{kur['nama']}** ({kat}) lulus dengan nilai **{val_nilai}**")
        else:
            detail_status.append(f"Mata kuliah **{kur['nama']}** ({kat}) belum lulus / belum diambil")
           
    sisa_per_kategori = {kat: kategori_total[kat] - kategori_lulus.get(kat, 0) for kat in kategori_total}
    return {"detail": detail_status, "sisa": sisa_per_kategori}

# --- FUNGSI MERANGKAI TEKS STATUS ACC SESUAI KEPERLUAN YANG DIPILIH ---
def format_teks_acc(keperluan: str, tanggal_acc: str) -> str:
    return f"Di ACC untuk {keperluan} ({tanggal_acc})"

# --- TAMPILAN KARTU TANDA TANGAN KAPROGDI DI WEB ---
def tampilkan_kartu_ttd_web(keperluan: str, tanggal_acc: str):
    teks_acc = format_teks_acc(keperluan, tanggal_acc)
    html_code = f"""
    <div style="background-color: #ffffff; border: 1.5px solid #222222; padding: 20px 25px; border-radius: 8px; color: #000000; width: fit-content; margin-top: 15px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
        <p style="font-family: Arial, sans-serif; font-size: 16px; font-weight: bold; margin: 0 0 8px 0; color: #000000; letter-spacing: 0.3px;">
            {teks_acc}
        </p>
        <div style="margin: 2px 0 8px -4px;">
            <svg width="220" height="85" viewBox="0 0 220 90" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M 15 50 C 15 15, 75 10, 75 35 C 75 60, 20 75, 45 70 C 65 65, 80 40, 70 30 C 65 25, 60 50, 75 60 C 80 40, 78 20, 80 15 L 80 62 C 80 62, 85 45, 90 40 C 95 35, 95 62, 100 62 C 105 45, 115 50, 115 62" stroke="#000000" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                <path d="M 125 15 L 125 78 M 125 48 C 125 35, 142 30, 138 48 C 135 62, 115 75, 145 68 C 155 60, 160 38, 160 30 L 160 65" stroke="#000000" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                <path d="M 105 60 L 175 52" stroke="#000000" stroke-width="3" stroke-linecap="round"/>
            </svg>
        </div>
        <p style="font-family: Arial, sans-serif; font-size: 15px; font-weight: bold; text-decoration: underline; margin: 0; color: #000000;">
            Dr. Indrastanti Ratna Widiasari, MT.
        </p>
        <p style="font-family: Arial, sans-serif; font-size: 13.5px; margin: 2px 0 0 0; color: #111111;">
            Ketua Program Studi S1 Teknik Informatika
        </p>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)

# --- FUNGSI MENGGAMBAR STEMPEL ACC & MENEMPELKANNYA KE HALAMAN BAWAH PDF ASLI ---
def _gambar_stempel_ttd_pil(teks_acc: str) -> Image.Image:
    w_kartu = 650
    h_kartu = 300
    canvas = Image.new("RGBA", (w_kartu, h_kartu), (255, 255, 255, 0))
    draw = ImageDraw.Draw(canvas)
    try:
        font_bold_hdr = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
        font_bold_nama = ImageFont.truetype("DejaVuSans-Bold.ttf", 21)
        font_reg_jab = ImageFont.truetype("DejaVuSans.ttf", 18)
    except Exception:
        font_bold_hdr = ImageFont.load_default()
        font_bold_nama = ImageFont.load_default()
        font_reg_jab = ImageFont.load_default()

    # Teks Status ACC (contoh: "Di ACC untuk KP (12/11/2026)")
    draw.text((10, 10), teks_acc, fill=(0, 0, 0, 255), font=font_bold_hdr)

    # Goresan tanda tangan Kaprogdi (Presisi tinggi)
    sx, sy = 12, 45
    strokes = [
        [(15, 50), (15, 24), (42, 14), (72, 20), (75, 35), (72, 54), (40, 68), (28, 72), (45, 70), (65, 62), (76, 42), (70, 30), (63, 34), (66, 52), (75, 60), (79, 36), (80, 15), (80, 62), (86, 45), (90, 40), (95, 52), (100, 62), (107, 48), (115, 62)],
        [(125, 15), (125, 78)],
        [(125, 48), (130, 35), (140, 33), (138, 48), (131, 63), (122, 72), (145, 68), (155, 55), (160, 30), (160, 65)],
        [(105, 60), (175, 52)],
    ]
    for path in strokes:
        pts = [(sx + x * 2.2, sy + y * 1.95) for x, y in path]
        draw.line(pts, fill=(0, 0, 0, 255), width=6, joint="curve")

    # Nama Kaprogdi & Garis Bawah
    nama_kaprogdi = "Dr. Indrastanti Ratna Widiasari, MT."
    y_nama = 222
    draw.text((10, y_nama), nama_kaprogdi, fill=(0, 0, 0, 255), font=font_bold_nama)
    draw.line([(10, y_nama + 27), (440, y_nama + 27)], fill=(0, 0, 0, 255), width=3)

    # Jabatan
    draw.text((10, y_nama + 34), "Ketua Program Studi S1 Teknik Informatika", fill=(15, 15, 15, 255), font=font_reg_jab)
    return canvas

def tempel_ttd_ke_pdf_asli(pdf_asli_bytes: bytes, keperluan_acc: str, tanggal_acc: str) -> bytes:
    """
    Menempelkan gambar stempel TTD Kaprogdi langsung ke area kosong paling bawah
    di halaman terakhir PDF asli sesuai keperluan yang dipilih dan lulus.
    """
    if not keperluan_acc:
        return pdf_asli_bytes

    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(io.BytesIO(pdf_asli_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    last_page = writer.pages[-1]
    page_w = float(last_page.mediabox.width)
    page_h = float(last_page.mediabox.height)

    teks_acc = format_teks_acc(keperluan_acc, tanggal_acc)
    stempel_img = _gambar_stempel_ttd_pil(teks_acc)

    target_w = min(page_w - 72.0, 310.0)
    scale = target_w / stempel_img.width
    target_h = stempel_img.height * scale

    pos_x = 36.0
    pos_y = 25.0

    overlay_buf = io.BytesIO()
    canvas_halaman = Image.new("RGBA", (int(page_w * 2), int(page_h * 2)), (255, 255, 255, 0))
    stempel_resized = stempel_img.resize((int(target_w * 2), int(target_h * 2)), Image.Resampling.LANCZOS)

    pil_x = int(pos_x * 2)
    pil_y = int((page_h - pos_y - target_h) * 2)
    canvas_halaman.paste(stempel_resized, (pil_x, max(0, pil_y)), stempel_resized)

    canvas_rgb = Image.new("RGB", canvas_halaman.size, (255, 255, 255))
    canvas_rgb.paste(canvas_halaman, mask=canvas_halaman.split()[3])
    canvas_rgb.save(overlay_buf, format="PDF", resolution=144.0)

    overlay_reader = PdfReader(io.BytesIO(overlay_buf.getvalue()))
    overlay_page = overlay_reader.pages[0]
    last_page.merge_page(overlay_page, over=False)

    out_buf = io.BytesIO()
    writer.write(out_buf)
    return out_buf.getvalue()

# --- FUNGSI EVALUASI SYARAT AKADEMIK ---
def evaluasi_syarat_akademik(mk_list: list[dict]) -> dict:
    total_sks_lulus = 0
    passed_mk_dict = {}
   
    mk_d_atau_e = []
    mk_nilai_e = []
    mk_nilai_d = []
    sks_d = 0
   
    for mk in mk_list:
        nilai = str(mk.get("nilai", "-")).strip().upper()
        try:
            sks = int(mk.get("sks", 0))
        except Exception:
            sks = 0
        nama = str(mk.get("nama_mk", "")).strip()
        kode = str(mk.get("kode", "")).strip()
        nama_lower = nama.lower()
       
        passed_mk_dict[nama_lower] = {"nilai": nilai, "kode": kode, "nama": nama, "sks": sks}
       
        if nilai not in ("E", "T", "-"):
            total_sks_lulus += sks
           
        if nilai in ("D", "D+"):
            mk_nilai_d.append(f"{nama} ({kode}) [Nilai: {nilai}]")
            mk_d_atau_e.append(f"{nama} ({kode}) [Nilai: {nilai}]")
            sks_d += sks
        elif nilai in ("E", "T"):
            mk_nilai_e.append(f"{nama} ({kode}) [Nilai: {nilai}]")
            mk_d_atau_e.append(f"{nama} ({kode}) [Nilai: {nilai}]")

    pesan_rekomendasi = []
    status_per_keperluan = {}

    # 1. EVALUASI SYARAT KERJA PRAKTEK (KP)
    syarat_kelompok = [
        (["pendidikan agama"], "Pendidikan Agama"),
        (["pancasila"], "Pancasila"),
        (["kewarganegaraan"], "Kewarganegaraan"),
        (["bahasa indonesia"], "Bahasa Indonesia"),
        (["metodologi penelitian", "metode penelitian"], "Metode / Metodologi Penelitian"),
    ]
    mk_kp_belum_c = []
    for variasi_nama, label_syarat in syarat_kelompok:
        ditemukan_dan_lulus = False
        for nama_mk_lower, info in passed_mk_dict.items():
            if any(v in nama_mk_lower for v in variasi_nama):
                if BOBOT.get(info["nilai"], 0.0) >= 2.0:
                    ditemukan_dan_lulus = True
                    break
                else:
                    mk_kp_belum_c.append(f"{info['nama']} ({info['kode']}) - Nilai: {info['nilai']}")
                    ditemukan_dan_lulus = True
                    break
        if not ditemukan_dan_lulus:
            mk_kp_belum_c.append(f"{label_syarat} (Belum diambil / Tidak ditemukan)")

    syarat_kp_sks = total_sks_lulus >= 108
    syarat_kp_mk = len(mk_kp_belum_c) == 0
    syarat_kp = syarat_kp_sks and syarat_kp_mk
    status_per_keperluan["KP"] = syarat_kp

    if syarat_kp:
        pesan_rekomendasi.append({"status": True, "jenis": "KP", "teks": "✅ Anda memenuhi syarat dan bisa mendaftar **Kerja Praktek (KP)**."})
    else:
        alasan_kp = []
        if not syarat_kp_sks:
            alasan_kp.append(f"Total SKS lulus baru **{total_sks_lulus} SKS** (Kurang {108 - total_sks_lulus} SKS dari syarat minimal 108 SKS).")
        if not syarat_kp_mk:
            alasan_kp.append("Mata kuliah wajib KP berikut belum mencapai nilai minimal C:\n      - " + "\n      - ".join(mk_kp_belum_c))
        pesan_rekomendasi.append({
            "status": False,
            "jenis": "KP",
            "teks": "❌ **Belum memenuhi syarat KP (Min. 108 SKS & MK Wajib min C).**\n   *Alasan:*\n   * " + "\n   * ".join(alasan_kp)
        })

    # 2. EVALUASI SYARAT TUGAS TALENTA UNGGUL (TTU)
    syarat_ttu = (total_sks_lulus >= 120)
    status_per_keperluan["TTU"] = syarat_ttu

    if syarat_ttu:
        pesan_rekomendasi.append({"status": True, "jenis": "TTU", "teks": "✅ Anda memenuhi syarat dan bisa mendaftar **TTU** (Min. 120 SKS)."})
    else:
        kekurangan_sks_ttu = 120 - total_sks_lulus
        pesan_rekomendasi.append({
            "status": False,
            "jenis": "TTU",
            "teks": f"❌ **Belum memenuhi syarat TTU (< 120 SKS).**\n   *Alasan:* SKS Anda saat ini baru **{total_sks_lulus} SKS**, sehingga masih kurang **{kekurangan_sks_ttu} SKS** dari batas minimal 120 SKS."
        })

    # 3. EVALUASI SYARAT REVIEW PROPOSAL
    syarat_review = (len(mk_d_atau_e) == 0) and (len(mk_list) > 0)
    status_per_keperluan["Review"] = syarat_review

    if syarat_review:
        pesan_rekomendasi.append({"status": True, "jenis": "Review", "teks": "✅ Anda memenuhi syarat dan bisa mendaftar **Review Proposal** (Tidak ada nilai D/E)."})
    else:
        pesan_rekomendasi.append({
            "status": False,
            "jenis": "Review",
            "teks": "❌ **Belum memenuhi syarat Review (Masih ada nilai D/E).**\n   *Alasan:* Terdapat **" + str(len(mk_d_atau_e)) + " mata kuliah** yang bernilai D/E yang harus diperbaiki terlebih dahulu:\n      - " + "\n      - ".join(mk_d_atau_e)
        })

    # 4. EVALUASI SYARAT YUDISIUM
    jumlah_d = len(mk_nilai_d)
    ada_e = len(mk_nilai_e) > 0
    syarat_yudisium_sks = total_sks_lulus >= 144
    syarat_yudisium_d = (jumlah_d <= 3) and (sks_d <= 8)
    syarat_yudisium_e = not ada_e
    syarat_yudisium = syarat_yudisium_sks and syarat_yudisium_d and syarat_yudisium_e
    status_per_keperluan["Yudisium"] = syarat_yudisium

    if syarat_yudisium:
        pesan_rekomendasi.append({"status": True, "jenis": "Yudisium", "teks": "🎉 Selamat! Anda memenuhi syarat untuk mendaftar **Yudisium**."})
    else:
        alasan_yudisium = []
        if not syarat_yudisium_sks:
            alasan_yudisium.append(f"Total SKS lulus baru **{total_sks_lulus} SKS** (Kurang {144 - total_sks_lulus} SKS dari syarat minimal 144 SKS).")
        if ada_e:
            alasan_yudisium.append("Masih terdapat nilai E/T pada mata kuliah berikut:\n      - " + "\n      - ".join(mk_nilai_e))
        if not syarat_yudisium_d:
            alasan_yudisium.append(f"Jumlah nilai D melebihi ketentuan (Maksimal 3 MK & total 8 SKS). Saat ini Anda memiliki **{jumlah_d} MK** bernilai D dengan total **{sks_d} SKS**:\n      - " + "\n      - ".join(mk_nilai_d))
        pesan_rekomendasi.append({
            "status": False,
            "jenis": "Yudisium",
            "teks": "❌ **Belum memenuhi syarat Yudisium.**\n   *Alasan:*\n   * " + "\n   * ".join(alasan_yudisium)
        })

    return {
        "total_sks_lulus": total_sks_lulus,
        "status_per_keperluan": status_per_keperluan,
        "pesan": pesan_rekomendasi
    }

# --- SIDEBAR & NAVIGASI UTAMA ---
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/graduation-cap.png", width=100)
    st.title("👤 Akun Mahasiswa")
    st.write(f"**{USER_NAMA}**")
    st.caption(st.session_state["user_email"])
    if st.button("🚪 Logout", key="btn_logout"):
        for k in ("logged_in", "user_email", "user_nama", "user_nim", "hasil_analisis"):
            st.session_state.pop(k, None)
        st.rerun()
    st.markdown("---")
    st.markdown("### 📌 Petunjuk Penggunaan")
    st.markdown("""
    1. Pilih **Keperluan Pengajuan** (**KP**, **Review**, **TTU**, atau **Yudisium**).
    2. Unggah transkrip nilai (**PDF**, **PNG**, **JPG**, **JPEG**).
    3. Sistem membaca dokumen dan mengecek syarat sesuai keperluan yang dipilih.
    4. Jika lulus syarat, unduh hasil PDF yang sudah dibubuhi tanda tangan ACC Kaprogdi.
    """)
    st.markdown("---")
    st.caption("Dibuat dengan ❤️ menggunakan Streamlit")

btn_col1, btn_col2, btn_col3, btn_col4, _ = st.columns([1.2, 1.8, 2.2, 2.2, 2])
with btn_col1:
    if st.button("🏠 HOME", key="btn_home_nav"):
        st.session_state["active_view"] = "HOME"
        st.rerun()
with btn_col2:
    if st.button("💼 Kerja Praktek (KP)", key="btn_kp_nav"):
        st.session_state["active_view"] = "KP"
        st.rerun()
with btn_col3:
    if st.button("🏆 Tugas Talenta Unggul", key="btn_ttu_nav"):
        st.session_state["active_view"] = "TTU"
        st.rerun()
with btn_col4:
    if st.button("📚 Kurikulum 2026", key="btn_kur_nav"):
        st.session_state["active_view"] = "KURIKULUM"
        st.rerun()
st.markdown("---")

current_view = st.session_state.get("active_view", "HOME")

# --- HALAMAN HOME ---
if current_view == "HOME":
    st.title("Transkrip Nilai Reader & Analisis Kurikulum")
    st.markdown("Ekstrak data mahasiswa dan pantau sisa mata kuliah berdasarkan Jurusan & Peminatan secara otomatis.")
    st.markdown("---")

    # --- 1. PILIHAN KEPERLUAN SEBELUM UPLOAD FILE ---
    keperluan_pilih = st.selectbox(
        "📋 Pilih Keperluan Pengajuan ACC Transkrip",
        ["KP", "Review", "TTU", "Yudisium"],
        help="Pilih satu keperluan yang ingin di-ACC. Tanda tangan akan diberikan pada PDF apabila Anda memenuhi syarat untuk keperluan ini."
    )

    uploaded_file = st.file_uploader(
        f"📂 Unggah File Transkrip Nilai untuk Keperluan **{keperluan_pilih}** (PDF / Gambar)",
        type=["pdf", "png", "jpg", "jpeg"],
    )
   
    if uploaded_file is not None:
        ext = uploaded_file.name.split(".")[-1].lower()
        file_bytes = uploaded_file.getvalue()
       
        with st.spinner("🔄 Membaca file secara otomatis..."):
            try:
                st.session_state["hasil_analisis"] = analisis_transkrip(file_bytes, ext)
                st.session_state["analisis_id"] += 1
            except Exception as e:
                st.error(f"❌ Terjadi kesalahan saat memproses dokumen: {e}")
               
        col_preview, col_result = st.columns([1, 1.3], gap="large")
        with col_preview:
            st.markdown("### 📄 Preview Dokumen")
            if ext in ("png", "jpg", "jpeg"):
                st.image(Image.open(io.BytesIO(file_bytes)), caption=f"File: {uploaded_file.name}", use_container_width=True)
            else:
                st.success(f"📄 File PDF berhasil diunggah: **{uploaded_file.name}**")
                st.info(f"🎯 Keperluan dipilih: **{keperluan_pilih}**")
               
        with col_result:
            st.markdown("### ⚙️ Hasil Analisis Otomatis")
            hasil = st.session_state.get("hasil_analisis")
            if hasil:
                aid = st.session_state["analisis_id"]
                mhs = hasil["mahasiswa"]
                st.markdown("---")
               
                with st.expander("🔍 Lihat Teks Mentah yang Terbaca (Debug OCR)"):
                    st.text(hasil.get("raw_teks", "Tidak ada teks."))
                if not hasil["mata_kuliah"]:
                    st.warning("⚠️ Tidak ada mata kuliah yang terdeteksi otomatis. Silakan lengkapi baris secara manual pada tabel di bawah.")
                else:
                    st.success(f"✨ Ekstraksi selesai: {len(hasil['mata_kuliah'])} mata kuliah terdeteksi.")
               
                st.markdown("#### 👤 Profil Mahasiswa & Pengaturan Jurusan/Minat")
                c1, c2 = st.columns(2)
                with c1:
                    nama_v = st.text_input("Nama", mhs["nama"], key=f"p_nama_{aid}")
                    nim_v = st.text_input("NIM", mhs["nim"], key=f"p_nim_{aid}")
                    jur_v = st.text_input("Jurusan", mhs["jurusan"] if mhs["jurusan"] != "-" else "S1 Teknik Informatika", key=f"p_jur_{aid}")
                with c2:
                    uni_v = st.text_input("Universitas", mhs["universitas"], key=f"p_uni_{aid}")
                    ipk_v = st.text_input("IPK Kumulatif", mhs["ipk"], key=f"p_ipk_{aid}")
                   
                peminatan_pilih = st.selectbox(
                    "🎯 Pilih Peminatan / Konsentrasi Studi",
                    ["Data Science", "Software Engineering", "Network Engineering", "Umum / Belum Pilih"],
                    key=f"peminatan_{aid}"
                )
               
                st.markdown("#### 📚 Daftar Mata Kuliah (bisa diedit)")
                df = pd.DataFrame(hasil["mata_kuliah"], columns=["kode", "nama_mk", "sks", "nilai"])
                df.columns = ["Kode MK", "Nama Mata Kuliah", "SKS", "Nilai"]
                df_edit = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"editor_{aid}")
               
                st.markdown("---")
                st.markdown(f"### 📊 Ringkasan Nilai & Sisa Mata Kuliah ({jur_v} - {peminatan_pilih})")
               
                current_mk_list = [
                    {"kode": str(r["Kode MK"]), "nama_mk": str(r["Nama Mata Kuliah"]), "sks": str(r["SKS"]), "nilai": str(r["Nilai"])}
                    for _, r in df_edit.iterrows()
                ]
               
                ringkasan = buat_ringkasan_kurikulum(current_mk_list, jur_v, peminatan_pilih)
               
                st.markdown("#### 📌 Sisa Mata Kuliah yang Harus Diambil per Kategori:")
                col_sisa1, col_sisa2 = st.columns(2)
                idx = 0
                for kat, sisa in ringkasan["sisa"].items():
                    target_col = col_sisa1 if idx % 2 == 0 else col_sisa2
                    target_col.metric(label=kat, value=f"Sisa {sisa} MK")
                    idx += 1
               
                with st.expander("📝 Lihat Detail Status Mata Kuliah Lulus/Belum"):
                    for item in ringkasan["detail"]:
                        st.markdown(f"- {item}")
               
                # --- HASIL EVALUASI & TANDA TANGAN ACC SESUAI PILIHAN KEPERLUAN ---
                st.markdown("---")
                st.markdown(f"### 🔍 Status Kelayakan & Lembar ACC ({keperluan_pilih})")
                eval_hasil = evaluasi_syarat_akademik(current_mk_list)
                st.metric(label="Total SKS Diperoleh / Lulus", value=f"{eval_hasil['total_sks_lulus']} SKS")
               
                for item in eval_hasil["pesan"]:
                    if item["status"]:
                        st.success(item["teks"])
                    else:
                        st.warning(item["teks"])

                tanggal_hari_ini = datetime.now().strftime("%d/%m/%Y")
                lulus_keperluan_dipilih = eval_hasil["status_per_keperluan"].get(keperluan_pilih, False)

                if lulus_keperluan_dipilih:
                    st.markdown(f"#### ✍️ Lembar Tanda Tangan ACC Kaprogdi — {keperluan_pilih}")
                    tampilkan_kartu_ttd_web(keperluan=keperluan_pilih, tanggal_acc=tanggal_hari_ini)
                else:
                    st.error(f"⛔ Pengajuan untuk **{keperluan_pilih}** belum memenuhi syarat, sehingga tanda tangan ACC tidak diterbitkan.")

                st.markdown("---")
                profil_aktual = {"nama": nama_v, "nim": nim_v, "jurusan": jur_v, "universitas": uni_v, "ipk": ipk_v}
                col_s, col_pdf = st.columns(2)
                with col_s:
                    if st.button("💾 Simpan ke Database", key="btn_simpan_transkrip"):
                        if simpan_ke_database(profil_aktual, current_mk_list):
                            st.success("💾 Data berhasil disimpan ke database lokal!")
                with col_pdf:
                    if ext == "pdf":
                        if lulus_keperluan_dipilih:
                            try:
                                pdf_bertanda_tangan = tempel_ttd_ke_pdf_asli(
                                    pdf_asli_bytes=file_bytes,
                                    keperluan_acc=keperluan_pilih,
                                    tanggal_acc=tanggal_hari_ini,
                                )
                                nama_file_unduh = f"Transkrip_ACC_{keperluan_pilih}_{nim_v}.pdf"
                                st.download_button(
                                    f"📄 Unduh file PDF (ACC {keperluan_pilih})",
                                    data=pdf_bertanda_tangan,
                                    file_name=nama_file_unduh,
                                    mime="application/pdf",
                                )
                            except ImportError:
                                st.info("Install `pypdf` (`pip install pypdf`) untuk mengaktifkan fitur penempelan TTD pada PDF.")
                            except Exception as e:
                                st.error(f"Gagal menempelkan tanda tangan ke PDF: {e}")
                        else:
                            st.button(
                                f"🔒 Unduh PDF Terkunci (Syarat {keperluan_pilih} Belum Lulus)",
                                disabled=True,
                                key="btn_pdf_locked"
                            )
                    else:
                        st.warning("⚠️ Unggah file dalam format **PDF** untuk mengunduh PDF bertanda tangan ACC.")

# --- HALAMAN KURIKULUM ---
elif current_view == "KURIKULUM":
    st.title("📚 Daftar Kurikulum 2026")
    st.markdown("Berikut adalah daftar alir Kurikulum S1 Teknik Informatika tahun 2026 yang terhubung dengan sistem database:")
   
    conn = sqlite3.connect(DB_PATH)
    df_kur = pd.read_sql_query("SELECT kode_mk AS 'Kode MK', nama_mk AS 'Nama Mata Kuliah', sks AS 'SKS', kategori AS 'Kategori' FROM kurikulum_2026", conn)
    conn.close()
    col_filter, col_search = st.columns([1, 2])
    with col_filter:
        kategori_opt = ["Semua Kategori"] + list(df_kur["Kategori"].unique())
        selected_kat = st.selectbox("Filter Kategori MK", kategori_opt)
    with col_search:
        search_query = st.text_input("Cari Kode / Nama Mata Kuliah", placeholder="Ketik kata kunci...")
    filtered_df = df_kur.copy()
    if selected_kat != "Semua Kategori":
        filtered_df = filtered_df[filtered_df["Kategori"] == selected_kat]
    if search_query:
        filtered_df = filtered_df[
            filtered_df["Kode MK"].str.contains(search_query, case=False, na=False) |
            filtered_df["Nama Mata Kuliah"].str.contains(search_query, case=False, na=False)
        ]
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    st.info(f"Total Mata Kuliah Ditampilkan: {len(filtered_df)} MK")

# --- HALAMAN TTU ---
elif current_view == "TTU":
    st.title("🏆 Tugas Talenta Unggul (TTU) & Review")
    st.markdown("Kelola pendaftaran Tugas Talenta Unggul, Review Proposal, dan Yudisium.")
   
    tab1, tab2, tab3, tab4 = st.tabs(["Pendaftaran TTU", "Review Proposal", "Yudisium", "Sarasehan Magang"])
   
    with tab1:
        st.subheader("Form Pendaftaran TTU 1")
        st.info("ℹ️ **Syarat TTU 1:** Sudah mengambil minimal 120 SKS dan MK Wajib sudah diambil & lulus.")
        with st.form("form_pendaftaran_ttu"):
            c1, c2 = st.columns(2)
            with c1:
                t_nim = st.text_input("NIM", value=USER_NIM)
                t_nama = st.text_input("Nama Mahasiswa", value=USER_NAMA)
                t_prodi = st.text_input("Program Studi", value="S1 Teknik Informatika")
            with c2:
                t_peminatan = st.selectbox("Peminatan", ["Data Science", "Software Engineering", "Network Engineering"])
                t_status = st.selectbox("Status", ["Aktif", "Cuti"])
           
            ttu_pilih = st.multiselect(
                "Pilih Mata Kuliah TTU",
                ["TC851 - Tugas Talenta Unggul 1", "TC852 - Tugas Talenta Unggul 2", "TC853 - Tugas Talenta Unggul 3"]
            )
            t_judul = st.text_area("Judul Proposal / Tugas Talenta Unggul")
           
            c3, c4 = st.columns(2)
            with c3:
                t_pemb1 = st.text_input("Pembimbing 1")
            with c4:
                t_pemb2 = st.text_input("Pembimbing 2")
               
            submitted_ttu = st.form_submit_button("Daftar TTU")
            if submitted_ttu:
                if simpan_ttu(t_nim, t_nama, t_prodi, t_peminatan, ttu_pilih, t_status, t_judul, t_pemb1, t_pemb2):
                    st.success("✅ Pendaftaran TTU berhasil disimpan!")
                   
    with tab2:
        st.subheader("Pendaftaran Review Proposal")
        st.info("ℹ️ **Syarat Review:** Tidak ada nilai D/E dan sedang mengambil TTU 2 dan atau TTU 3.")
        with st.form("form_pendaftaran_review"):
            r_nim = st.text_input("NIM", value=USER_NIM)
            r_nama = st.text_input("Nama Mahasiswa", value=USER_NAMA)
            r_prodi = st.text_input("Program Studi", value="S1 Teknik Informatika")
            r_peminatan = st.selectbox("Peminatan Review", ["Data Science", "Software Engineering", "Network Engineering"])
            r_judul = st.text_area("Judul Proposal untuk Review")
           
            rc1, rc2 = st.columns(2)
            with rc1:
                r_pemb1 = st.text_input("Pembimbing 1 (Review)")
                r_rev1 = st.text_input("Reviewer 1")
            with rc2:
                r_pemb2 = st.text_input("Pembimbing 2 (Review)")
                r_rev2 = st.text_input("Reviewer 2")
               
            submitted_review = st.form_submit_button("Daftar Review")
            if submitted_review:
                if simpan_review(r_nim, r_nama, r_prodi, r_peminatan, r_judul, r_pemb1, r_pemb2, r_rev1, r_rev2):
                    st.success("✅ Pendaftaran Review berhasil disimpan!")
    with tab3:
        st.subheader("Pendaftaran Yudisium")
        st.info("ℹ️ **Syarat Yudisium:** Minimal total SKS 144, tidak ada nilai E, boleh ada nilai D maksimal 3 MK dengan total 8 SKS, mata kuliah wajib minimal C, sudah ambil KP dan LKP, serta sudah ada TTU 1, TTU 2, dan TTU 3.")
        if st.button("Ajukan Pendaftaran Yudisium"):
            if simpan_yudisium():
                st.success("🎉 Pendaftaran Yudisium berhasil diajukan!")
    with tab4:
        st.subheader("Pendaftaran Sarasehan Magang")
        st.markdown("Status pendaftaran orientasi Sarasehan Magang.")
        if not st.session_state["sarasehan_registered"]:
            if st.button("Daftar Sarasehan Magang"):
                if simpan_sarasehan("Terdaftar"):
                    st.session_state["sarasehan_registered"] = True
                    st.success("✅ Berhasil mendaftar Sarasehan Magang!")
        else:
            st.info("ℹ️ Anda sudah terdaftar dalam Sarasehan Magang.")

# --- HALAMAN KP ---
elif current_view == "KP":
    st.title("💼 Kerja Praktek (KP)")
    st.markdown("Kelola permohonan surat dan pendaftaran Kerja Praktek Anda.")
   
    tab_kp1, tab_kp2 = st.tabs(["Permohonan Surat KP", "Pendaftaran KP"])
   
    with tab_kp1:
        st.subheader("Form Permohonan Surat Pengantar KP")
        st.info("ℹ️ **Syarat KP:** Sudah mengambil 108 SKS serta mengambil MK Pendidikan Agama, Pancasila, Kewarganegaraan, Bahasa Indonesia, dan Metodologi Penelitian dengan nilai minimal C.")
        with st.form("form_surat_kp"):
            instansi = st.text_input("Nama Instansi / Perusahaan")
            alamat = st.text_area("Alamat Instansi")
            ditujukan = st.text_input("Surat Ditujukan Kepada (Cth: HRD Manager)")
           
            submitted_surat = st.form_submit_button("Ajukan Surat Permohonan")
            if submitted_surat:
                if simpan_surat_kp(instansi, alamat, ditujukan):
                    st.success("✅ Permohonan surat KP berhasil diajukan!")
                   
    with tab_kp2:
        st.subheader("Form Pendaftaran Kerja Praktek")
        with st.form("form_pendaftaran_kp"):
            kp_nim = st.text_input("NIM", value=USER_NIM)
            kp_nama = st.text_input("Nama", value=USER_NAMA)
            kp_mk = st.multiselect("Mata Kuliah KP yang Diambil", ["TC821 - Kerja Praktek (5 SKS)", "TC822 - Laporan Kerja Praktek (5 SKS)"])
            kp_tempat = st.text_input("Tempat / Perusahaan KP")
           
            submitted_kp = st.form_submit_button("Daftar Kerja Praktek")
            if submitted_kp:
                if simpan_kp(kp_nim, kp_nama, kp_mk, kp_tempat):
                    st.success("✅ Pendaftaran Kerja Praktek berhasil disimpan!")
