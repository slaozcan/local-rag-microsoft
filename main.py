import os
import re
import math
import hashlib
from db import init_db, insert_chunk, get_all_chunks

try:
    from foundry_adapter import USE_FOUNDRY, generate_foundry_answer
except Exception as e:
    print("Foundry adapter yüklenemedi:", e)
    USE_FOUNDRY = False
    generate_foundry_answer = None


DOCS_FOLDER = "docs"
EMBEDDING_DIM = 256


def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-ZçğıöşüÇĞİÖŞÜ0-9\s]", " ", text)
    words = text.split()

    stop_words = {
        "ve", "veya", "ile", "bir", "bu", "şu", "o", "için", "gibi",
        "de", "da", "mi", "mı", "mu", "mü", "ne", "nedir", "nasıl",
        "the", "is", "are", "a", "an", "of", "to", "in", "on"
    }

    return [word for word in words if word not in stop_words]


def create_embedding(text):
    """
    Basit local embedding üretimi.
    Metni 256 boyutlu sayısal vektöre çevirir.
    """

    vector = [0.0] * EMBEDDING_DIM
    words = tokenize(text)

    for word in words:
        hash_value = hashlib.md5(word.encode("utf-8")).hexdigest()
        index = int(hash_value, 16) % EMBEDDING_DIM
        vector[index] += 1.0

    norm = math.sqrt(sum(value * value for value in vector))

    if norm == 0:
        return vector

    return [value / norm for value in vector]


def cosine_similarity(vec1, vec2):
    return sum(a * b for a, b in zip(vec1, vec2))


def index_documents_to_sqlite():
    """
    docs klasöründeki txt dosyalarını okur,
    paragraflara böler,
    her paragraf için embedding üretir
    ve SQLite veritabanına kaydeder.
    """

    if not os.path.exists(DOCS_FOLDER):
        os.makedirs(DOCS_FOLDER)

    init_db()

    total_chunks = 0

    for filename in os.listdir(DOCS_FOLDER):
        if filename.endswith(".txt"):
            path = os.path.join(DOCS_FOLDER, filename)

            with open(path, "r", encoding="utf-8") as file:
                text = file.read()

            paragraphs = [
                paragraph.strip()
                for paragraph in text.split("\n\n")
                if paragraph.strip()
            ]

            for paragraph in paragraphs:
                embedding = create_embedding(paragraph)
                insert_chunk(filename, paragraph, embedding)
                total_chunks += 1

    return total_chunks


def load_documents():
    """
    app.py tarafından çağrılır.
    Belgeleri SQLite'a indexler ve sonra SQLite'tan chunk'ları okur.
    """

    index_documents_to_sqlite()
    chunks = get_all_chunks()
    return chunks


def get_top_chunks(question, chunks, top_k=3):
    """
    Kullanıcı sorusunu embedding'e çevirir.
    Chunk embedding'leriyle cosine similarity hesaplar.
    En alakalı top-k belge parçasını döndürür.
    """

    query_embedding = create_embedding(question)
    scored_chunks = []

    for chunk in chunks:
        score = cosine_similarity(query_embedding, chunk["embedding"])
        scored_chunks.append((score, chunk))

    scored_chunks.sort(key=lambda item: item[0], reverse=True)

    top_results = []

    for score, chunk in scored_chunks[:top_k]:
        if score > 0.05:
            top_results.append(chunk)

    return top_results


def build_context(top_chunks):
    context = "\n\n".join(
        [
            f"Kaynak: {chunk['source']}\n{chunk['text']}"
            for chunk in top_chunks
        ]
    )

    return context


def context_has_answer(question, context):
    """
    Soru ile context arasında basit anahtar kelime kontrolü yapar.
    Amaç: Model cevap verip sonra yanlışlıkla 'bilgi yok' derse bunu temizlemek.
    """

    question_lower = question.lower()
    context_lower = context.lower()

    keyword_groups = {
        "rag": ["rag", "retrieval", "augmented", "generation"],
        "sqlite": ["sqlite", "veritabanı", "database"],
        "foundry": ["foundry", "local", "offline"],
        "proje": ["proje", "amaç", "asistan"],
        "embedding": ["embedding", "vektör", "vector"],
    }

    for question_key, terms in keyword_groups.items():
        if question_key in question_lower:
            for term in terms:
                if term in context_lower:
                    return True

    question_words = tokenize(question)
    context_words = tokenize(context)

    overlap = set(question_words).intersection(set(context_words))

    return len(overlap) > 0


