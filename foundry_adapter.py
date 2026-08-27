import subprocess

USE_FOUNDRY = True

CHAT_MODEL_ALIAS = "phi-4-mini"


def generate_foundry_answer(question, context):
    """
    Foundry Local CLI üzerinden yerel LLM cevabı üretir.
    Arka planda şu komutu çalıştırır:

    foundry complete phi-4-mini PROMPT
    """

    prompt = f"""
Sen yerel belgelerle çalışan bir Local RAG asistanısın.

Kurallar:
- Sadece BAĞLAM bölümündeki bilgileri kullan.
- Bağlamda cevap varsa kesinlikle "Bu bilgi belgelerde yok." deme.
- Bağlamda cevap gerçekten yoksa sadece "Bu bilgi belgelerde yok." yaz.
- Cevabı Türkçe ver.
- Cevap 2-4 cümle olsun.
- Gereksiz tekrar yapma.
- Kaynak metindeki bilgiyi sadeleştirerek açıkla.

BAĞLAM:
{context}

SORU:
{question}

Cevap:
"""

    result = subprocess.run(
        [
            "foundry",
            "complete",
            CHAT_MODEL_ALIAS,
            prompt
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=240
    )

    if result.returncode != 0:
        error_message = result.stderr.strip()

        if not error_message:
            error_message = result.stdout.strip()

        raise RuntimeError(error_message)

    answer = result.stdout.strip()

    if not answer:
        raise RuntimeError("Foundry boş cevap döndürdü.")

    return answer