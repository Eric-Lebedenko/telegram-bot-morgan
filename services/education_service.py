from __future__ import annotations


LESSONS = {
    'en': [
        {
            'id': 'risk-reward',
            'title': 'Risk vs Reward',
            'pages': [
                'Higher potential returns usually mean higher risk. Look at volatility, drawdowns, and time horizon.',
                'Match risk to your goals: long-term goals can handle more volatility, short-term goals should be safer.',
            ],
            'sources': [
                'Book: The Intelligent Investor — Benjamin Graham',
                'https://www.investopedia.com/terms/r/riskrewardratio.asp',
            ],
        },
        {
            'id': 'diversification',
            'title': 'Diversification',
            'pages': [
                'Spreading across assets reduces the impact of any one loss.',
                'Diversify by asset class, sector, geography, and time.',
            ],
            'sources': [
                'Book: A Random Walk Down Wall Street — Burton Malkiel',
                'https://www.investopedia.com/terms/d/diversification.asp',
            ],
        },
        {
            'id': 'market-cap',
            'title': 'Market Cap Basics',
            'pages': [
                'Market cap = price × shares outstanding. It is a proxy for company size.',
                'Large-cap tends to be more stable, small-cap can grow faster but is riskier.',
            ],
            'sources': [
                'Book: Common Stocks and Uncommon Profits — Philip Fisher',
                'https://www.investopedia.com/terms/m/marketcapitalization.asp',
            ],
        },
        {
            'id': 'liquidity',
            'title': 'Liquidity',
            'pages': [
                'Liquidity means how quickly you can buy/sell at a fair price.',
                'Low liquidity = wider spreads and more slippage.',
            ],
            'sources': [
                'https://www.investopedia.com/terms/l/liquidity.asp',
            ],
        },
        {
            'id': 'valuation',
            'title': 'Valuation (P/E, P/B)',
            'pages': [
                'P/E compares price to earnings. High P/E = high growth expectations or overvaluation.',
                'P/B compares price to book value; useful for banks and asset-heavy firms.',
            ],
            'sources': [
                'Book: Valuation — McKinsey & Company',
                'https://www.investopedia.com/terms/p/price-earningsratio.asp',
            ],
        },
        {
            'id': 'earnings',
            'title': 'Earnings Reports',
            'pages': [
                'Watch revenue growth, margins, guidance, and EPS surprises.',
                'Price moves often depend on expectations vs. actual results.',
            ],
            'sources': [
                'https://www.investopedia.com/terms/e/earnings.asp',
            ],
        },
        {
            'id': 'dca',
            'title': 'Dollar-Cost Averaging',
            'pages': [
                'Invest fixed amounts regularly to reduce timing risk.',
                'Works best in volatile markets and long horizons.',
            ],
            'sources': [
                'https://www.investopedia.com/terms/d/dollarcostaveraging.asp',
            ],
        },
        {
            'id': 'rebalance',
            'title': 'Portfolio Rebalancing',
            'pages': [
                'Rebalancing restores your target allocation after market moves.',
                'It can reduce risk and lock in gains.',
            ],
            'sources': [
                'Book: The Bogleheads\' Guide to Investing',
                'https://www.investopedia.com/terms/r/rebalancing.asp',
            ],
        },
        {
            'id': 'etf',
            'title': 'ETF vs Mutual Fund',
            'pages': [
                'ETFs trade intraday; mutual funds trade once per day.',
                'ETFs are usually cheaper and more tax efficient.',
            ],
            'sources': [
                'https://www.investopedia.com/terms/e/etf.asp',
            ],
        },
        {
            'id': 'inflation',
            'title': 'Inflation & Real Returns',
            'pages': [
                'Real return = nominal return − inflation.',
                'Inflation hurts cash and fixed income, but stocks can keep up long-term.',
            ],
            'sources': [
                'https://www.investopedia.com/terms/i/inflation.asp',
            ],
        },
        {
            'id': 'macd-rsi',
            'title': 'MACD & RSI Basics',
            'pages': [
                'MACD shows trend momentum; RSI shows overbought/oversold.',
                'Use indicators with risk management, not alone.',
            ],
            'sources': [
                'https://www.investopedia.com/terms/m/macd.asp',
                'https://www.investopedia.com/terms/r/rsi.asp',
            ],
        },
    ],
    'ru': [
        {
            'id': 'risk-reward',
            'title': 'Риск и доходность',
            'pages': [
                'Чем выше потенциальная доходность, тем выше риск. Смотрите на волатильность и просадки.',
                'Подбирайте риск под цели: для коротких горизонтов нужна стабильность.',
            ],
            'sources': [
                'Книга: Разумный инвестор — Бенджамин Грэм',
                'https://www.investopedia.com/terms/r/riskrewardratio.asp',
            ],
        },
        {
            'id': 'diversification',
            'title': 'Диверсификация',
            'pages': [
                'Распределение по активам снижает влияние одной ошибки.',
                'Диверсифицируйте по классам, секторам, странам и времени.',
            ],
            'sources': [
                'Книга: Случайная прогулка по Уолл‑стрит — Бёртон Малкил',
                'https://www.investopedia.com/terms/d/diversification.asp',
            ],
        },
        {
            'id': 'market-cap',
            'title': 'Капитализация',
            'pages': [
                'Капитализация = цена × количество акций.',
                'Крупные компании стабильнее, малые могут расти быстрее, но риск выше.',
            ],
            'sources': [
                'Книга: Обыкновенные акции и необыкновенные прибыли — Филип Фишер',
                'https://www.investopedia.com/terms/m/marketcapitalization.asp',
            ],
        },
        {
            'id': 'liquidity',
            'title': 'Ликвидность',
            'pages': [
                'Ликвидность — это скорость покупки/продажи без сильного изменения цены.',
                'Низкая ликвидность = большие спреды и проскальзывание.',
            ],
            'sources': [
                'https://www.investopedia.com/terms/l/liquidity.asp',
            ],
        },
        {
            'id': 'valuation',
            'title': 'Оценка (P/E, P/B)',
            'pages': [
                'P/E показывает, сколько лет окупится цена при текущей прибыли.',
                'P/B полезен для банков и компаний с большим балансом.',
            ],
            'sources': [
                'Книга: Оценка бизнеса — McKinsey',
                'https://www.investopedia.com/terms/p/price-earningsratio.asp',
            ],
        },
        {
            'id': 'earnings',
            'title': 'Отчётность компаний',
            'pages': [
                'Смотрите выручку, маржу, прогноз и EPS.',
                'Рынок реагирует на ожидания, а не только на факт.',
            ],
            'sources': [
                'https://www.investopedia.com/terms/e/earnings.asp',
            ],
        },
        {
            'id': 'dca',
            'title': 'DCA (усреднение)',
            'pages': [
                'Инвестируйте фиксированную сумму регулярно.',
                'Снижает риск неправильного тайминга.',
            ],
            'sources': [
                'https://www.investopedia.com/terms/d/dollarcostaveraging.asp',
            ],
        },
        {
            'id': 'rebalance',
            'title': 'Ребалансировка',
            'pages': [
                'Возвращает портфель к целевым долям после движения рынка.',
                'Снижает риск и фиксирует прибыль.',
            ],
            'sources': [
                'Книга: The Bogleheads\' Guide to Investing',
                'https://www.investopedia.com/terms/r/rebalancing.asp',
            ],
        },
        {
            'id': 'etf',
            'title': 'ETF и ПИФ',
            'pages': [
                'ETF торгуются в течение дня, ПИФ — раз в день.',
                'ETF обычно дешевле и налогово эффективнее.',
            ],
            'sources': [
                'https://www.investopedia.com/terms/e/etf.asp',
            ],
        },
        {
            'id': 'inflation',
            'title': 'Инфляция и реальная доходность',
            'pages': [
                'Реальная доходность = номинальная − инфляция.',
                'Инфляция снижает силу кэша и облигаций, но акции могут компенсировать.',
            ],
            'sources': [
                'https://www.investopedia.com/terms/i/inflation.asp',
            ],
        },
        {
            'id': 'macd-rsi',
            'title': 'MACD и RSI',
            'pages': [
                'MACD показывает тренд и импульс, RSI — перекупленность/перепроданность.',
                'Индикаторы используйте вместе с управлением рисками.',
            ],
            'sources': [
                'https://www.investopedia.com/terms/m/macd.asp',
                'https://www.investopedia.com/terms/r/rsi.asp',
            ],
        },
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
    def _lang(self, language: str | None) -> str:
        return 'ru' if (language or '').lower().startswith('ru') else 'en'

    async def get_lessons(self, language: str = 'en') -> list[dict[str, object]]:
        lang = self._lang(language)
        return LESSONS.get(lang, LESSONS['en'])

    async def get_lesson(self, language: str, lesson_id: str) -> dict[str, object] | None:
        lessons = await self.get_lessons(language)
        for lesson in lessons:
            if str(lesson.get('id')) == lesson_id:
                return lesson
        return None

    async def get_glossary(self, language: str = 'en') -> list[str]:
        lang = self._lang(language)
        return GLOSSARY.get(lang, GLOSSARY['en'])

    async def get_quiz(self) -> str:
        return 'Q: What is diversification?\nA) Buying one asset\nB) Spreading across assets'
