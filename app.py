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
        CREATE TABLE IF NOT EXISTS kurikulum_2026 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kode_mk TEXT UNIQUE, nama_mk TEXT, sks INTEGER, kategori TEXT
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

def buat_ringkasan_kurikulum(mk_list: list[dict], jurusan_pilih: str, peminatan_pilih: str) -> dict:
    passed_codes = {m["kode"] for m in mk_list if str(m["nilai"]).upper() not in ("E", "T", "-")}
    passed_names = {m["nama_mk"].lower() for m in mk_list if str(m["nilai"]).upper() not in ("E", "T", "-")}
    
    kategori_total = {}
    kategori_lulus = {}
    detail_status = []
    
    for kur in KURIKULUM_2026_DATA:
        kat = kur["kategori"]
        
        # Filter relevansi berdasarkan jurusan dan peminatan
        if "Teknik Informatika" in jurusan_pilih or "IT" in jurusan_pilih.upper():
            if "Data Science" in peminatan_pilih:
                # Jika IT & Data Science, abaikan konsentrasi lain (Network / Software) kecuali MK Umum/Wajib Prodi/DS/Pilihan/KP+TTU
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
            # Cari nilai pastinya
            val_nilai = next((m["nilai"] for m in mk_list if m["kode"] == kur["kode"] or m["nama_mk"].lower() == kur["nama"].lower()), "A")
            detail_status.append(f"Mata kuliah **{kur['nama']}** ({kat}) lulus dengan nilai **{val_nilai}**")
        else:
            detail_status.append(f"Mata kuliah **{kur['nama']}** ({kat}) belum lulus / belum diambil")
            
    sisa_per_kategori = {kat: kategori_total[kat] - kategori_lulus.get(kat, 0) for kat in kategori_total}
    return {"detail": detail_status, "sisa": sisa_per_kategori}
st.session_state.setdefault("active_view", "HOME")
st.session_state.setdefault("sarasehan_registered", False)
st.session_state.setdefault("analisis_id", 0)

with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/graduation-cap.png", width=100)
    st.title("👤 Akun admin")
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
    2. Sistem membaca dokumen **secara otomatis**.
    3. Pilih Jurusan dan Peminatan Anda.
    4. Periksa sisa mata kuliah sesuai galir.
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

if st.session_state["active_view"] == "HOME":
    st.title("Transkrip Nilai Reader & Analisis Kurikulum")
    st.markdown("Ekstrak data mahasiswa dan pantau sisa mata kuliah berdasarkan Jurusan & Peminatan secara otomatis.")
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "📂 Unggah File Transkrip Nilai (PDF / Gambar)",
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
                
        col_preview, col_result = st.columns([1, 1.2], gap="large")
        with col_preview:
            st.markdown("### 📄 Preview Dokumen")
            if ext in ("png", "jpg", "jpeg"):
                st.image(Image.open(io.BytesIO(file_bytes)),
                         caption=f"File: {uploaded_file.name}", use_container_width=True)
            else:
                st.success(f"📄 File PDF berhasil diunggah: **{uploaded_file.name}**")
                
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
                    st.warning(
                        "⚠️ Tidak ada mata kuliah yang terdeteksi otomatis. "
                        "Silakan lengkapi baris secara manual pada tabel di bawah."
                    )
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
                    
                # Pilihan Peminatan/Konsentrasi interaktif untuk menyesuaikan sisa matkul
                peminatan_pilih = st.selectbox(
                    "🎯 Pilih Peminatan / Konsentrasi Studi",
                    ["Data Science", "Software Engineering", "Network Engineering", "Umum / Belum Pilih"],
                    key=f"peminatan_{aid}"
                )
                
                st.markdown("#### 📚 Daftar Mata Kuliah (bisa diedit)")
                df = pd.DataFrame(hasil["mata_kuliah"], columns=["kode", "nama_mk", "sks", "nilai"])
                df.columns = ["Kode MK", "Nama Mata Kuliah", "SKS", "Nilai"]
                df_edit = st.data_editor(
                    df, num_rows="dynamic", use_container_width=True,
                    hide_index=True, key=f"editor_{aid}",
                )
                
                st.markdown("---")
                st.markdown(f"### 📊 Ringkasan Nilai & Sisa Mata Kuliah ({jur_v} - {peminatan_pilih})")
                
                current_mk_list = [
                    {"kode": str(r["Kode MK"]), "nama_mk": str(r["Nama Mata Kuliah"]),
                     "sks": str(r["SKS"]), "nilai": str(r["Nilai"])}
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
                
                st.markdown("---")
                col_s, col_d = st.columns(2)
                with col_s:
                    if st.button("💾 Simpan ke Database", key="btn_simpan_transkrip"):
                        profil = {"nama": nama_v, "nim": nim_v, "jurusan": jur_v,
                                  "universitas": uni_v, "ipk": ipk_v}
                        if simpan_ke_database(profil, current_mk_list):
                            st.success("💾 Data berhasil disimpan ke database lokal!")
                with col_d:
                    st.download_button(
                        "📥 Unduh Data Mata Kuliah (.CSV)",
                        data=df_edit.to_csv(index=False).encode("utf-8"),
                        file_name="transkrip_extracted.csv",
                        mime="text/csv",
                    )

elif st.session_state["active_view"] == "KURIKULUM":
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
elif st.session_state["active_view"] == "TTU":
    st.title("🏆 Tugas Talenta Unggul (TTU)")
    st.markdown("Kelola pendaftaran Tugas Talenta Unggul dan seminar Anda di sini.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Pendaftaran TTU", "Review Proposal", "Yudisium", "Sarasehan Magang"])
    
    with tab1:
        st.subheader("Form Pendaftaran TTU")
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
        st.markdown("Pastikan seluruh persyaratan kelulusan telah terpenuhi.")
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

elif st.session_state["active_view"] == "KP":
    st.title("💼 Kerja Praktek (KP)")
    st.markdown("Kelola permohonan surat dan pendaftaran Kerja Praktek Anda.")
    
    tab_kp1, tab_kp2 = st.tabs(["Permohonan Surat KP", "Pendaftaran KP"])
    
    with tab_kp1:
        st.subheader("Form Permohonan Surat Pengantar KP")
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