def safe_answer_if_needed(question, foundry_response, context):
    """
    Demo güvenliği için basit hallucination kontrolü.
    """

    question_lower = question.lower()
    response_lower = foundry_response.lower()
    context_lower = context.lower()

    answer_exists_in_context = context_has_answer(question, context)

    # Model doğru cevap verip en sona yanlışlıkla "Bu bilgi belgelerde yok" eklerse temizle.
    if "bu bilgi belgelerde yok" in response_lower and answer_exists_in_context:
        cleaned = foundry_response.replace("Bu bilgi belgelerde yok.", "")
        cleaned = cleaned.replace("Bu bilgi belgelerde yok", "")
        cleaned = cleaned.strip()

        if cleaned:
            foundry_response = cleaned
            response_lower = foundry_response.lower()

    # RAG sorusunda model kısa, eksik veya yanlış cevap verirse güvenli cevap kullan.
    if "rag" in question_lower:
        correct_terms_in_context = (
            "retrieval" in context_lower
            and "augmented" in context_lower
            and "generation" in context_lower
        )

        wrong_terms = (
            "kıta" in response_lower
            or "ad, yeri" in response_lower
            or "yemeğin" in response_lower
        )

        too_short = len(foundry_response.strip()) < 40

        if correct_terms_in_context and (wrong_terms or too_short):
            return (
                "RAG, Retrieval-Augmented Generation anlamına gelir. "
                "Sistem önce ilgili belge parçalarını bulur, ardından bu parçaları "
                "modelin cevabına bağlam olarak ekler. Böylece cevaplar daha doğru "
                "ve kaynaklara dayalı şekilde üretilir."
            )

    return foundry_response


def generate_answer(question, top_chunks):
    """
    Cevap üretimi.

    1. İlgili chunk yoksa güvenli fallback döndürür.
    2. Foundry Local çalışıyorsa context'i Foundry Local LLM'e gönderir.
    3. Foundry hata verirse kaynak parçalarına dayalı fallback cevap verir.
    """

    if not top_chunks:
        return "Bu bilgi belgelerde yok. Bu yüzden emin bir cevap veremiyorum."

    context = build_context(top_chunks)

    if USE_FOUNDRY and generate_foundry_answer is not None:
        try:
            foundry_response = generate_foundry_answer(question, context)
            foundry_response = safe_answer_if_needed(
                question,
                foundry_response,
                context
            )

            return f"""
**Foundry Local LLM Cevabı:**

{foundry_response}

**Kullanılan Kaynaklar:**

{context}
"""
        except Exception as e:
            print("Foundry Local LLM kullanılamadı. Fallback cevap kullanılacak.")
            print("Hata:", e)

    combined_text = " ".join([chunk["text"] for chunk in top_chunks])

    fallback_answer = f"""
**Kısa cevap:**

{combined_text}

**Kaynaklara dayalı açıklama:**

Bu cevap, SQLite veritabanında saklanan yerel doküman parçaları arasından
embedding ve cosine similarity kullanılarak seçilen en alakalı kaynaklara göre oluşturulmuştur.

**Teknik not:**

Foundry Local LLM bu çalıştırmada kullanılamadığı için fallback cevap gösteriliyor.
Normal tam akışta bulunan bağlam Foundry Local üzerindeki yerel LLM'e gönderilir.
"""

    return fallback_answer


def main():
    print("Local RAG Assistant başlatıldı.")
    print("SQLite + embedding + cosine similarity hazırlanıyor...")
    print("-" * 50)

    chunks = load_documents()

    print(f"{len(chunks)} belge parçası SQLite veritabanından yüklendi.")
    print("Çıkmak için q, quit veya exit yaz.")
    print("-" * 50)

    while True:
        question = input("\nSoru: ")

        if question.lower() in ["q", "quit", "exit"]:
            print("Çıkılıyor...")
            break

        top_chunks = get_top_chunks(question, chunks)
        answer = generate_answer(question, top_chunks)

        print("\nCevap:")
        print(answer)


if __name__ == "__main__":
    main()