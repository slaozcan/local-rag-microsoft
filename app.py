import streamlit as st
from main import load_documents, get_top_chunks, generate_answer


st.set_page_config(
    page_title="Local RAG Assistant MVP",
    page_icon="🤖",
    layout="wide"
)


st.title("🤖 Local RAG Assistant MVP")

st.info(
    "Bu sürüm bir MVP'dir: Streamlit arayüzü, SQLite veri katmanı, "
    "embedding üretimi, cosine similarity tabanlı vector search ve "
    "Foundry Local LLM entegrasyonu içerir."
)

st.write(
    "Bu uygulama, yerel dokümanlardan ilgili bilgileri bulup "
    "kullanıcı sorularına kaynak parçalarıyla cevap verir."
)


st.sidebar.title("Proje Bilgisi")

st.sidebar.write("""
Bu demo, bir Local RAG MVP prototipidir.

- Dokümanlar `docs/` klasöründen okunur.
- Metinler paragraflara bölünür.
- Her parça için embedding vektörü üretilir.
- Parçalar ve embedding'ler SQLite veritabanına kaydedilir.
- Kullanıcı sorusu embedding'e çevrilir.
- Cosine similarity ile en alakalı parçalar bulunur.
- Bulunan bağlam Foundry Local LLM'e gönderilir.
- Cevap yerel/offline model üzerinden üretilir.
""")


@st.cache_data
def get_chunks():
    return load_documents()


if st.sidebar.button("Veritabanını Yenile"):
    st.cache_data.clear()
    st.rerun()


chunks = get_chunks()

st.sidebar.success(f"{len(chunks)} belge parçası yüklendi.")

st.divider()

question = st.text_input(
    "Sorunu yaz:",
    placeholder="Örn: RAG nedir?"
)

col1, col2 = st.columns([1, 4])

with col1:
    ask_clicked = st.button("Cevapla", type="primary")

with col2:
    clear_clicked = st.button("Temizle")


if clear_clicked:
    st.rerun()


if ask_clicked:
    if not question.strip():
        st.warning("Lütfen bir soru yaz.")
    else:
        top_chunks = get_top_chunks(question, chunks)
        answer = generate_answer(question, top_chunks)

        st.subheader("Cevap")
        st.markdown(answer)

        st.subheader("Bulunan Kaynak Parçaları")

        if top_chunks:
            for i, chunk in enumerate(top_chunks, start=1):
                with st.expander(f"{i}. Kaynak: {chunk['source']}"):
                    st.write(chunk["text"])
        else:
            st.info("Bu soru için ilgili kaynak bulunamadı.")


st.divider()

st.caption(
    "Not: Sistem önce SQLite veritabanındaki embedding'ler üzerinden ilgili belge parçalarını bulur. "
    "Foundry Local kullanılabiliyorsa bulunan bağlam yerel LLM'e gönderilerek cevap üretilir; "
    "aksi halde fallback olarak kaynak parçaları gösterilir."
)