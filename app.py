import hmac
import io
import re
import sqlite3
import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

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
SKIP_PREFIX = ("jumlah", "total", "ipk", "indeks", "semester", "sks", "program", "nama", "nim", "fakultas", "universitas", "no", "kode")
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
    return {
        "nama": _cari(r"\bNama(?:\s+Mahasiswa)?\s*[:\-]\s*([^\n]+)", teks),
        "nim": _cari(r"\b(?:NIM|N\.I\.M)\s*[:\-]?\s*(\d{6,12})", teks),
        "jurusan": _cari(r"(?:Program\s+Studi|Prodi|Jurusan)\s*[:\-]\s*([^\n]+)", teks),
        "universitas": universitas,
        "ipk": _cari(r"(?:IPK|Indeks\s+Prestasi\s+Kumulatif|GPA)[^\d\n]{0,30}(\d[.,]\d{1,2})", teks).replace(",", "."),
    }

def parse_matakuliah_pro(teks: str, tables: list) -> list[dict]:
    hasil = []
    seen = set()
    if tables:
        for row in tables:
            row_text = " ".join([str(c) for c in row if c])
            m_grade = re.search(rf"\b({GRADE})\b", row_text)
            if m_grade:
                grade = m_grade.group(1)
                m_sks = re.search(r"\b([1-5])\b", row_text)
                sks = m_sks.group(1) if m_sks else "3"
                m_kode = re.search(r"\b([A-Z]{2,5}\s?\d{2,5})\b", row_text)
                kode = m_kode.group(1).replace(" ", "") if m_kode else "-"
               
                nama_mk = "-"
                for k in KURIKULUM_2026_DATA:
                    if k["kode"] == kode:
                        nama_mk = k["nama"]
                        break
                if nama_mk == "-":
                    clean_txt = row_text
                    if m_kode: clean_txt = clean_txt.replace(m_kode.group(1), "")
                    clean_txt = re.sub(rf"\b{grade}\b", "", clean_txt)
                    clean_txt = re.sub(r"\b[1-5]\b", "", clean_txt)
                    nama_mk = clean_txt.strip(" -./")
               
                if nama_mk and len(nama_mk) > 2 and not any(nama_mk.lower().startswith(p) for p in SKIP_PREFIX):
                    key = (kode, nama_mk)
                    if key not in seen:
                        seen.add(key)
                        hasil.append({"kode": kode, "nama_mk": nama_mk, "sks": sks, "nilai": grade})
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
# --- FUNGSI TAMPILKAN TANDA TANGAN ACC KAPROGDI ---
def tampilkan_ttd_kaprogdi(jenis_acc: str, tanggal_acc: str = "24/08/2026"):
    """
    Menampilkan Tanda Tangan ACC Kaprogdi persis sampel gambar:
    - Text: ACC [KP/TTU 1/Review/Yudisium] (Tanggal)
    - Coretan Tanda Tangan Hitam Presisi
    - Nama Lengkap Kaprogdi Bergaris Bawah
    - Jabatan Ketua Program Studi S1 Teknik Informatika
    """
    html_code = f"""
    <div style="background-color: #ffffff; padding: 25px 35px; border-radius: 8px; color: #000000; width: fit-content; margin-top: 15px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
        <p style="font-family: Arial, sans-serif; font-size: 19px; font-weight: bold; margin: 0 0 10px 0; color: #000000; letter-spacing: 0.5px;">
            ACC {jenis_acc} &nbsp;&nbsp;({tanggal_acc})
        </p>
        <div style="margin: 5px 0 10px -5px;">
            <svg width="220" height="90" viewBox="0 0 220 90" fill="none" xmlns="http://www.w3.org/2000/svg">
                <!-- SVG Tanda Tangan Hitam Presisi -->
                <path d="M 15 50 C 15 15, 75 10, 75 35 C 75 60, 20 75, 45 70 C 65 65, 80 40, 70 30 C 65 25, 60 50, 75 60 C 80 40, 78 20, 80 15 L 80 62 C 80 62, 85 45, 90 40 C 95 35, 95 62, 100 62 C 105 45, 115 50, 115 62" stroke="#000000" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                <path d="M 125 15 L 125 78 M 125 48 C 125 35, 142 30, 138 48 C 135 62, 115 75, 145 68 C 155 60, 160 38, 160 30 L 160 65" stroke="#000000" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                <path d="M 105 60 L 175 52" stroke="#000000" stroke-width="3" stroke-linecap="round"/>
            </svg>
        </div>
        <p style="font-family: Arial, sans-serif; font-size: 16px; font-weight: bold; text-decoration: underline; margin: 0; color: #000000;">
            Dr. Indrastanti Ratna Widiasari, MT.
        </p>
        <p style="font-family: Arial, sans-serif; font-size: 15px; margin: 3px 0 0 0; color: #111111;">
            Ketua Program Studi S1 Teknik Informatika
        </p>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)

# --- FUNGSI EVALUASI SYARAT AKADEMIK HANYA SPESIFIK KEPERLUAN YANG DIPILIH ---
def evaluasi_syarat_spesifik(mk_list: list[dict], keperluan: str) -> dict:
    total_sks_lulus = 0
    list_nilai_huruf = []
    passed_mk_dict = {}
   
    mk_d_atau_e = []
    mk_nilai_e = []
    mk_nilai_d = []
    sks_d = 0
   
    for mk in mk_list:
        nilai = str(mk.get("nilai", "-")).strip().upper()
        try:
            sks = int(mk.get("sks", 0))
        except:
            sks = 0
        nama = str(mk.get("nama_mk", "")).strip()
        kode = str(mk.get("kode", "")).strip()
        nama_lower = nama.lower()
       
        list_nilai_huruf.append(nilai)
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

    is_lulus = False
    pesan = ""
    label_acc = ""

    # 1. EVALUASI KHUSUS KERJA PRAKTEK (KP)
    if keperluan == "KP":
        label_acc = "KP"
        mk_kp_syarat = ["pendidikan agama", "pancasila", "kewarganegaraan", "bahasa indonesia", "metodologi penelitian"]
        mk_kp_belum_c = []
        for syarat in mk_kp_syarat:
            ditemukan_dan_lulus = False
            for nama_mk_lower, info in passed_mk_dict.items():
                if syarat in nama_mk_lower:
                    if BOBOT.get(info["nilai"], 0.0) >= 2.0:
                        ditemukan_dan_lulus = True
                        break
                    else:
                        mk_kp_belum_c.append(f"{info['nama']} ({info['kode']}) - Nilai: {info['nilai']}")
                        ditemukan_dan_lulus = True
                        break
            if not ditemukan_dan_lulus:
                mk_kp_belum_c.append(f"{syarat.title()} (Belum diambil / Tidak ditemukan)")

        syarat_sks = total_sks_lulus >= 108
        syarat_mk = len(mk_kp_belum_c) == 0
        is_lulus = syarat_sks and syarat_mk

        if is_lulus:
            pesan = "✅ Selamat! Anda memenuhi syarat untuk mendaftar **Kerja Praktek (KP)**."
        else:
            alasan = []
            if not syarat_sks:
                alasan.append(f"Total SKS lulus Anda baru **{total_sks_lulus} SKS** (Kurang {108 - total_sks_lulus} SKS dari syarat minimal 108 SKS).")
            if not syarat_mk:
                alasan.append("Mata kuliah wajib KP berikut belum mencapai nilai minimal C:\n      - " + "\n      - ".join(mk_kp_belum_c))
            pesan = "❌ **Belum memenuhi syarat KP (Min. 108 SKS & MK Wajib min C).**\n   *Alasan:*\n   * " + "\n   * ".join(alasan)

    # 2. EVALUASI KHUSUS REVIEW PROPOSAL
    elif keperluan == "Review":
        label_acc = "Review Proposal"
        is_lulus = (len(mk_d_atau_e) == 0)
        if is_lulus:
            pesan = "✅ Selamat! Anda memenuhi syarat untuk mendaftar **Review Proposal** (Tidak ada nilai D/E)."
        else:
            pesan = f"❌ **Belum memenuhi syarat Review (Masih ada nilai D/E).**\n   *Alasan:* Terdapat **{len(mk_d_atau_e)} mata kuliah** bernilai D/E yang harus diperbaiki terlebih dahulu:\n      - " + "\n      - ".join(mk_d_atau_e)

    # 3. EVALUASI KHUSUS TTU (TUGAS TALENTA UNGGUL 1)
    elif keperluan == "TTU":
        label_acc = "TTU 1"
        is_lulus = (total_sks_lulus >= 120)
        if is_lulus:
            pesan = "✅ Selamat! Anda memenuhi syarat SKS untuk mendaftar **TTU 1** (Minimal 120 SKS)."
        else:
            kekurangan = 120 - total_sks_lulus
            pesan = f"❌ **Belum memenuhi syarat TTU 1 (< 120 SKS).**\n   *Alasan:* SKS lulus Anda saat ini baru **{total_sks_lulus} SKS**, sehingga masih kurang **{kekurangan} SKS** dari batas minimal 120 SKS."

    # 4. EVALUASI KHUSUS YUDISIUM
    elif keperluan == "Yudisium":
        label_acc = "Yudisium"
        jumlah_d = len(mk_nilai_d)
        ada_e = len(mk_nilai_e) > 0
        syarat_sks = total_sks_lulus >= 144
        syarat_d = (jumlah_d <= 3) and (sks_d <= 8)
        syarat_e = not ada_e
        is_lulus = syarat_sks and syarat_d and syarat_e

        if is_lulus:
            pesan = "🎉 Selamat! Anda memenuhi kelayakan untuk mendaftar **Yudisium**."
        else:
            alasan = []
            if not syarat_sks:
                alasan.append(f"Total SKS lulus baru **{total_sks_lulus} SKS** (Kurang {144 - total_sks_lulus} SKS dari syarat minimal 144 SKS).")
            if ada_e:
                alasan.append(f"Masih terdapat nilai E/T pada mata kuliah berikut:\n      - " + "\n      - ".join(mk_nilai_e))
            if not syarat_d:
                alasan.append(f"Jumlah nilai D melebihi ketentuan (Maksimal 3 MK & total 8 SKS). Saat ini Anda memiliki **{jumlah_d} MK** bernilai D dengan total **{sks_d} SKS**:\n      - " + "\n      - ".join(mk_nilai_d))
            pesan = "❌ **Belum memenuhi syarat Yudisium.**\n   *Alasan:*\n   * " + "\n   * ".join(alasan)

    return {
        "total_sks_lulus": total_sks_lulus,
        "is_lulus": is_lulus,
        "pesan": pesan,
        "label_acc": label_acc
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
    1. Unggah transkrip nilai (**PDF**, **PNG**, **JPG**, **JPEG**).
    2. Pilih **Keperluan Pengajuan** Anda.
    3. Periksa status memenuhi/tidak memenuhi syarat khusus keperluan tersebut & **Tanda Tangan ACC**.
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
    st.title("Transkrip Nilai Reader & Evaluasi Akademik")
    st.markdown("Ekstrak data transkrip nilai dan periksa kelayakan pendaftaran secara instan.")
    st.markdown("---")
   
    uploaded_file = st.file_uploader(
        "📂 Unggah File Transkrip Nilai (PDF / Gambar)",
        type=["pdf", "png", "jpg", "jpeg"],
    )
   
    if uploaded_file is not None:
        ext = uploaded_file.name.split(".")[-1].lower()
        file_bytes = uploaded_file.getvalue()
       
        # 1. PILIHAN KEPERLUAN MUNCUL DULUAN SETELAH UPLOAD FILE (SEBELUM MEMPROSES HASIL)
        st.markdown("---")
        keperluan_pilihan = st.selectbox(
            "📌 Pilih Keperluan Pengajuan Akademik Anda:",
            [
                "-- Pilih Keperluan Pengajuan --",
                "KP",
                "Review",
                "TTU",
                "Yudisium"
            ],
            key="pilihan_keperluan_utama"
        )

        # 2. HASIL DAN KELAYAKAN HANYA MUNCUL APABILA PENGGUNA SUDAH MEMILIH KEPERLUAN
        if keperluan_pilihan != "-- Pilih Keperluan Pengajuan --":
            with st.spinner("🔄 Membaca dan menganalisis transkrip nilai..."):
                try:
                    st.session_state["hasil_analisis"] = analisis_transkrip(file_bytes, ext)
                    st.session_state["analisis_id"] += 1
                except Exception as e:
                    st.error(f"❌ Terjadi kesalahan saat memproses dokumen: {e}")
                   
            col_preview, col_result = st.columns([1, 1.2], gap="large")
            with col_preview:
                st.markdown("### 📄 Preview Dokumen")
                if ext in ("png", "jpg", "jpeg"):
                    st.image(Image.open(io.BytesIO(file_bytes)), caption=f"File: {uploaded_file.name}", use_container_width=True)
                else:
                    st.success(f"📄 File PDF berhasil diunggah: **{uploaded_file.name}**")
                   
            with col_result:
                hasil = st.session_state.get("hasil_analisis")
                if hasil:
                    aid = st.session_state["analisis_id"]
                    mhs = hasil["mahasiswa"]
                   
                    st.markdown("### 👤 Profil Mahasiswa & Peminatan")
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
                   
                    current_mk_list = [
                        {"kode": str(r["Kode MK"]), "nama_mk": str(r["Nama Mata Kuliah"]), "sks": str(r["SKS"]), "nilai": str(r["Nilai"])}
                        for _, r in df_edit.iterrows()
                    ]
                   
                    # --- EVALUASI KHUSUS UNTUK KEPERLUAN YANG DIPILIH SAJA ---
                    st.markdown("---")
                    st.markdown(f"### 🔍 Hasil Evaluasi Kelayakan: Keperluan {keperluan_pilihan}")
                   
                    hasil_eval = evaluasi_syarat_spesifik(current_mk_list, keperluan_pilihan)
                    st.metric(label="Total SKS Diperoleh / Lulus", value=f"{hasil_eval['total_sks_lulus']} SKS")
                   
                    if hasil_eval["is_lulus"]:
                        st.success(hasil_eval["pesan"])
                        # JIKA MEMENUHI SYARAT -> TANDA TANGAN KAPROGDI MUNCUL
                        tampilkan_ttd_kaprogdi(jenis_acc=hasil_eval["label_acc"], tanggal_acc="24/08/2026")
                    else:
                        st.warning(hasil_eval["pesan"])
                        # JIKA TIDAK MEMENUHI SYARAT -> TANDA TANGAN TIDAK MUNCUL
                        st.error("🔒 Tanda tangan ACC Kaprogdi belum dapat diterbitkan karena syarat belum terpenuhi.")

                    st.markdown("---")
                    col_s, col_d = st.columns(2)
                    with col_s:
                        if st.button("💾 Simpan ke Database", key="btn_simpan_transkrip"):
                            profil = {"nama": nama_v, "nim": nim_v, "jurusan": jur_v, "universitas": uni_v, "ipk": ipk_v}
                            if simpan_ke_database(profil, current_mk_list):
                                st.success("💾 Data berhasil disimpan ke database lokal!")
                    with col_d:
                        st.download_button(
                            "📥 Unduh Data Mata Kuliah (.CSV)",
                            data=df_edit.to_csv(index=False).encode("utf-8"),
                            file_name="transkrip_extracted.csv",
                            mime="text/csv",
                        )
        else:
            st.info("💡 **Silakan pilih Keperluan Pengajuan Akademik Anda di atas terlebih dahulu untuk melihat hasil evaluasi dan tanda tangan.**")

# --- HALAMAN KURIKULUM ---
elif current_view == "KURIKULUM":
    st.title("📚 Daftar Kurikulum 2026")
    st.markdown("Berikut adalah daftar alir Kurikulum S1 Teknik Informatika tahun 2026:")
   
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

# --- HALAMAN TTU ---
elif current_view == "TTU":
    st.title("🏆 Tugas Talenta Unggul (TTU) & Review")
    tab1, tab2, tab3, tab4 = st.tabs(["Pendaftaran TTU", "Review Proposal", "Yudisium", "Sarasehan Magang"])
   
    with tab1:
        st.subheader("Form Pendaftaran TTU 1")
        with st.form("form_pendaftaran_ttu"):
            t_nim = st.text_input("NIM", value=USER_NIM)
            t_nama = st.text_input("Nama Mahasiswa", value=USER_NAMA)
            t_prodi = st.text_input("Program Studi", value="S1 Teknik Informatika")
            t_peminatan = st.selectbox("Peminatan", ["Data Science", "Software Engineering", "Network Engineering"])
            t_status = st.selectbox("Status", ["Aktif", "Cuti"])
            ttu_pilih = st.multiselect("Pilih Mata Kuliah TTU", ["TC851 - Tugas Talenta Unggul 1", "TC852 - Tugas Talenta Unggul 2", "TC853 - Tugas Talenta Unggul 3"])
            t_judul = st.text_area("Judul Proposal / Tugas Talenta Unggul")
            t_pemb1 = st.text_input("Pembimbing 1")
            t_pemb2 = st.text_input("Pembimbing 2")
            if st.form_submit_button("Daftar TTU"):
                if simpan_ttu(t_nim, t_nama, t_prodi, t_peminatan, ttu_pilih, t_status, t_judul, t_pemb1, t_pemb2):
                    st.success("✅ Pendaftaran TTU berhasil disimpan!")
                   
    with tab2:
        st.subheader("Pendaftaran Review Proposal")
        with st.form("form_pendaftaran_review"):
            r_nim = st.text_input("NIM", value=USER_NIM)
            r_nama = st.text_input("Nama Mahasiswa", value=USER_NAMA)
            r_prodi = st.text_input("Program Studi", value="S1 Teknik Informatika")
            r_peminatan = st.selectbox("Peminatan Review", ["Data Science", "Software Engineering", "Network Engineering"])
            r_judul = st.text_area("Judul Proposal untuk Review")
            r_pemb1 = st.text_input("Pembimbing 1")
            r_pemb2 = st.text_input("Pembimbing 2")
            r_rev1 = st.text_input("Reviewer 1")
            r_rev2 = st.text_input("Reviewer 2")
            if st.form_submit_button("Daftar Review"):
                if simpan_review(r_nim, r_nama, r_prodi, r_peminatan, r_judul, r_pemb1, r_pemb2, r_rev1, r_rev2):
                    st.success("✅ Pendaftaran Review berhasil disimpan!")

    with tab3:
        st.subheader("Pendaftaran Yudisium")
        if st.button("Ajukan Pendaftaran Yudisium"):
            if simpan_yudisium():
                st.success("🎉 Pendaftaran Yudisium berhasil diajukan!")

    with tab4:
        st.subheader("Pendaftaran Sarasehan Magang")
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
    tab_kp1, tab_kp2 = st.tabs(["Permohonan Surat KP", "Pendaftaran KP"])
   
    with tab_kp1:
        st.subheader("Form Permohonan Surat Pengantar KP")
        with st.form("form_surat_kp"):
            instansi = st.text_input("Nama Instansi / Perusahaan")
            alamat = st.text_area("Alamat Instansi")
            ditujukan = st.text_input("Surat Ditujukan Kepada (Cth: HRD Manager)")
            if st.form_submit_button("Ajukan Surat Permohonan"):
                if simpan_surat_kp(instansi, alamat, ditujukan):
                    st.success("✅ Permohonan surat KP berhasil diajukan!")
                   
    with tab_kp2:
        st.subheader("Form Pendaftaran Kerja Praktek")
        with st.form("form_pendaftaran_kp"):
            kp_nim = st.text_input("NIM", value=USER_NIM)
            kp_nama = st.text_input("Nama", value=USER_NAMA)
            kp_mk = st.multiselect("Mata Kuliah KP yang Diambil", ["TC821 - Kerja Praktek (5 SKS)", "TC822 - Laporan Kerja Praktek (5 SKS)"])
            kp_tempat = st.text_input("Tempat / Perusahaan KP")
            if st.form_submit_button("Daftar Kerja Praktek"):
                if simpan_kp(kp_nim, kp_nama, kp_mk, kp_tempat):
                    st.success("✅ Pendaftaran Kerja Praktek berhasil disimpan!")
