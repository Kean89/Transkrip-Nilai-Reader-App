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
    page_icon="logo_transkrip.ico",  
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


with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/graduation-cap.png", width=100)
    st.title("⚙️ Pengaturan AI")
    st.markdown("---")

    api_key = st.text_input(
        "🔑 Google Gemini API Key:",
        type="password",
        help="Masukkan API Key dari Google AI Studio",
    )

    st.markdown("---")
    st.markdown("### 📌 Petunjuk Penggunaan")
    st.markdown("""
    1. Masukkan **API Key** Gemini Anda.
    2. Unggah transkrip nilai (**PDF**, **PNG**, **JPG**, **JPEG**).
    3. Klik tombol **Analisis Transkrip**.
    4. Unduh hasil ekstraksi ke **CSV**.
    """)
    st.markdown("---")
    st.caption("Dibuat dengan ❤️ menggunakan Streamlit")


st.title("Transkrip Nilai Reader")
st.markdown(
    "Aplikasi pintar berbasis AI untuk mengekstrak data mahasiswa dan daftar mata kuliah dari dokumen transkrip nilai secara otomatis dan akurat."
)
st.markdown("---")

if not api_key:
    st.info(
        "👋 **Selamat datang!** Silakan masukkan **Google Gemini API Key** Anda di panel sebelah kiri untuk memulai aplikasi."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### ⚡ Ekstraksi Kilat")
        st.write("Membaca dokumen transkrip dalam hitungan detik menggunakan model Gemini terbaru.")
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
                st.image(image, caption=f"File: {uploaded_file.name}", use_column_width=True)
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
