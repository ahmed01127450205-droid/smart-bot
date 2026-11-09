from google import genai
from google.genai import types


SYSTEM_INSTRUCTION = (
    "أنت مساعد تعليمي ذكي وودود. أجب باللغة العربية ما لم يطلب المستخدم لغة أخرى. "
    "اشرح الحلول بوضوح وخطوات مرتبة، ولا تخترع معلومات غير مؤكدة. "
    "إذا أرسل المستخدم صورة أو مستندًا، اقرأ محتواه بعناية وأجب عن طلبه."
)


class GeminiService:
    def __init__(self, api_key: str, model_name: str) -> None:
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def answer(
        self,
        user_text: str,
        history: list[dict[str, str]],
        attachment: bytes | None = None,
        mime_type: str | None = None,
        extracted_text: str | None = None,
    ) -> str:
        contents: list[types.Content] = []
        for item in history:
            contents.append(
                types.Content(
                    role=item["role"],
                    parts=[types.Part.from_text(text=item["content"])],
                )
            )

        prompt = user_text.strip() or "حلّل الملف أو الصورة المرفقة واشرح محتواها."
        if extracted_text:
            prompt += f"\n\nمحتوى المستند المرفق:\n{extracted_text}"

        parts: list[types.Part] = [types.Part.from_text(text=prompt)]
        if attachment is not None and mime_type:
            parts.append(types.Part.from_bytes(data=attachment, mime_type=mime_type))
        contents.append(types.Content(role="user", parts=parts))

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.4,
            ),
        )
        answer = response.text
        if not answer:
            raise RuntimeError("The AI service returned an empty response.")
        return answer.strip()
