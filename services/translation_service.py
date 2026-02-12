from __future__ import annotations

from config import load_config
from services.http_client import HttpClient


class TranslationService:
    def __init__(self, http: HttpClient | None = None, timeout: int = 60) -> None:
        self.http = http or HttpClient(timeout=timeout)
        self.cfg = load_config()

    def is_configured(self) -> bool:
        return bool(self.cfg.translate_api_url)

    async def translate(self, text: str, target_lang: str, source_lang: str | None = None) -> str:
        if not text:
            return text
        if not self.cfg.translate_api_url:
            return text
        try:
            return await self._translate_request(text, target_lang, source_lang)
        except Exception:
            return text

    async def _translate_request(self, text: str, target_lang: str, source_lang: str | None = None) -> str:
        payload = {
            'q': text,
            'target': target_lang,
            'format': 'text',
        }
        if source_lang:
            payload['source'] = source_lang
        else:
            payload['source'] = 'auto'
        if self.cfg.translate_api_key:
            payload['api_key'] = self.cfg.translate_api_key
        data = await self.http.post_json(self.cfg.translate_api_url.rstrip('/') + '/translate', payload)
        return data.get('translatedText') or text

    async def translate_texts(self, texts: list[str], target_lang: str, source_lang: str | None = None) -> list[str]:
        results: list[str] = []
        for text in texts:
            results.append(await self.translate(text, target_lang, source_lang))
        return results

    async def try_translate_texts(self, texts: list[str], target_lang: str, source_lang: str | None = None) -> tuple[list[str], bool]:
        results: list[str] = []
        try:
            for text in texts:
                results.append(await self._translate_request(text, target_lang, source_lang))
            return results, True
        except Exception:
            return texts, False

    async def is_available(self, target_lang: str | None = None) -> bool:
        if not self.cfg.translate_api_url:
            return False
        try:
            data = await self.http.get_json(self.cfg.translate_api_url.rstrip('/') + '/languages')
            if not target_lang:
                return True
            langs = {str(item.get('code')) for item in data if isinstance(item, dict)}
            return target_lang in langs
        except Exception:
            return False
