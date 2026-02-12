from __future__ import annotations


class EducationService:
    async def get_lessons(self) -> list[str]:
        return [
            'Risk vs Reward: balancing upside and downside',
            'Diversification: why it matters',
            'What is market cap?',
            'Understanding liquidity',
            'MACD and RSI basics',
            'Portfolio rebalancing strategies',
            'On-chain metrics 101',
            'Options: calls vs puts',
        ]

    async def get_glossary(self) -> list[str]:
        return [
            'Alpha — excess return over benchmark',
            'Beta — volatility vs market',
            'Liquidity — ease of buying/selling',
            'Spread — bid/ask difference',
        ]

    async def get_quiz(self) -> str:
        return 'Q: What is diversification?\nA) Buying one asset\nB) Spreading across assets'
