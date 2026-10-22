import json
import os
import pandas as pd
from PIL import Image
from pydantic import BaseModel, Field
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="Transkrip Nilai Reader",
    page_icon="logo_transkrip.png",  
    layout="wide"
)

st.markdown(
    """
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        background: linear-gradient(90deg, #4f46e5 0%, #3b82f6 100%);
        color: white;
        border: none;
        padding: 0.6rem 1rem;
        transition: 0.3s;
    }
    .stButton>button:hover {
        opacity: 0.9;
        transform: translateY(-2px);
    }
    .metric-card {
        background-color: #1f2937;
        padding: 1.2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #374151;
        text-align: center;
    }
    /* Style Box Pengumuman Biru */
    .announcement-box {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 12px 20px;
        border-radius: 6px;
        border-left: 5px solid #0284c7;
        font-weight: 500;
        margin-bottom: 15px;
    }
    /* Style Box Pengumuman Hijau (Sukses/Yudisium) */
    .success-box {
        background-color: #dcfce7;
        color: #15803d;
        padding: 12px 20px;
        border-radius: 6px;
        border-left: 5px solid #16a34a;
        font-weight: bold;
        margin-bottom: 15px;
    }
    /* Style Box Info Kuning (Jadwal Sarasehan / Petunjuk KP) */
    .warning-box {
        background-color: #fef9c3;
        color: #854d0e;
        padding: 15px 20px;
        border-radius: 6px;
        border-left: 5px solid #ca8a04;
        margin-bottom: 15px;
        line-height: 1.6;
    }
    .form-header {
        background-color: #1f2937;
        padding: 10px 15px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-weight: bold;
        color: white;
        border-bottom: 2px solid #374151;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-req {
        color: #ef4444;
        font-weight: bold;
    }
    /* Tombol Custom Submit */
    .btn-custom-submit button {
        background: #00838f !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 4px !important;
        padding: 0.5rem 1.5rem !important;
    }
    .btn-custom-submit button:hover {
        background: #006064 !important;
    }
    /* Tombol Hijau Khas Form KP */
    .btn-kp-green button {
        background: #2e7d32 !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 4px !important;
        padding: 0.6rem 1.8rem !important;
        font-size: 0.95rem !important;
    }
    .btn-kp-green button:hover {
        background: #1b5e20 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


class MataKuliah(BaseModel):
    kode: str = Field(description="Kode mata kuliah, '-' jika tidak ada")
    nama_mk: str = Field(description="Nama mata kuliah")
    sks: str = Field(description="Jumlah SKS")
    nilai: str = Field(description="Nilai huruf atau angka")


class ProfilMahasiswa(BaseModel):
    nama: str = Field(description="Nama lengkap mahasiswa, '-' jika tidak terdeteksi")
    nim: str = Field(description="NIM / Nomor Induk Mahasiswa, '-' jika tidak terdeteksi")
    jurusan: str = Field(description="Program Studi / Jurusan, '-' jika tidak terdeteksi")
    universitas: str = Field(description="Nama Perguruan Tinggi / Universitas")
    ipk: str = Field(description="IPK Kumulatif")


class TranskripNilai(BaseModel):
    mahasiswa: ProfilMahasiswa
    mata_kuliah: list[MataKuliah]



if "active_view" not in st.session_state:
    st.session_state["active_view"] = "HOME"
if "sarasehan_registered" not in st.session_state:
    st.session_state["sarasehan_registered"] = False



with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/graduation-cap.png", width=100)
    st.title("⚙️ Pengaturan AI")
    st.markdown("---")

    api_key = st.text_input(
        "🔑 Google API Key:",
        type="password",
        help="Masukkan API Key dari Google AI Studio",
    )

    st.markdown("---")
    st.markdown("### 📌 Petunjuk Penggunaan")
    st.markdown("""
    1. Masukkan **API Key** Anda.
    2. Unggah transkrip nilai (**PDF**, **PNG**, **JPG**, **JPEG**).
    3. Klik tombol **Analisis Transkrip**.
    4. Unduh hasil ekstraksi ke **CSV**.
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
        "Aplikasi pintar berbasis AI untuk mengekstrak data mahasiswa dan daftar mata kuliah dari dokumen transkrip nilai secara otomatis dan akurat."
    )
    st.markdown("---")

    if not api_key:
        st.info(
            "👋 **Selamat datang!** Silakan masukkan **Google API Key** Anda di panel sebelah kiri untuk memulai aplikasi."
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### ⚡ Ekstraksi Kilat")
            st.write("Membaca dokumen transkrip dalam hitungan detik menggunakan model terbaru.")
        with col2:
            st.markdown("#### 📊 Rapi & Terstruktur")
            st.write("Data langsung diubah menjadi tabel interaktif siap analisis.")
        with col3:
            st.markdown("#### 📥 Ekspor Mudah")
            st.write("Unduh data transkrip langsung ke format CSV atau spreadsheet.")

    else:
        client = genai.Client(api_key=api_key)

        uploaded_file = st.file_uploader(
            "📂 Unggah File Transkrip Nilai (PDF / Gambar)",
            type=["pdf", "png", "jpg", "jpeg"],
        )

        if uploaded_file is not None:
            file_extension = uploaded_file.name.split(".")[-1].lower()

            col_preview, col_result = st.columns([1, 1.2], gap="large")

            with col_preview:
                st.markdown("### 📄 Preview Dokumen")
                if file_extension in ["png", "jpg", "jpeg"]:
                    image = Image.open(uploaded_file)
                    st.image(image, caption=f"File: {uploaded_file.name}", use_container_width=True)
                else:
                    st.success(f"📄 File PDF Berhasil Diunggah: **{uploaded_file.name}**")
                    st.info("Dokumen PDF siap diproses oleh model AI.")

            with col_result:
                st.markdown("### ⚙️ Kontrol & Hasil Analisis")

                process_btn = st.button("🔍 Mulai Analisis Transkrip Sekarang")

                if process_btn:
                    with st.spinner("🤖 AI sedang membaca dan mengekstrak data transkrip... Mohon tunggu sebentar."):
                        try:
                            prompt = """
                            Analisis dokumen transkrip nilai ini (baik berupa PDF digital maupun hasil scan/foto) dengan sangat teliti.
                            Lakukan OCR dengan cermat jika teks berada pada dokumen scan.
                            Ekstrak informasi profil mahasiswa dan seluruh daftar mata kuliah yang ada.
                            """

                            config = types.GenerateContentConfig(
                                response_mime_type="application/json",
                                response_schema=TranskripNilai,
                                temperature=0.1,
                            )

                            if file_extension in ["png", "jpg", "jpeg"]:
                                image = Image.open(uploaded_file)
                                response = client.models.generate_content(
                                    model="gemini-3.8-flash",
                                    contents=[image, prompt],
                                    config=config,
                                )
                            else:
                                pdf_bytes = uploaded_file.read()
                                response = client.models.generate_content(
                                    model="gemini-3.8-flash",
                                    contents=[
                                        types.Part.from_bytes(
                                            data=pdf_bytes,
                                            mime_type="application/pdf",
                                        ),
                                        prompt,
                                    ],
                                    config=config,
                                )

                            parsed_json = json.loads(response.text)

                            st.session_state["parsed_data"] = parsed_json
                            st.session_state["success_processed"] = True

                        except Exception as e:
                            st.error(f"❌ Terjadi kesalahan saat memproses dokumen: {e}")

                if "success_processed" in st.session_state and st.session_state["success_processed"]:
                    data = st.session_state["parsed_data"]
                    mhs = data.get("mahasiswa", {})
                    mk_list = data.get("mata_kuliah", [])

                    st.markdown("---")
                    st.success("✨ Ekstraksi Data Berhasil Dilakukan!")

                    st.markdown("#### 👤 Profil Mahasiswa")
                    info_col1, info_col2 = st.columns(2)
                    with info_col1:
                        st.write(f"**Nama:** {mhs.get('nama', '-')}")
                        st.write(f"**NIM:** {mhs.get('nim', '-')}")
                        st.write(f"**Jurusan:** {mhs.get('jurusan', '-')}")
                    with info_col2:
                        st.write(f"**Universitas:** {mhs.get('universitas', '-')}")
                        st.metric(label="**IPK Kumulatif**", value=str(mhs.get("ipk", "-")))

                    st.markdown("#### 📚 Daftar Mata Kuliah")
                    df = pd.DataFrame(mk_list)

                    if not df.empty:
                        df.columns = ["Kode MK", "Nama Mata Kuliah", "SKS", "Nilai"]
                        st.dataframe(df, use_container_width=True, hide_index=True)

                        csv_data = df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label="📥 Unduh Data Mata Kuliah (.CSV)",
                            data=csv_data,
                            file_name="transkrip_extracted.csv",
                            mime="text/csv",
                        )
                    else:
                        st.warning("⚠️ Tidak ada daftar mata kuliah yang terdeteksi.")



