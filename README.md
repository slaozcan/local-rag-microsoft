# Local RAG Assistant MVP

Bu proje, Microsoft Foundry Local ile çalışan bir Local RAG Assistant MVP uygulamasıdır.

## Amaç

Amaç, küçük bir yerel doküman koleksiyonundan soru-cevap yapabilen bir asistan geliştirmektir.

Sistem şu akışla çalışır:

1. `docs/` klasöründeki metin dosyalarını okur.
2. Belgeleri paragraf bazlı chunk'lara böler.
3. Her chunk için embedding vektörü üretir.
4. Chunk metni ve embedding bilgisini SQLite veritabanında saklar.
5. Kullanıcı soru sorduğunda soruyu embedding'e çevirir.
6. Cosine similarity ile en alakalı belge parçalarını bulur.
7. Bulunan bağlamı Foundry Local LLM'e gönderir.
8. Cevap yerel/offline modelden üretilir.

## Kullanılan Teknolojiler

- Python
- Streamlit
- SQLite
- Foundry Local
- Cosine Similarity
- Local RAG Pipeline

## Çalıştırma

Sanal ortamı aktif et:

```powershell
.\.venv\Scripts\Activate.ps1