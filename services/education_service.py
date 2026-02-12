from __future__ import annotations


LESSONS = {
    'en': [
        'Risk vs Reward: balancing upside and downside',
        'Diversification: why it matters',
        'What is market cap?',
        'Understanding liquidity',
        'MACD and RSI basics',
        'Portfolio rebalancing strategies',
        'On-chain metrics 101',
        'Options: calls vs puts',
        'ETF vs Mutual Fund: key differences',
        'Inflation: how it affects returns',
        'Dollar-cost averaging (DCA)',
        'Stop-loss and take-profit basics',
        'P/E and valuation intuition',
        'Yield curve: what it can signal',
        'Earnings reports: what to watch',
    ],
    'ru': [
        'Риск и доходность: баланс между прибылью и просадками',
        'Диверсификация: зачем она нужна',
        'Что такое капитализация',
        'Ликвидность: как быстро продать актив',
        'MACD и RSI: базовые сигналы',
        'Ребалансировка портфеля: когда и зачем',
        'Ончейн‑метрики: что они показывают',
        'Опционы: коллы и путы простыми словами',
        'ETF и ПИФ: чем отличаются',
        'Инфляция и реальная доходность',
        'DCA: усреднение стоимости',
        'Стоп‑лосс и тейк‑профит',
        'P/E и оценка компании',
        'Кривая доходности: какие сигналы даёт',
        'Отчётность: на что смотреть инвестору',
    ],
}


GLOSSARY = {
    'en': [
        'Alpha — excess return over benchmark',
        'Beta — volatility vs market',
        'Liquidity — ease of buying/selling',
        'Spread — bid/ask difference',
    ],
    'ru': [
        'Alpha — доходность сверх бенчмарка',
        'Beta — волатильность относительно рынка',
        'Ликвидность — насколько легко купить/продать',
        'Спред — разница между bid/ask',
    ],
}


class EducationService:
    async def get_lessons(self, language: str = 'en') -> list[str]:
        lang = 'ru' if (language or '').lower().startswith('ru') else 'en'
        return LESSONS.get(lang, LESSONS['en'])

    async def get_glossary(self, language: str = 'en') -> list[str]:
        lang = 'ru' if (language or '').lower().startswith('ru') else 'en'
        return GLOSSARY.get(lang, GLOSSARY['en'])

    async def get_quiz(self) -> str:
        return 'Q: What is diversification?\nA) Buying one asset\nB) Spreading across assets'