elif st.session_state["active_view"] == "TTU":
    
    tab1, tab2, tab3 = st.tabs(["📋 Daftar TTU", "🔍 Daftar Review", "🎓 Daftar Yudisium"])

   
    with tab1:
        st.markdown("### SEMESTER GANJIL 2026-2027")
        st.markdown("## PENDAFTARAN TUGAS TALENTA UNGGUL")
        
        st.markdown(
            """
            <div class="announcement-box">
                ℹ️ Pendaftaran Tugas Talenta Unggul Dibuka Sampai Minggu, 10 September 2026
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown('<div class="form-header">FORM PENDAFTARAN TUGAS TALENTA UNGGUL SEMESTER GANJIL 2026-2027</div>', unsafe_allow_html=True)
        
        with st.container():
            st.write("") 
            
            
            col_nim, col_nama = st.columns(2)
            with col_nim:
                nim = st.text_input("NIM", value="672014011")
            with col_nama:
                nama = st.text_input("Nama", value="RAYNALDO")

            
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
                doc_ttu = st.file_uploader("Upload Dokumen", type=["pdf", "doc", "docx"], label_visibility="collapsed", key="doc_ttu")
            
            with col_transkrip:
                st.markdown("🖼️ **Scan Transkrip Nilai** <span class='badge-req'>⚠️ Max 5MB</span>", unsafe_allow_html=True)
                transkrip_file = st.file_uploader("Upload Transkrip", type=["pdf", "png", "jpg", "jpeg"], label_visibility="collapsed", key="transkrip_ttu")

            st.markdown("---")

           
            col_btn, _ = st.columns([1, 3])
            with col_btn:
                btn_daftar = st.button("DAFTAR", key="btn_submit_ttu")

            if btn_daftar:
                if not judul_ttu or judul_ttu == "-":
                    st.warning("⚠️ Mohon isi Judul Tugas Talenta Unggul terlebih dahulu!")
                else:
                    st.success("✅ Pendaftaran Tugas Talenta Unggul Berhasil Dikirim!")

    
    with tab2:
        st.markdown("### SEMESTER GANJIL 2026-2027")
        st.markdown("## PENDAFTARAN REVIEW")

        st.markdown(
            """
            <div class="announcement-box">
                ℹ️ Pendaftaran Review Dibuka Sampai Minggu, 3 Desember 2026
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown('<div class="form-header">FORM PENDAFTARAN REVIEW</div>', unsafe_allow_html=True)

        with st.container():
            st.write("")

            
            col_r_nim, col_r_nama = st.columns(2)
            with col_r_nim:
                r_nim = st.text_input("NIM", value="672014011", key="r_nim")
            with col_r_nama:
                r_nama = st.text_input("Nama", value="RAYNALDO", key="r_nama")

           
            col_r_prodi, col_r_peminatan = st.columns(2)
            with col_r_prodi:
                r_prodi = st.text_input("Program Studi", value="S1 TEKNIK INFORMATIKA", key="r_prodi")
            with col_r_peminatan:
                r_peminatan = st.text_input("Peminatan", value="web, webservice, php", key="r_peminatan")

            
            st.markdown("**Judul Tugas Akhir**", unsafe_allow_html=True)
            r_judul = st.text_input(
                "Judul Tugas Akhir",
                value="Perancangan Website Sistem Informasi Tugas Akhir Dengan Teknologi SOAP Web Services",
                label_visibility="collapsed",
                key="r_judul"
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

            # Baris 6: Upload Dokumen Akhir & Scan Transkrip Nilai
            col_r_doc, col_r_transkrip = st.columns(2)
            with col_r_doc:
                st.markdown("📄 **Dokumen Akhir (PDF/Ms.Word)** <span class='badge-req'>⚠️ *Ukuran file max 15MB</span>", unsafe_allow_html=True)
                r_doc_file = st.file_uploader("Upload Dokumen Akhir", type=["pdf", "doc", "docx"], label_visibility="collapsed", key="r_doc_file")

            with col_r_transkrip:
                st.markdown("🖼️ **Scan Transkrip Nilai** <span class='badge-req'>⚠️ *Ukuran file max 5MB</span>", unsafe_allow_html=True)
                r_transkrip_file = st.file_uploader("Upload Scan Transkrip", type=["pdf", "png", "jpg", "jpeg"], label_visibility="collapsed", key="r_transkrip_file")

            st.markdown("---")

            
            col_r_btn, _ = st.columns([1.5, 3])
            with col_r_btn:
                st.markdown('<div class="btn-custom-submit">', unsafe_allow_html=True)
                btn_daftar_review = st.button("DAFTAR REVIEW", key="btn_submit_review")
                st.markdown('</div>', unsafe_allow_html=True)

            if btn_daftar_review:
                st.success("✅ Pendaftaran Review Berhasil Dikirim!")

 
    with tab3:
        st.markdown("### SEMESTER GANJIL 2026-2027")
        st.markdown("## PENDAFTARAN YUDISIUM")

        st.markdown('<div class="form-header">DAFTAR YUDISIUM</div>', unsafe_allow_html=True)

        with st.container():
            st.write("")

            st.markdown(
                """
                <div class="success-box">
                    Yudisium Akan Dilakukan Pada Jumat, 14 Desember 2026
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                """
                <div class="announcement-box">
                    ℹ️ Pendaftaran Yudisium Dibuka Sampai Rabu, 12 Desember 2026
                </div>
                """,
                unsafe_allow_html=True
            )

            st.write("")

            col_y_btn, _ = st.columns([1.8, 3])
            with col_y_btn:
                st.markdown('<div class="btn-custom-submit">', unsafe_allow_html=True)
                btn_daftar_yudisium = st.button("DAFTAR YUDISIUM", key="btn_submit_yudisium")
                st.markdown('</div>', unsafe_allow_html=True)

            if btn_daftar_yudisium:
                st.success("✅ Pendaftaran Yudisium Berhasil Dikirim!")



elif st.session_state["active_view"] == "KP":
    
    tab_kp1, tab_kp2, tab_kp3, tab_kp4, tab_kp5 = st.tabs([
        "👥 1. Daftar Sarasehan",
        "🏢 2. List Tempat KP",
        "📢 3. Pengumuman",
        "📄 4. Surat Permohonan",
        "📋 5. Daftar KP"
    ])
    
   
    with tab_kp1:
        st.markdown("### SEMESTER GANJIL 2026-2027")
        st.markdown("## DAFTAR SARASEHAN")

        st.markdown('<div class="form-header">Daftar Sarasehan</div>', unsafe_allow_html=True)

        with st.container():
            st.write("")

            if not st.session_state["sarasehan_registered"]:
                st.markdown(
                    """
                    <div class="announcement-box">
                        Pendaftaran Sarasehan Akan Ditutup Pada <b>SENIN, 15 OKTOBER 2026</b>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.write("")

                col_s_btn, _ = st.columns([2, 3])
                with col_s_btn:
                    st.markdown('<div class="btn-sarasehan">', unsafe_allow_html=True)
                    btn_daftar_sarasehan = st.button("DAFTAR SARASEHAN!", key="btn_submit_sarasehan")
                    st.markdown('</div>', unsafe_allow_html=True)

                if btn_daftar_sarasehan:
                    st.session_state["sarasehan_registered"] = True
                    st.rerun()

            else:
                st.markdown(
                    """
                    <div class="success-box">
                        Sukses daftar Sarasehan!
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.markdown(
                    """
                    <div class="warning-box">
                        Sarasehan akan diadakan pada :<br>
                        <b>Hari/Tanggal : Senin, 19 Oktober 2026</b><br>
                        <b>Waktu : 13:00-selesai</b><br>
                        <b>Tempat : AUDITORIUM</b>
                    </div>
                    """,
                    unsafe_allow_html=True
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
            {"No": 3, "Nama Perusahaan": "Alfacart (Tangerang)", "Kota": "Tangerang", "Kuota": "5 Mahasiswa", "Status": "Tersedia"}
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
            unsafe_allow_html=True
        )

    
    with tab_kp4:
        st.subheader("📄 Pengajuan Surat Permohonan KP")
        with st.form("form_surat_kp"):
            st.text_input("Nama Instansi / Perusahaan Tujuan", placeholder="Masukkan nama perusahaan...")
            st.text_area("Alamat Lengkap Perusahaan", placeholder="Masukkan alamat lengkap...")
            st.text_input("Ditujukan Kepada (Jabatan/HRD)", placeholder="Contoh: HRD Manager / Kepala Divisi IT")
            submitted_surat = st.form_submit_button("Kirim Pengajuan Surat")
            if submitted_surat:
                st.success("✅ Pengajuan Surat Permohonan KP Berhasil Dikirim!")

    
    with tab_kp5:
        
        st.markdown(
            """
            <div class="announcement-box">
                Pendaftaran Kerja Praktek Akan Ditutup Pada <b>KAMIS, 20 DESEMBER 2026</b>
            </div>
            """,
            unsafe_allow_html=True
        )

       
        st.markdown(
            """
            <div class="warning-box">
                <b>Baca Sebelum Melanjutkan!</b><br><br>
                1. Pastikan anda sudah menyiapkan seluruh berkas yang dibutuhkan.<br>
                &nbsp;&nbsp;&nbsp;&nbsp;• KST Terbaru yang ada matakuliah KPnya.<br>
                &nbsp;&nbsp;&nbsp;&nbsp;• Transkrip Terbaru yang sudah di TTD oleh Kaprogdi.<br>
                &nbsp;&nbsp;&nbsp;&nbsp;• Surat diterima untuk melaksanakan Kerja Praktek di Perusahaan / Instansi.<br>
                2. Pilih Perusahaan yang tersedia di list, jika tidak ada silahkan menemui kaprogdi.<br>
                3. Pastikan kembali data yang anda pilih / isi sudah benar dan final, karena tidak ada perubahan data setelah anda mengklik "Daftar KP".<br>
                4. Setelah mengklik "Daftar KP" dan sukses untuk mendaftar, silahkan kumpulkan berkas diatas ke Kantor KP pada jam kerja.
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("")

        
        col_kp_left, col_kp_right = st.columns([1, 3])

        with col_kp_left:
            st.markdown("**NIM**", unsafe_allow_html=True)
            st.write("")
            st.markdown("**Nama**", unsafe_allow_html=True)
            st.write("")
            st.markdown("**Makul KP**", unsafe_allow_html=True)
            st.write("")
            st.markdown("**List Tempat KP**", unsafe_allow_html=True)
            st.write("")
            st.markdown("**Berkas-Berkas**", unsafe_allow_html=True)

        with col_kp_right:
            kp_nim = st.text_input("NIM KP", value="672015002", label_visibility="collapsed", key="kp_nim")
            kp_nama = st.text_input("Nama KP", value="ANDHIKA PUTRA UTOMO", label_visibility="collapsed", key="kp_nama")
            
            
            col_mk1, col_mk2 = st.columns(2)
            with col_mk1:
                kp_mk1 = st.checkbox("KERJA PRAKTEK 1", key="kp_mk1")
            with col_mk2:
                kp_mk2 = st.checkbox("KERJA PRAKTEK 2", value=True, key="kp_mk2")

           
            list_perusahaan = [
                "Alfacart (Tangerang)",
                "PT Solusi Teknologi Indonesia (Semarang)",
                "Dinas Komunikasi dan Informatika (Salatiga)",
                "PT LeadGeeks Indonesia (Salatiga)"
            ]
            kp_tempat = st.selectbox("Tempat KP", list_perusahaan, label_visibility="collapsed", key="kp_tempat")

            
            st.markdown(
                "<span style='color: #ef4444; font-weight: bold;'>Semua scan berkas pendaftaran KP hanya berupa gambar (jpg/png) atau pdf dengan ukuran file max 5MB.</span>",
                unsafe_allow_html=True
            )

           
            st.markdown("🖼️ **Scan Transkrip Nilai**", unsafe_allow_html=True)
            kp_transkrip_file = st.file_uploader("Scan Transkrip Nilai", type=["pdf", "png", "jpg", "jpeg"], label_visibility="collapsed", key="kp_transkrip_file")

            
            st.markdown("🖼️ **Scan Surat Diterima Perusahaan**", unsafe_allow_html=True)
            kp_surat_file = st.file_uploader("Scan Surat Diterima Perusahaan", type=["pdf", "png", "jpg", "jpeg"], label_visibility="collapsed", key="kp_surat_file")

        st.markdown("---")

        
        col_kp_btn, _ = st.columns([1.5, 3])
        with col_kp_btn:
            st.markdown('<div class="btn-kp-green">', unsafe_allow_html=True)
            btn_submit_kp = st.button("Daftar KP", key="btn_submit_kp")
            st.markdown('</div>', unsafe_allow_html=True)

        if btn_submit_kp:
            st.success("✅ Pendaftaran Kerja Praktek Berhasil Dikirim!")
