from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Awaitable
from html import escape
from datetime import datetime

from core.permissions import UserContext, has_access, missing_access_message, is_admin_allowed
from core.i18n import t
from core.ui import UIMessage, ButtonSpec, format_section, format_kv, paginate
from services.stocks_service import StocksService
from services.crypto_service import CryptoService
from services.ton_service import TonService
from services.nft_service import NftService
from services.forex_service import ForexService
from services.news_service import NewsService
from services.translation_service import TranslationService
from services.education_service import EducationService
from services.portfolio_service import PortfolioService
from services.alert_service import AlertService
from services.user_service import UserService
from services.payment_service import PaymentService
from services.link_service import LinkService
from services.exchange_service import ExchangeService


@dataclass
class Router:
    stocks: StocksService
    crypto: CryptoService
    ton: TonService
    nft: NftService
    forex: ForexService
    news: NewsService
    education: EducationService
    portfolio: PortfolioService
    alerts: AlertService
    users: UserService
    payments: PaymentService
    links: LinkService
    exchanges: ExchangeService
    webapp_url: str
    discord_url: str
    translator: TranslationService

    def _t(self, user: UserContext, key: str, **kwargs: str) -> str:
        return t(key, user.language, **kwargs)

    def _btn(self, user: UserContext, key: str, action: str) -> ButtonSpec:
        return ButtonSpec(self._t(user, key), action)

    def main_menu(self, user: UserContext, display_name: str | None = None) -> UIMessage:
        buttons = [
            [self._btn(user, 'btn.start_here', 'menu:onboarding'), self._btn(user, 'btn.quick_prices', 'action:crypto_prices')],
            [self._btn(user, 'btn.markets', 'menu:markets'), self._btn(user, 'btn.crypto', 'menu:crypto')],
            [self._btn(user, 'btn.nft', 'menu:nft'), self._btn(user, 'btn.ton', 'menu:ton')],
            [self._btn(user, 'btn.portfolio', 'menu:portfolio'), self._btn(user, 'btn.education', 'menu:education')],
            [self._btn(user, 'btn.news', 'menu:news'), self._btn(user, 'btn.settings', 'menu:settings')],
            [self._btn(user, 'btn.profile', 'menu:profile')],
        ]
        if self.discord_url:
            buttons.append([self._btn(user, 'btn.discord', f'url:{self.discord_url}')])
        if self.webapp_url:
            buttons.append([self._btn(user, 'btn.open_app', f'webapp:{self.webapp_url}')])

        intro = self._t(
            user,
            'main.intro',
            username=display_name or user.username or 'Investor',
            tier=self._t(user, f'tier.{user.tier}'),
        )
        text = format_section(self._t(user, 'main.title'), intro)
        return UIMessage(text=text, buttons=buttons)

    def menu(self, menu_id: str, user: UserContext) -> UIMessage:
        menus: dict[str, UIMessage] = {
            'markets': UIMessage(
                text=format_section(self._t(user, 'menu.markets.title'), self._t(user, 'menu.markets.body')),
                buttons=[
                    [self._btn(user, 'btn.stocks', 'menu:stocks'), self._btn(user, 'btn.etfs', 'menu:etfs')],
                    [self._btn(user, 'btn.forex', 'menu:forex')],
                    [self._btn(user, 'btn.back', 'menu:main')],
                ],
            ),
            'onboarding': UIMessage(
                text=format_section(self._t(user, 'menu.onboarding.title'), self._t(user, 'menu.onboarding.body')),
                buttons=[
                    [self._btn(user, 'btn.prices', 'action:crypto_prices:onboarding'), self._btn(user, 'btn.add_asset', 'action:portfolio_add')],
                    [self._btn(user, 'btn.create_alert', 'menu:alerts'), self._btn(user, 'btn.mini_lessons', 'action:education_lessons')],
                    [self._btn(user, 'btn.back', 'menu:main')],
                ],
            ),
            'stocks': UIMessage(
                text=format_section(self._t(user, 'menu.stocks.title'), self._t(user, 'menu.stocks.body')),
                buttons=[
                    [self._btn(user, 'btn.price', 'action:stocks_price'), self._btn(user, 'btn.fundamentals', 'action:stocks_fundamentals')],
                    [self._btn(user, 'btn.ratios', 'action:stocks_ratios'), self._btn(user, 'btn.earnings', 'action:stocks_earnings')],
                    [self._btn(user, 'btn.dividends', 'action:stocks_dividends'), self._btn(user, 'btn.find_stock', 'action:stocks_find')],
                    [self._btn(user, 'btn.top_stocks', 'action:stocks_top:popular:1')],
                    [self._btn(user, 'btn.valuation', 'action:stocks_valuation')],
                    [self._btn(user, 'btn.back', 'menu:markets')],
                ],
            ),
            'etfs': UIMessage(
                text=format_section(self._t(user, 'menu.etfs.title'), self._t(user, 'menu.etfs.body')),
                buttons=[
                    [self._btn(user, 'btn.top_gainers', 'action:etf_top:gainers:1'), self._btn(user, 'btn.top_losers', 'action:etf_top:losers:1')],
                    [self._btn(user, 'btn.top_volume', 'action:etf_top:volume:1'), self._btn(user, 'btn.list', 'action:etfs')],
                    [self._btn(user, 'btn.back', 'menu:markets')],
                ],
            ),
            'forex': UIMessage(
                text=format_section(self._t(user, 'menu.forex.title'), self._t(user, 'menu.forex.body')),
                buttons=[
                    [self._btn(user, 'btn.rates', 'action:forex_rates'), self._btn(user, 'btn.top_pairs', 'action:forex_top:gainers:1')],
                    [self._btn(user, 'btn.find_pair', 'action:forex_find_input')],
                    [self._btn(user, 'btn.back', 'menu:markets')],
                ],
            ),
            'crypto': UIMessage(
                text=format_section(self._t(user, 'menu.crypto.title'), self._t(user, 'menu.crypto.body')),
                buttons=[
                    [self._btn(user, 'btn.prices', 'action:crypto_prices'), self._btn(user, 'btn.alerts', 'action:alerts_crypto')],
                    [self._btn(user, 'btn.dominance', 'action:crypto_dominance'), self._btn(user, 'btn.onchain', 'action:crypto_onchain')],
                    [self._btn(user, 'btn.find_asset', 'action:crypto_find'), self._btn(user, 'btn.top_100', 'action:crypto_top')],
                    [self._btn(user, 'btn.back', 'menu:main')],
                ],
            ),
            'ton': UIMessage(
                text=format_section(self._t(user, 'menu.ton.title'), self._t(user, 'menu.ton.body')),
                buttons=[
                    [self._btn(user, 'btn.price', 'action:ton_price'), self._btn(user, 'btn.wallet_info', 'action:ton_wallet')],
                    [self._btn(user, 'btn.usernames', 'action:ton_usernames'), self._btn(user, 'btn.nfts', 'action:ton_nfts')],
                    [self._btn(user, 'btn.gifts', 'action:ton_gifts'), self._btn(user, 'btn.projects', 'action:ton_projects')],
                    [self._btn(user, 'btn.back', 'menu:main')],
                ],
            ),
            'nft': UIMessage(
                text=format_section(self._t(user, 'menu.nft.title'), self._t(user, 'menu.nft.body')),
                buttons=[
                    [self._btn(user, 'btn.floor_prices', 'action:nft_floor'), self._btn(user, 'btn.collections', 'action:nft_collections')],
                    [self._btn(user, 'btn.search', 'action:nft_search')],
                    [self._btn(user, 'btn.back', 'menu:main')],
                ],
            ),
            'portfolio': UIMessage(
                text=format_section(self._t(user, 'menu.portfolio.title'), self._t(user, 'menu.portfolio.body')),
                buttons=self._portfolio_buttons(user),
            ),
            'portfolio_sync': UIMessage(
                text=format_section(self._t(user, 'menu.sync.title'), self._t(user, 'menu.sync.body')),
                buttons=[
                    [self._btn(user, 'btn.sync_exchange', 'action:portfolio_link_exchange'), self._btn(user, 'btn.sync_wallet', 'action:portfolio_link_wallet')],
                    [self._btn(user, 'btn.sync_run', 'action:portfolio_sync_run')],
                    [self._btn(user, 'btn.sync_links', 'action:portfolio_links')],
                    [self._btn(user, 'btn.csv_import', 'action:portfolio_import_csv'), self._btn(user, 'btn.csv_export', 'action:portfolio_export_csv')],
                    [self._btn(user, 'btn.back', 'menu:portfolio')],
                ],
            ),
            'alerts': UIMessage(
                text=format_section(self._t(user, 'menu.alerts.title'), self._t(user, 'menu.alerts.body')),
                buttons=[
                    [self._btn(user, 'btn.price_alert', 'action:alerts_price_add'), self._btn(user, 'btn.percent_alert', 'action:alerts_percent_add')],
                    [self._btn(user, 'btn.view_alerts', 'action:alerts_list')],
                    [self._btn(user, 'btn.back', 'menu:portfolio')],
                ],
            ),
            'education': UIMessage(
                text=format_section(self._t(user, 'menu.education.title'), self._t(user, 'menu.education.body')),
                buttons=[
                    [self._btn(user, 'btn.mini_lessons', 'action:education_lessons'), self._btn(user, 'btn.glossary', 'action:education_glossary')],
                    [self._btn(user, 'btn.quizzes', 'action:education_quiz')],
                    [self._btn(user, 'btn.back', 'menu:main')],
                ],
            ),
            'news': UIMessage(
                text=format_section(self._t(user, 'menu.news.title'), self._t(user, 'menu.news.body')),
                buttons=[
                    [self._btn(user, 'btn.headlines', 'action:news_headlines'), self._btn(user, 'btn.project_news', 'action:news_project')],
                    [self._btn(user, 'btn.back', 'menu:main')],
                ],
            ),
            'settings': self._settings_menu(user),
            'admin': self._admin_menu(user),
            'language': self._language_menu(user),
            'profile': self._profile_menu(user),
        }
        return menus.get(menu_id, self.main_menu(user))

    def _portfolio_buttons(self, user: UserContext) -> list[list[ButtonSpec]]:
        return [
            [self._btn(user, 'btn.add_asset', 'action:portfolio_add'), self._btn(user, 'btn.remove_asset', 'action:portfolio_remove')],
            [self._btn(user, 'btn.holdings', 'action:portfolio_list')],
            [self._btn(user, 'btn.pnl', 'action:portfolio_pnl'), self._btn(user, 'btn.allocation', 'action:portfolio_allocation')],
            [self._btn(user, 'btn.sync', 'menu:portfolio_sync')],
            [self._btn(user, 'btn.alerts_menu', 'menu:alerts')],
            [self._btn(user, 'btn.back', 'menu:main')],
        ]

    async def build_portfolio_menu(self, user: UserContext) -> UIMessage:
        items = await self.portfolio.list_assets(user)
        if not items:
            text = format_section(self._t(user, 'menu.portfolio.title'), self._t(user, 'msg.no_holdings'))
            return UIMessage(text=text, buttons=self._portfolio_buttons(user))

        lines = [self._t(user, 'menu.portfolio.body'), "", f"*{self._t(user, 'section.holdings')}*"]
        for item in items[:15]:
            symbol = item.get('symbol', 'N/A')
            asset_type = item.get('asset_type', 'N/A')
            amount = item.get('amount', 'N/A')
            cost = item.get('cost_basis', 'N/A')
            lines.append(
                f"{symbol} | {self._t(user, 'label.asset_type')}: {asset_type} | "
                f"{self._t(user, 'label.amount')}: {amount} | {self._t(user, 'label.cost_basis')}: {cost}"
            )
        text = format_section(self._t(user, 'menu.portfolio.title'), "\n".join(lines))
        return UIMessage(text=text, buttons=self._portfolio_buttons(user))

    def _settings_menu(self, user: UserContext) -> UIMessage:
        buttons = [
            [self._btn(user, 'btn.upgrade_pro', 'action:subscription_upgrade_pro'), self._btn(user, 'btn.upgrade_elite', 'action:subscription_upgrade_elite')],
            [self._btn(user, 'btn.subscription', 'action:subscription_status')],
            [self._btn(user, 'btn.billing', 'action:subscription_manage')],
            [self._btn(user, 'btn.language', 'menu:language')],
            [self._btn(user, 'btn.back', 'menu:main')],
        ]
        if user.is_admin:
            buttons.insert(0, [self._btn(user, 'btn.admin', 'menu:admin')])
        text = format_section(self._t(user, 'menu.settings.title'), self._t(user, 'menu.settings.body', tier=self._t(user, f'tier.{user.tier}')))
        return UIMessage(text=text, buttons=buttons)

    def _admin_menu(self, user: UserContext) -> UIMessage:
        if not is_admin_allowed(user):
            return UIMessage(text=self._t(user, 'msg.admin_required'), buttons=[[self._btn(user, 'btn.back', 'menu:settings')]])
        buttons = [
            [self._btn(user, 'btn.broadcast', 'action:admin_broadcast')],
            [self._btn(user, 'btn.user_stats', 'action:admin_stats')],
            [self._btn(user, 'btn.feature_toggle', 'action:admin_toggle')],
            [self._btn(user, 'btn.verify', 'action:admin_verify')],
            [self._btn(user, 'btn.back', 'menu:settings')],
        ]
        return UIMessage(text=f"*{self._t(user, 'menu.admin.title')}*", buttons=buttons)

    def _language_menu(self, user: UserContext) -> UIMessage:
        buttons = [
            [self._btn(user, 'btn.lang_ru', 'action:language_set_ru'), self._btn(user, 'btn.lang_en', 'action:language_set_en')],
            [self._btn(user, 'btn.back', 'menu:settings')],
        ]
        return UIMessage(text=format_section(self._t(user, 'menu.language.title'), self._t(user, 'menu.language.body')), buttons=buttons)

    def _profile_menu(self, user: UserContext) -> UIMessage:
        badge = self._t(user, f'badge.{user.badge}')
        username = user.username or 'N/A'
        text = format_section(
            self._t(user, 'menu.profile.title'),
            self._t(user, 'menu.profile.body', badge=badge, tier=self._t(user, f'tier.{user.tier}'), username=username),
        )
        buttons = [[self._btn(user, 'btn.back', 'menu:main')]]
        return UIMessage(text=text, buttons=buttons)

    async def handle_action(self, action: str, user: UserContext, payload: str | None = None) -> UIMessage:
        action_map: dict[str, Callable[[], Awaitable[UIMessage]]] = {
            'stocks_price': lambda: self._stocks_price(user),
            'stocks_fundamentals': lambda: self._stocks_fundamentals(user),
            'stocks_fundamentals_input': lambda: self._stocks_fundamentals_input(user),
            'stocks_fundamentals_portfolio': lambda: self._stocks_fundamentals_portfolio(user, payload),
            'stocks_fundamentals_symbol': lambda: self._stocks_fundamentals_symbol(user, payload),
            'stocks_ratios': lambda: self._stocks_ratios(user),
            'stocks_ratios_input': lambda: self._stocks_ratios_input(user),
            'stocks_ratios_portfolio': lambda: self._stocks_ratios_portfolio(user, payload),
            'stocks_ratios_symbol': lambda: self._stocks_ratios_symbol(user, payload),
            'stocks_earnings': lambda: self._stocks_earnings(user),
            'stocks_earnings_input': lambda: self._stocks_earnings_input(user),
            'stocks_earnings_portfolio': lambda: self._stocks_earnings_portfolio(user, payload),
            'stocks_earnings_symbol': lambda: self._stocks_earnings_symbol(user, payload),
            'stocks_dividends': lambda: self._stocks_dividends(user),
            'stocks_dividends_input': lambda: self._stocks_dividends_input(user),
            'stocks_dividends_portfolio': lambda: self._stocks_dividends_portfolio(user, payload),
            'stocks_dividends_symbol': lambda: self._stocks_dividends_symbol(user, payload),
            'stocks_find': lambda: self._stocks_find(user),
            'stocks_find_input': lambda: self._stocks_find_input(user),
            'stocks_profile': lambda: self._stocks_profile(user, payload),
            'stocks_top': lambda: self._stocks_top(user, payload),
            'stocks_valuation': lambda: self._stocks_valuation(user),
            'etfs': lambda: self._etfs(user),
            'etf_top': lambda: self._etf_top(user, payload),
            'etf_profile': lambda: self._stocks_profile(user, payload),
            'forex_rates': lambda: self._forex_rates(user),
            'forex_top': lambda: self._forex_top(user, payload),
            'forex_find_input': lambda: self._forex_find_input(user),
            'forex_profile': lambda: self._forex_profile(user, payload),
            'crypto_prices': lambda: self._crypto_prices(user),
            'crypto_dominance': lambda: self._crypto_dominance(user),
            'crypto_onchain': lambda: self._crypto_onchain(user),
            'crypto_find': lambda: self._crypto_find(user),
            'crypto_profile': lambda: self._crypto_profile(user, payload),
            'crypto_top': lambda: self._crypto_top(user, payload),
            'alerts_crypto': lambda: self._alerts_crypto(user),
            'alerts_price_add': lambda: self._alerts_price_add(user),
            'alerts_percent_add': lambda: self._alerts_percent_add(user),
            'alerts_list': lambda: self._alerts_list(user),
            'ton_price': lambda: self._ton_price(user),
            'ton_nfts': lambda: self._ton_nfts(user),
            'ton_wallet': lambda: self._ton_wallet(user),
            'ton_usernames': lambda: self._ton_usernames(user),
            'ton_gifts': lambda: self._ton_gifts(user),
            'ton_projects': lambda: self._ton_projects(user, payload),
            'nft_floor': lambda: self._nft_floor(user),
            'nft_collections': lambda: self._nft_collections(user),
            'nft_search': lambda: self._nft_search(user),
            'portfolio_add': lambda: self._portfolio_add(user),
            'portfolio_add_type': lambda: self._portfolio_add_type(user, payload),
            'portfolio_add_custom': lambda: self._portfolio_add_custom(user),
            'portfolio_remove': lambda: self._portfolio_remove_menu(user, payload),
            'portfolio_remove_symbol': lambda: self._portfolio_remove_symbol(user, payload),
            'portfolio_list': lambda: self._portfolio_list(user),
            'portfolio_pnl': lambda: self._portfolio_pnl(user),
            'portfolio_allocation': lambda: self._portfolio_allocation(user),
            'portfolio_link_exchange': lambda: self._portfolio_link_exchange(user),
            'portfolio_link_wallet': lambda: self._portfolio_link_wallet(user),
            'portfolio_sync_run': lambda: self._portfolio_sync_run(user),
            'portfolio_links': lambda: self._portfolio_links(user),
            'portfolio_link_remove': lambda: self._portfolio_link_remove(user, payload),
            'portfolio_import_csv': lambda: self._portfolio_import_csv(user),
            'portfolio_export_csv': lambda: self._portfolio_export_csv(user),
            'education_lessons': lambda: self._education_lessons(user, payload),
            'education_glossary': lambda: self._education_glossary(user),
            'education_quiz': lambda: self._education_quiz(user),
            'news_headlines': lambda: self._news_headlines(user, payload),
            'news_project': lambda: self._news_project(user, payload),
            'subscription_status': lambda: self._subscription_status(user),
            'subscription_manage': lambda: self._subscription_manage(user),
            'subscription_upgrade_pro': lambda: self._subscription_upgrade(user, 'pro'),
            'subscription_upgrade_elite': lambda: self._subscription_upgrade(user, 'elite'),
            'language_set_ru': lambda: self._set_language(user, 'ru'),
            'language_set_en': lambda: self._set_language(user, 'en'),
            'admin_broadcast': lambda: self._admin_broadcast(user),
            'admin_stats': lambda: self._admin_stats(user),
            'admin_toggle': lambda: self._admin_toggle(user),
            'admin_verify': lambda: self._admin_verify(user),
        }
        handler = action_map.get(action)
        if not handler:
            return UIMessage(text=self._t(user, 'msg.unknown_action'))
        message = await handler()
        if message.buttons is None:
            back_menu = ACTION_BACK_MENU.get(action, 'main')
            message.buttons = [
                [self._btn(user, 'btn.back', f'menu:{back_menu}')],
                [self._btn(user, 'btn.main_menu', 'menu:main')],
            ]
        return message

    async def _stocks_price(self, user: UserContext) -> UIMessage:
        quote = await self.stocks.get_price('AAPL')
        text = format_section(self._t(user, 'menu.stocks.title'), format_kv([
            ('Symbol', quote['symbol']),
            ('Price', quote['price']),
            ('Change', quote['change']),
        ]))
        return UIMessage(text=text)

    async def _stocks_find(self, user: UserContext) -> UIMessage:
        popular = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'TSLA', 'JPM']
        rows: list[list[ButtonSpec]] = []
        row: list[ButtonSpec] = []
        for sym in popular:
            row.append(ButtonSpec(sym, f'action:stocks_profile:{sym}'))
            if len(row) == 4:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        rows.append([self._btn(user, 'btn.search', 'action:stocks_find_input')])
        rows.append([self._btn(user, 'btn.back', 'menu:stocks')])
        return UIMessage(text=self._t(user, 'msg.stocks_find_menu'), buttons=rows)

    async def _stocks_find_input(self, user: UserContext) -> UIMessage:
        return UIMessage(text=self._t(user, 'msg.stocks_find'), expect_input='stocks_find', input_hint='AAPL / TSLA / NVDA')

    async def _stocks_valuation(self, user: UserContext) -> UIMessage:
        return UIMessage(
            text=self._t(user, 'msg.stocks_valuation_hint'),
            expect_input='stocks_valuation',
            input_hint='AAPL / TSLA / NVDA',
        )

    async def _stocks_fundamentals(self, user: UserContext) -> UIMessage:
        if not has_access(user, 'stocks_fundamentals'):
            return UIMessage(text=missing_access_message('stocks_fundamentals', user.language))
        return self._stock_metric_menu(user, 'btn.fundamentals', 'stocks_fundamentals')

    async def _stocks_fundamentals_input(self, user: UserContext) -> UIMessage:
        if not has_access(user, 'stocks_fundamentals'):
            return UIMessage(text=missing_access_message('stocks_fundamentals', user.language))
        return UIMessage(
            text=self._t(user, 'msg.stocks_find'),
            expect_input='stocks_fundamentals_symbol',
            input_hint='AAPL / TSLA / SPY',
        )

    async def _stocks_fundamentals_portfolio(self, user: UserContext, payload: str | None) -> UIMessage:
        return await self._stock_metric_portfolio(user, payload, 'stocks_fundamentals', 'btn.fundamentals')

    async def _stocks_fundamentals_symbol(self, user: UserContext, payload: str | None) -> UIMessage:
        symbol = (payload or 'AAPL').upper()
        return await self.build_stock_fundamentals(user, symbol)

    async def _stocks_ratios(self, user: UserContext) -> UIMessage:
        if not has_access(user, 'stocks_ratios'):
            return UIMessage(text=missing_access_message('stocks_ratios', user.language))
        return self._stock_metric_menu(user, 'btn.ratios', 'stocks_ratios')

    async def _stocks_ratios_input(self, user: UserContext) -> UIMessage:
        if not has_access(user, 'stocks_ratios'):
            return UIMessage(text=missing_access_message('stocks_ratios', user.language))
        return UIMessage(
            text=self._t(user, 'msg.stocks_find'),
            expect_input='stocks_ratios_symbol',
            input_hint='AAPL / TSLA / SPY',
        )

    async def _stocks_ratios_portfolio(self, user: UserContext, payload: str | None) -> UIMessage:
        return await self._stock_metric_portfolio(user, payload, 'stocks_ratios', 'btn.ratios')

    async def _stocks_ratios_symbol(self, user: UserContext, payload: str | None) -> UIMessage:
        symbol = (payload or 'AAPL').upper()
        return await self.build_stock_ratios(user, symbol)

    async def _stocks_earnings(self, user: UserContext) -> UIMessage:
        if not has_access(user, 'stocks_earnings'):
            return UIMessage(text=missing_access_message('stocks_earnings', user.language))
        return self._stock_metric_menu(user, 'btn.earnings', 'stocks_earnings')

    async def _stocks_earnings_input(self, user: UserContext) -> UIMessage:
        if not has_access(user, 'stocks_earnings'):
            return UIMessage(text=missing_access_message('stocks_earnings', user.language))
        return UIMessage(
            text=self._t(user, 'msg.stocks_find'),
            expect_input='stocks_earnings_symbol',
            input_hint='AAPL / TSLA / SPY',
        )

    async def _stocks_earnings_portfolio(self, user: UserContext, payload: str | None) -> UIMessage:
        return await self._stock_metric_portfolio(user, payload, 'stocks_earnings', 'btn.earnings')

    async def _stocks_earnings_symbol(self, user: UserContext, payload: str | None) -> UIMessage:
        symbol = (payload or 'AAPL').upper()
        return await self.build_stock_earnings(user, symbol)

    async def _stocks_dividends(self, user: UserContext) -> UIMessage:
        if not has_access(user, 'stocks_dividends'):
            return UIMessage(text=missing_access_message('stocks_dividends', user.language))
        return self._stock_metric_menu(user, 'btn.dividends', 'stocks_dividends')

    async def _stocks_dividends_input(self, user: UserContext) -> UIMessage:
        if not has_access(user, 'stocks_dividends'):
            return UIMessage(text=missing_access_message('stocks_dividends', user.language))
        return UIMessage(
            text=self._t(user, 'msg.stocks_find'),
            expect_input='stocks_dividends_symbol',
            input_hint='AAPL / TSLA / SPY',
        )

    async def _stocks_dividends_portfolio(self, user: UserContext, payload: str | None) -> UIMessage:
        return await self._stock_metric_portfolio(user, payload, 'stocks_dividends', 'btn.dividends')

    async def _stocks_dividends_symbol(self, user: UserContext, payload: str | None) -> UIMessage:
        symbol = (payload or 'AAPL').upper()
        return await self.build_stock_dividends(user, symbol)

    async def _stocks_profile(self, user: UserContext, payload: str | None) -> UIMessage:
        symbol = (payload or 'AAPL').upper()
        return await self.build_stock_profile(user, symbol)

    def _stock_metric_menu(self, user: UserContext, title_key: str, action_prefix: str) -> UIMessage:
        text = format_section(self._t(user, title_key), self._t(user, 'msg.choose_stock_source'))
        buttons = [
            [self._btn(user, 'btn.from_portfolio', f'action:{action_prefix}_portfolio:1'), self._btn(user, 'btn.enter_ticker', f'action:{action_prefix}_input')],
            [self._btn(user, 'btn.back', 'menu:stocks')],
        ]
        return UIMessage(text=text, buttons=buttons)

    async def _stock_metric_portfolio(self, user: UserContext, payload: str | None, action_prefix: str, title_key: str) -> UIMessage:
        if not has_access(user, action_prefix):
            return UIMessage(text=missing_access_message(action_prefix, user.language))
        items = await self.portfolio.list_assets(user)
        if not items:
            return UIMessage(
                text=self._t(user, 'msg.no_stock_holdings'),
                buttons=[
                    [self._btn(user, 'btn.enter_ticker', f'action:{action_prefix}_input')],
                    [self._btn(user, 'btn.back', 'menu:stocks')],
                ],
            )
        allowed_types = {'stock', 'stocks', 'equity', 'etf', 'fund', 'funds'}
        counts: dict[str, int] = {}
        order: list[str] = []
        for item in items:
            asset_type = str(item.get('asset_type') or '').lower()
            if asset_type not in allowed_types:
                continue
            symbol = str(item.get('symbol') or '').upper()
            if not symbol:
                continue
            counts[symbol] = counts.get(symbol, 0) + 1
            if symbol not in order:
                order.append(symbol)

        if not order:
            return UIMessage(
                text=self._t(user, 'msg.no_stock_holdings'),
                buttons=[
                    [self._btn(user, 'btn.enter_ticker', f'action:{action_prefix}_input')],
                    [self._btn(user, 'btn.back', 'menu:stocks')],
                ],
            )

        page = int(payload or '1')
        page_items, page, total = paginate(order, page, per_page=8)
        buttons: list[list[ButtonSpec]] = []
        row: list[ButtonSpec] = []
        for symbol in page_items:
            label = f"{symbol} ({counts.get(symbol, 0)})"
            row.append(ButtonSpec(label, f"action:{action_prefix}_symbol:{symbol}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        nav_row: list[ButtonSpec] = []
        if page > 1:
            nav_row.append(self._btn(user, 'btn.prev', f'action:{action_prefix}_portfolio:{page-1}'))
        if page < total:
            nav_row.append(self._btn(user, 'btn.next', f'action:{action_prefix}_portfolio:{page+1}'))
        if nav_row:
            buttons.append(nav_row)

        buttons.append([self._btn(user, 'btn.enter_ticker', f'action:{action_prefix}_input')])
        buttons.append([self._btn(user, 'btn.back', 'menu:stocks')])
        text = format_section(self._t(user, title_key), self._t(user, 'msg.choose_stock', count=str(len(order))))
        return UIMessage(text=text, buttons=buttons)

    async def _stocks_top(self, user: UserContext, payload: str | None) -> UIMessage:
        sort, page = _parse_sort_page(payload, default_sort='popular')
        symbols = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'TSLA', 'JPM', 'V', 'UNH', 'BRK.B', 'XOM', 'AVGO', 'COST', 'LLY']
        quotes = await self.stocks.get_quotes_details(symbols)
        items = _sort_quotes(quotes, sort)
        rows = [self._format_stock_row(user, item) for item in items]
        page_items, page, total = paginate(rows, page, per_page=8)
        title = f"{self._t(user, 'btn.top_stocks')} ({page}/{total})"
        text = format_section(title, "\n".join(page_items) if page_items else 'N/A')
        buttons = _sort_buttons(user, 'stocks_top', sort, page)
        buttons.extend(_page_buttons(user, 'stocks_top', sort, page, total))
        buttons.append([self._btn(user, 'btn.back', 'menu:stocks')])
        return UIMessage(text=text, buttons=buttons)

    async def build_stock_fundamentals(self, user: UserContext, symbol: str) -> UIMessage:
        if not has_access(user, 'stocks_fundamentals'):
            return UIMessage(text=missing_access_message('stocks_fundamentals', user.language))
        sym = symbol.upper()
        data = await self.stocks.get_metrics(sym)
        lines = [
            f"*{sym}*",
            f"*{self._t(user, 'label.market_cap')}* — {self._t(user, 'hint.market_cap')}:\n{self._fmt_num(data.get('marketCapitalization'))}",
            f"*{self._t(user, 'label.eps')}* — {self._t(user, 'hint.eps')}:\n{self._fmt_num(data.get('epsTTM'))}",
            f"*{self._t(user, 'label.dividend_yield')}* — {self._t(user, 'hint.dividend')}:\n{self._fmt_num(data.get('dividendYieldIndicatedAnnual'), suffix='%')}",
            f"*{self._t(user, 'label.high_52w')}* / *{self._t(user, 'label.low_52w')}* — {self._t(user, 'hint.range_52w')}:\n{self._fmt_num(data.get('52WeekHigh'))} / {self._fmt_num(data.get('52WeekLow'))}",
            f"*{self._t(user, 'label.beta')}* — {self._t(user, 'hint.beta')}:\n{self._fmt_num(data.get('beta'))}",
        ]
        return UIMessage(text=format_section(self._t(user, 'btn.fundamentals'), "\n\n".join(lines)))

    async def build_stock_ratios(self, user: UserContext, symbol: str) -> UIMessage:
        if not has_access(user, 'stocks_ratios'):
            return UIMessage(text=missing_access_message('stocks_ratios', user.language))
        sym = symbol.upper()
        data = await self.stocks.get_metrics(sym)
        lines = [
            f"*{sym}*",
            f"*{self._t(user, 'label.pe')}* — {self._t(user, 'hint.pe')}:\n{self._fmt_num(data.get('peNormalizedAnnual') or data.get('peBasicExclExtraTTM'))}",
            f"*{self._t(user, 'label.pb')}* — {self._t(user, 'hint.pb')}:\n{self._fmt_num(data.get('pbAnnual'))}",
            f"*{self._t(user, 'label.roe')}* — {self._t(user, 'hint.roe')}:\n{self._fmt_num(data.get('roeTTM'), suffix='%')}",
            f"*{self._t(user, 'label.debt_to_equity')}* — {self._t(user, 'hint.debt_to_equity')}:\n{self._fmt_num(data.get('totalDebtToEquityAnnual'))}",
            f"*{self._t(user, 'label.current_ratio')}* — {self._t(user, 'hint.current_ratio')}:\n{self._fmt_num(data.get('currentRatioAnnual'))}",
        ]
        return UIMessage(text=format_section(self._t(user, 'btn.ratios'), "\n\n".join(lines)))

    async def build_stock_dividends(self, user: UserContext, symbol: str) -> UIMessage:
        if not has_access(user, 'stocks_dividends'):
            return UIMessage(text=missing_access_message('stocks_dividends', user.language))
        sym = symbol.upper()
        items = await self.stocks.get_dividends(sym)
        lines = [f"*{sym}*"]
        if items:
            lines.extend([f"{i['date']} — {i['amount']}" for i in items])
        else:
            lines.append(self._t(user, 'msg.dividends_empty'))
        return UIMessage(text=format_section(self._t(user, 'btn.dividends'), "\n".join(lines)))

    async def build_stock_earnings(self, user: UserContext, symbol: str) -> UIMessage:
        if not has_access(user, 'stocks_earnings'):
            return UIMessage(text=missing_access_message('stocks_earnings', user.language))
        sym = symbol.upper()
        items = await self.stocks.get_earnings(sym)
        lines = [f"*{sym}*"]
        if items:
            lines.extend([f"{i['date']} — EPS {i['eps']}" for i in items])
        else:
            lines.append(self._t(user, 'msg.earnings_empty'))
        return UIMessage(text=format_section(self._t(user, 'btn.earnings'), "\n".join(lines)))

    async def _etf_top(self, user: UserContext, payload: str | None) -> UIMessage:
        sort, page = _parse_sort_page(payload, default_sort='gainers')
        symbols = ['SPY', 'QQQ', 'VTI', 'IWM', 'DIA', 'XLK', 'XLF', 'XLV']
        quotes = await self.stocks.get_quotes_details(symbols)
        items = _sort_quotes(quotes, sort)
        rows = [self._format_stock_row(user, item) for item in items]
        page_items, page, total = paginate(rows, page, per_page=8)
        title = f"{self._t(user, 'btn.etfs')} ({page}/{total})"
        text = format_section(title, "\n".join(page_items) if page_items else 'N/A')
        buttons = _sort_buttons(user, 'etf_top', sort, page)
        buttons.extend(_page_buttons(user, 'etf_top', sort, page, total))
        buttons.append([self._btn(user, 'btn.back', 'menu:etfs')])
        return UIMessage(text=text, buttons=buttons)

    async def _forex_top(self, user: UserContext, payload: str | None) -> UIMessage:
        sort, page = _parse_sort_page(payload, default_sort='gainers')
        pairs = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD']
        items = await self.forex.get_pairs_changes(pairs)
        if sort == 'losers':
            items = sorted(items, key=lambda x: (x.get('change_pct') or 0))
        else:
            items = sorted(items, key=lambda x: -(x.get('change_pct') or 0))
        rows = [self._format_forex_row(user, item) for item in items]
        page_items, page, total = paginate(rows, page, per_page=6)
        title = f"{self._t(user, 'btn.top_pairs')} ({page}/{total})"
        text = format_section(title, "\n".join(page_items) if page_items else 'N/A')
        buttons = _sort_buttons(user, 'forex_top', sort, page, include_volume=False)
        buttons.extend(_page_buttons(user, 'forex_top', sort, page, total))
        buttons.append([self._btn(user, 'btn.back', 'menu:forex')])
        return UIMessage(text=text, buttons=buttons)

    async def _forex_find_input(self, user: UserContext) -> UIMessage:
        return UIMessage(text=self._t(user, 'msg.forex_find'), expect_input='forex_find', input_hint='EUR/USD')

    async def _forex_profile(self, user: UserContext, payload: str | None) -> UIMessage:
        pair = (payload or 'EUR/USD').upper()
        return await self.build_forex_profile(user, pair)

    async def build_stock_valuation(self, user: UserContext, symbol: str) -> UIMessage:
        sym = symbol.upper()
        quote = await self.stocks.get_price(sym)
        metrics = await self.stocks.get_metrics(sym)
        sentiment = await self.stocks.get_social_sentiment(sym)

        price_raw = quote.get('price')
        change_raw = quote.get('change')
        price = price_raw if isinstance(price_raw, str) else self._fmt_price(price_raw)
        change = change_raw if isinstance(change_raw, str) else self._fmt_pct(change_raw)

        pe_proxy = _num(metrics.get('peNormalizedAnnual') or metrics.get('peBasicExclExtraTTM'))
        eps = _num(metrics.get('epsTTM') or metrics.get('epsNormalizedAnnual'))
        growth = _num(metrics.get('epsGrowth3Y') or metrics.get('epsGrowth5Y'))
        graham_value, graham_note = _calc_graham_value(eps, growth)
        margin = _calc_margin_of_safety(graham_value, _num(price_raw))

        lines = [
            f"*{sym}*",
            f"{self._t(user, 'label.price')}: {price}",
            f"{self._t(user, 'label.change')}: {change}",
            "",
            f"*{self._t(user, 'section.valuation')}*",
            f"{self._t(user, 'label.cape_proxy')}: {self._fmt_num(pe_proxy)}",
            f"{self._t(user, 'label.graham_value')}: {self._fmt_num(graham_value, prefix='$')}",
            f"{self._t(user, 'label.growth_used')}: {graham_note}",
            f"{self._t(user, 'label.margin_safety')}: {self._fmt_num(margin, suffix='%')}",
        ]

        reddit = sentiment.get('reddit') or {}
        twitter = sentiment.get('twitter') or {}
        lines.extend([
            "",
            f"*{self._t(user, 'section.community')}*",
            f"Reddit — {self._t(user, 'label.score')}: {self._fmt_num(reddit.get('score'))} | "
            f"{self._t(user, 'label.mentions')}: {self._fmt_int(reddit.get('mentions'))} | "
            f"{self._t(user, 'label.pos_neg')}: {self._fmt_int(reddit.get('positive'))}/{self._fmt_int(reddit.get('negative'))}",
            f"Twitter — {self._t(user, 'label.score')}: {self._fmt_num(twitter.get('score'))} | "
            f"{self._t(user, 'label.mentions')}: {self._fmt_int(twitter.get('mentions'))} | "
            f"{self._t(user, 'label.pos_neg')}: {self._fmt_int(twitter.get('positive'))}/{self._fmt_int(twitter.get('negative'))}",
        ])

        return UIMessage(text="\n".join(lines))

    async def build_stock_profile(self, user: UserContext, symbol: str) -> UIMessage:
        sym = symbol.upper()
        quote = await self.stocks.get_quote_details(sym)
        metrics = await self.stocks.get_metrics(sym)
        news_items = await self.news.get_project_news(sym)

        price = self._fmt_price(quote.get('price'))
        change = self._fmt_pct(quote.get('change_pct'))
        volume = self._fmt_num(quote.get('volume'))
        market_cap = self._fmt_num(metrics.get('marketCapitalization'))
        pe = self._fmt_num(metrics.get('peNormalizedAnnual') or metrics.get('peBasicExclExtraTTM'))
        eps = self._fmt_num(metrics.get('epsTTM') or metrics.get('epsNormalizedAnnual'))
        beta = self._fmt_num(metrics.get('beta'))
        div_yield = self._fmt_num(metrics.get('dividendYieldIndicatedAnnual'), suffix='%')
        high_52 = self._fmt_num(metrics.get('52WeekHigh'))
        low_52 = self._fmt_num(metrics.get('52WeekLow'))
        pb = self._fmt_num(metrics.get('pbAnnual'))
        roe = self._fmt_num(metrics.get('roeTTM'), suffix='%')
        debt_to_equity = self._fmt_num(metrics.get('totalDebtToEquityAnnual'))
        current_ratio = self._fmt_num(metrics.get('currentRatioAnnual'))

        lines = [
            f"*{sym}*",
            f"{self._t(user, 'label.price')}: {price}",
            f"{self._t(user, 'label.change_24h')}: {change}",
            f"{self._t(user, 'label.volume')}: {volume}",
            f"{self._t(user, 'label.market_cap')}: {market_cap}",
            "",
            f"*{self._t(user, 'section.fundamentals')}*",
            f"{self._t(user, 'label.eps')}: {eps} — {self._t(user, 'hint.eps')}",
            f"{self._t(user, 'label.dividend_yield')}: {div_yield} — {self._t(user, 'hint.dividend')}",
            f"{self._t(user, 'label.high_52w')}: {high_52} | {self._t(user, 'label.low_52w')}: {low_52}",
            "",
            f"*{self._t(user, 'btn.ratios')}*",
            f"{self._t(user, 'label.pe')}: {pe} — {self._t(user, 'hint.pe')}",
            f"{self._t(user, 'label.pb')}: {pb} — {self._t(user, 'hint.pb')}",
            f"{self._t(user, 'label.roe')}: {roe} — {self._t(user, 'hint.roe')}",
            f"{self._t(user, 'label.debt_to_equity')}: {debt_to_equity} — {self._t(user, 'hint.debt_to_equity')}",
            f"{self._t(user, 'label.current_ratio')}: {current_ratio} — {self._t(user, 'hint.current_ratio')}",
            f"{self._t(user, 'label.beta')}: {beta} — {self._t(user, 'hint.beta')}",
        ]

        lines.append("")
        lines.append(f"*{self._t(user, 'section.news')}*")
        if news_items:
            for item in news_items[:2]:
                title = item.get('title') or 'N/A'
                source = item.get('source') or 'N/A'
                url = item.get('url') or ''
                if url:
                    lines.append(f"• {title} — {source}\n{url}")
                else:
                    lines.append(f"• {title} — {source}")
        else:
            lines.append(self._t(user, 'msg.news_empty'))
        return UIMessage(text="\n".join(lines))

    async def _crypto_profile(self, user: UserContext, payload: str | None) -> UIMessage:
        symbol = (payload or 'BTC').upper()
        return await self.build_crypto_profile(user, symbol)

    async def build_crypto_profile(self, user: UserContext, symbol: str) -> UIMessage:
        sym = symbol.upper()
        quote = await self.crypto.get_asset(sym)
        news_items = await self.news.get_project_news(sym)
        if not quote:
            return UIMessage(text=self._t(user, 'msg.crypto_not_found'))
        price = self._fmt_price(quote.get('price'))
        change = self._fmt_pct(quote.get('change_24h'))
        cap = self._fmt_cap(quote.get('market_cap'))
        volume = self._fmt_num(quote.get('volume_24h'))

        lines = [
            f"*{sym}*",
            f"{self._t(user, 'label.price')}: {price}",
            f"{self._t(user, 'label.change_24h')}: {change}",
            f"{self._t(user, 'label.market_cap')}: {cap}",
            f"{self._t(user, 'label.volume')}: {volume}",
            "",
            f"*{self._t(user, 'section.news')}*",
        ]
        if news_items:
            for item in news_items[:2]:
                title = item.get('title') or 'N/A'
                source = item.get('source') or 'N/A'
                url = item.get('url') or ''
                if url:
                    lines.append(f"• {title} — {source}\n{url}")
                else:
                    lines.append(f"• {title} — {source}")
        else:
            lines.append(self._t(user, 'msg.news_empty'))
        return UIMessage(text="\n".join(lines))

    async def build_forex_profile(self, user: UserContext, pair: str) -> UIMessage:
        data = await self.forex.get_pair_change(pair)
        if not data:
            return UIMessage(text=self._t(user, 'msg.forex_not_found'))
        rate = data.get('rate')
        change = data.get('change_pct')
        open_v = data.get('open')
        high_v = data.get('high')
        low_v = data.get('low')
        prev_close = data.get('prev_close')
        news_items = await self.news.get_project_news(pair)

        rate_str = f"{rate:.5f}" if isinstance(rate, (int, float)) else 'N/A'
        open_str = f"{open_v:.5f}" if isinstance(open_v, (int, float)) else self._fmt_num(open_v)
        high_str = f"{high_v:.5f}" if isinstance(high_v, (int, float)) else self._fmt_num(high_v)
        low_str = f"{low_v:.5f}" if isinstance(low_v, (int, float)) else self._fmt_num(low_v)
        prev_str = f"{prev_close:.5f}" if isinstance(prev_close, (int, float)) else self._fmt_num(prev_close)

        lines = [
            f"*{pair}*",
            f"{self._t(user, 'label.rate')}: {rate_str}",
            f"{self._t(user, 'label.change_24h')}: {self._fmt_pct(change)}",
            f"{self._t(user, 'label.open')}: {open_str} | {self._t(user, 'label.prev_close')}: {prev_str}",
            f"{self._t(user, 'label.high')}: {high_str} | {self._t(user, 'label.low')}: {low_str}",
            "",
            f"*{self._t(user, 'section.news')}*",
        ]
        if news_items:
            for item in news_items[:2]:
                title = item.get('title') or 'N/A'
                source = item.get('source') or 'N/A'
                url = item.get('url') or ''
                if url:
                    lines.append(f"• {title} — {source}\n{url}")
                else:
                    lines.append(f"• {title} — {source}")
        else:
            lines.append(self._t(user, 'msg.news_empty'))
        return UIMessage(text="\n".join(lines))

    def _fmt_num(self, value: object, prefix: str = '', suffix: str = '') -> str:
        if isinstance(value, (int, float)):
            return f"{prefix}{value:,.2f}{suffix}"
        return 'N/A'

    def _fmt_int(self, value: object) -> str:
        if isinstance(value, (int, float)):
            return f"{int(value)}"
        return 'N/A'

    async def _etfs(self, user: UserContext) -> UIMessage:
        items = await self.stocks.get_top_etfs()
        return UIMessage(text=format_section(self._t(user, 'btn.etfs'), "\n".join(items)))

    async def _forex_rates(self, user: UserContext) -> UIMessage:
        data = await self.forex.get_rates('USD', ['EUR', 'JPY', 'GBP'])
        lines = [f"USD/{k}: {v}" for k, v in data.items()]
        return UIMessage(text=format_section(self._t(user, 'btn.rates'), "\n".join(lines)))

    async def _crypto_prices(self, user: UserContext, payload: str | None = None) -> UIMessage:
        crypto_assets = await self.crypto.get_top_assets(10)
        crypto_lines = [self._format_asset_row(user, a) for a in crypto_assets]
        crypto_text = format_section(self._t(user, 'section.crypto_top'), "\n".join(crypto_lines) if crypto_lines else 'N/A')

        stock_symbols = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'TSLA', 'JPM', 'V', 'UNH']
        stock_quotes = await self.stocks.get_quotes(stock_symbols)
        label_change = self._t(user, 'label.change')
        stock_lines = []
        for sym in stock_symbols:
            q = stock_quotes.get(sym, {})
            price = q.get('price', 'N/A')
            change = q.get('change', 'N/A')
            stock_lines.append(f"{sym}: {price} | {label_change}: {change}")
        stocks_text = format_section(self._t(user, 'section.stocks_top'), "\n".join(stock_lines) if stock_lines else 'N/A')

        fund_symbols = ['SPY', 'QQQ', 'VTI', 'IWM', 'DIA', 'XLK', 'XLF', 'XLV']
        fund_quotes = await self.stocks.get_quotes(fund_symbols)
        fund_lines = []
        for sym in fund_symbols:
            q = fund_quotes.get(sym, {})
            price = q.get('price', 'N/A')
            change = q.get('change', 'N/A')
            description = self._t(user, f'fund.{sym.lower()}')
            fund_lines.append(f"{sym}: {price} | {label_change}: {change} | {description}")
        funds_text = format_section(self._t(user, 'section.funds_top'), "\n".join(fund_lines) if fund_lines else 'N/A')

        back_menu = (payload or 'crypto').strip()
        if back_menu not in ('crypto', 'onboarding', 'main'):
            back_menu = 'crypto'
        buttons = [
            [self._btn(user, 'btn.back', f'menu:{back_menu}')],
            [self._btn(user, 'btn.main_menu', 'menu:main')],
        ]
        return UIMessage(text=f"{crypto_text}\n\n{stocks_text}\n\n{funds_text}", buttons=buttons)

    async def _crypto_dominance(self, user: UserContext) -> UIMessage:
        data = await self.crypto.get_dominance()
        return UIMessage(text=format_section(self._t(user, 'btn.dominance'), format_kv(list(data.items()))))

    async def _crypto_onchain(self, user: UserContext) -> UIMessage:
        if not has_access(user, 'crypto_onchain'):
            return UIMessage(text=missing_access_message('crypto_onchain', user.language))
        data = await self.crypto.get_onchain_summary('bitcoin')
        return UIMessage(text=format_section(self._t(user, 'btn.onchain'), format_kv(list(data.items()))))

    async def _crypto_find(self, user: UserContext) -> UIMessage:
        return UIMessage(text=self._t(user, 'msg.crypto_find'), expect_input='crypto_find', input_hint='BTC / ETH / SOL')

    async def _crypto_top(self, user: UserContext, payload: str | None = None) -> UIMessage:
        page = int(payload or '1')
        assets = await self.crypto.get_top_assets(100)
        items = [self._format_asset_row(user, a) for a in assets]
        page_items, page, total = paginate(items, page, per_page=10)
        title = f"{self._t(user, 'btn.top_100')} ({page}/{total})"
        text = format_section(title, "\n".join(page_items) if page_items else 'N/A')
        buttons = []
        if page > 1:
            buttons.append([self._btn(user, 'btn.prev', f'page:crypto_top:{page-1}')])
        if page < total:
            buttons.append([self._btn(user, 'btn.next', f'page:crypto_top:{page+1}')])
        buttons.append([self._btn(user, 'btn.back', 'menu:crypto')])
        return UIMessage(text=text, buttons=buttons)

    async def _alerts_crypto(self, user: UserContext) -> UIMessage:
        return UIMessage(text=self._t(user, 'msg.alerts_hint'))

    async def _alerts_price_add(self, user: UserContext) -> UIMessage:
        return UIMessage(text=self._t(user, 'msg.send_alert_price'), expect_input='alert_price', input_hint='Example: crypto BTC 65000')

    async def _alerts_percent_add(self, user: UserContext) -> UIMessage:
        if not has_access(user, 'alerts_advanced'):
            return UIMessage(text=missing_access_message('alerts_advanced', user.language))
        return UIMessage(text=self._t(user, 'msg.send_alert_percent'), expect_input='alert_percent', input_hint='Example: stock TSLA 5')

    async def _alerts_list(self, user: UserContext) -> UIMessage:
        items = await self.alerts.list_alerts(user)
        if not items:
            return UIMessage(text=self._t(user, 'msg.no_active_alerts'))
        lines = [f"{i['asset_type']} {i['symbol']} {i['condition']} {i['target_value']}" for i in items]
        return UIMessage(text=format_section(self._t(user, 'menu.alerts.title'), "\n".join(lines)))

    def _format_asset_row(self, user: UserContext, asset: dict[str, object]) -> str:
        rank = asset.get('rank') or '-'
        symbol = asset.get('symbol') or 'N/A'
        price = self._fmt_price(asset.get('price'))
        change = self._fmt_pct(asset.get('change_24h'))
        cap = self._fmt_cap(asset.get('market_cap'))
        label_24h = self._t(user, 'label.change_24h')
        label_cap = self._t(user, 'label.market_cap')
        return f"{rank}. {symbol} | {price} | {label_24h}: {change} | {label_cap}: {cap}"

    def _format_stock_row(self, user: UserContext, item: dict[str, object]) -> str:
        symbol = item.get('symbol') or 'N/A'
        price = self._fmt_price(item.get('price'))
        change = self._fmt_pct(item.get('change_pct') if item.get('change_pct') is not None else item.get('change'))
        volume = self._fmt_num(item.get('volume'))
        return f"{symbol} | {self._t(user, 'label.price')}: {price} | {self._t(user, 'label.change_24h')}: {change} | {self._t(user, 'label.volume')}: {volume}"

    def _format_forex_row(self, user: UserContext, item: dict[str, object]) -> str:
        pair = item.get('pair') or 'N/A'
        rate = item.get('rate')
        change = item.get('change_pct')
        rate_str = f"{rate:.5f}" if isinstance(rate, (int, float)) else 'N/A'
        change_str = f"{change:+.2f}%" if isinstance(change, (int, float)) else 'N/A'
        return f"{pair} | {self._t(user, 'label.rate')}: {rate_str} | {self._t(user, 'label.change_24h')}: {change_str}"

    def _format_jetton_row(self, user: UserContext, jetton: dict[str, object], index: int) -> str:
        metadata = jetton.get('metadata') or {}
        name = metadata.get('name') or 'N/A'
        symbol = metadata.get('symbol') or ''
        holders = jetton.get('holders_count')
        verification = jetton.get('verification') or 'N/A'
        label_holders = self._t(user, 'label.holders')
        label_ver = self._t(user, 'label.verification')
        sym = f" ({symbol})" if symbol else ''
        holders_text = f"{label_holders}: {holders}" if holders is not None else f"{label_holders}: N/A"
        return f"{index}. {name}{sym} | {holders_text} | {label_ver}: {verification}"

    async def build_ton_usernames(self, user: UserContext, text: str) -> UIMessage:
        query = text.strip()
        if not query:
            return UIMessage(text=self._t(user, 'msg.ton_username_hint'))

        if _looks_like_address(query):
            domains = await self.ton.get_account_domains(query)
            expiring = await self.ton.get_account_expiring_domains(query, 90)
            if not domains:
                return UIMessage(text=self._t(user, 'msg.ton_no_domains'))
            lines = [f"*{self._t(user, 'section.ton_usernames')}*"]
            lines.extend([f"• {d}" for d in domains[:10]])
            if expiring:
                lines.append("")
                lines.append(f"*{self._t(user, 'section.ton_expiring')}*")
                for item in expiring[:5]:
                    name = item.get('name') or 'N/A'
                    expires = self.ton.fmt_date(item.get('expiring_at'))
                    lines.append(f"{name} — {self._t(user, 'label.expires')}: {expires}")
            return UIMessage(text="\n".join(lines))

        domain = _normalize_domain(query)
        record = await self.ton.resolve_domain(domain)
        info = await self.ton.get_domain_info(domain)
        wallet = _extract_wallet_from_record(record)
        expires = self.ton.fmt_date(info.get('expiring_at')) if isinstance(info, dict) else 'N/A'
        if not wallet and not record:
            return UIMessage(text=self._t(user, 'msg.ton_domain_not_found', domain=domain))

        lines = [
            f"*{self._t(user, 'section.ton_usernames')}*",
            f"{self._t(user, 'label.domain')}: {domain}",
            f"{self._t(user, 'label.wallet')}: {wallet or 'N/A'}",
            f"{self._t(user, 'label.expires')}: {expires}",
        ]
        sites = record.get('sites') if isinstance(record, dict) else None
        if sites:
            lines.append(f"{self._t(user, 'label.sites')}: {', '.join(str(s) for s in sites[:3])}")
        return UIMessage(text="\n".join(lines))

    async def build_ton_gifts(self, user: UserContext, text: str) -> UIMessage:
        query = text.strip()
        if not query:
            return UIMessage(text=self._t(user, 'msg.ton_gifts_hint'))
        address = query
        if not _looks_like_address(query):
            domain = _normalize_domain(query)
            record = await self.ton.resolve_domain(domain)
            address = _extract_wallet_from_record(record) or ''
        if not address:
            return UIMessage(text=self._t(user, 'msg.ton_wallet_not_found'))
        items = await self.ton.get_account_nfts(address, limit=50)
        if not items:
            return UIMessage(text=self._t(user, 'msg.ton_gifts_empty'))

        filtered = [i for i in items if _is_gift_nft(i)]
        if not filtered:
            filtered = items[:5]
        lines = [f"*{self._t(user, 'section.ton_gifts')}*"]
        for item in filtered[:10]:
            name = _nft_display_name(item)
            collection = _nft_collection_name(item)
            if collection:
                lines.append(f"• {name} — {collection}")
            else:
                lines.append(f"• {name}")
        return UIMessage(text="\n".join(lines))

    def _fmt_price(self, value: object) -> str:
        if isinstance(value, (int, float)):
            if value >= 1:
                return f"${value:,.2f}"
            return f"${value:,.6f}"
        return 'N/A'

    def _fmt_pct(self, value: object) -> str:
        if isinstance(value, (int, float)):
            return f"{value:+.2f}%"
        return 'N/A'

    def _fmt_cap(self, value: object) -> str:
        if not isinstance(value, (int, float)):
            return 'N/A'
        if value >= 1_000_000_000_000:
            return f"${value/1_000_000_000_000:.2f}T"
        if value >= 1_000_000_000:
            return f"${value/1_000_000_000:.2f}B"
        if value >= 1_000_000:
            return f"${value/1_000_000:.2f}M"
        return f"${value:,.0f}"

    async def _ton_price(self, user: UserContext) -> UIMessage:
        data = await self.ton.get_price()
        return UIMessage(text=format_section(self._t(user, 'menu.ton.title'), format_kv(list(data.items()))))

    async def _ton_nfts(self, user: UserContext) -> UIMessage:
        items = await self.ton.get_nft_collections()
        return UIMessage(text=format_section(self._t(user, 'btn.nfts'), "\n".join(items)))

    async def _ton_wallet(self, user: UserContext) -> UIMessage:
        return UIMessage(text=self._t(user, 'msg.send_ton_wallet'), expect_input='ton_wallet', input_hint='Example: EQB...')

    async def _ton_usernames(self, user: UserContext) -> UIMessage:
        return UIMessage(text=self._t(user, 'msg.ton_username_hint'), expect_input='ton_usernames', input_hint='alice.ton / alice.t.me / EQB...')

    async def _ton_gifts(self, user: UserContext) -> UIMessage:
        return UIMessage(text=self._t(user, 'msg.ton_gifts_hint'), expect_input='ton_gifts', input_hint='alice.ton / EQB...')

    async def _ton_projects(self, user: UserContext, payload: str | None = None) -> UIMessage:
        page = int(payload or '1')
        page = max(1, page)
        limit = 10
        offset = (page - 1) * limit
        jettons = await self.ton.get_jettons(limit=limit, offset=offset)
        items = [self._format_jetton_row(user, j, offset + idx + 1) for idx, j in enumerate(jettons)]
        title = f"{self._t(user, 'section.ton_projects')} ({page})"
        text = format_section(title, "\n".join(items) if items else 'N/A')
        buttons = []
        if page > 1:
            buttons.append([self._btn(user, 'btn.prev', f'page:ton_projects:{page-1}')])
        if jettons:
            buttons.append([self._btn(user, 'btn.next', f'page:ton_projects:{page+1}')])
        buttons.append([self._btn(user, 'btn.back', 'menu:ton')])
        return UIMessage(text=text, buttons=buttons)

    async def _nft_floor(self, user: UserContext) -> UIMessage:
        data = await self.nft.get_floor_prices(['azuki', 'bored-ape-yacht-club'])
        lines = [f"{k}: {v}" for k, v in data.items()]
        return UIMessage(text=format_section(self._t(user, 'btn.floor_prices'), "\n".join(lines)))

    async def _nft_collections(self, user: UserContext) -> UIMessage:
        items = await self.nft.get_top_collections()
        return UIMessage(text=format_section(self._t(user, 'btn.collections'), "\n".join(items)))

    async def _nft_search(self, user: UserContext) -> UIMessage:
        return UIMessage(text=self._t(user, 'msg.send_nft_search'), expect_input='nft_search', input_hint='Example: Pudgy Penguins')

    async def _portfolio_add(self, user: UserContext) -> UIMessage:
        return UIMessage(
            text=self._t(user, 'msg.portfolio_add_choose_type'),
            buttons=[
                [self._btn(user, 'btn.add_stock', 'action:portfolio_add_type:stock'), self._btn(user, 'btn.add_crypto', 'action:portfolio_add_type:crypto')],
                [self._btn(user, 'btn.add_fund', 'action:portfolio_add_type:fund'), self._btn(user, 'btn.add_custom', 'action:portfolio_add_custom')],
                [self._btn(user, 'btn.back', 'menu:portfolio')],
            ],
        )

    async def _portfolio_add_custom(self, user: UserContext) -> UIMessage:
        return UIMessage(
            text=self._t(user, 'msg.send_portfolio_add'),
            expect_input='portfolio_add_full',
            input_hint='TYPE SYMBOL AMOUNT COST',
        )

    async def _portfolio_add_type(self, user: UserContext, payload: str | None) -> UIMessage:
        asset_type = (payload or 'stock').lower()
        return UIMessage(
            text=self._t(user, 'msg.send_portfolio_add_details', asset_type=asset_type),
            expect_input='portfolio_add_details',
            input_hint='AAPL 5 180.50',
        )

    async def _portfolio_remove(self, user: UserContext) -> UIMessage:
        return await self._portfolio_remove_menu(user, '1')

    async def _portfolio_remove_menu(self, user: UserContext, payload: str | None) -> UIMessage:
        items = await self.portfolio.list_assets(user)
        if not items:
            return UIMessage(text=self._t(user, 'msg.no_holdings'))

        counts: dict[str, int] = {}
        order: list[str] = []
        for item in items:
            symbol = str(item.get('symbol') or '').upper()
            if not symbol:
                continue
            counts[symbol] = counts.get(symbol, 0) + 1
            if symbol not in order:
                order.append(symbol)

        page = int(payload or '1')
        page_items, page, total = paginate(order, page, per_page=8)
        buttons: list[list[ButtonSpec]] = []
        row: list[ButtonSpec] = []
        for symbol in page_items:
            label = f"❌ {symbol} ({counts.get(symbol, 0)})"
            row.append(ButtonSpec(label, f"action:portfolio_remove_symbol:{symbol}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        nav_row: list[ButtonSpec] = []
        if page > 1:
            nav_row.append(self._btn(user, 'btn.prev', f'action:portfolio_remove:{page-1}'))
        if page < total:
            nav_row.append(self._btn(user, 'btn.next', f'action:portfolio_remove:{page+1}'))
        if nav_row:
            buttons.append(nav_row)
        buttons.append([self._btn(user, 'btn.back', 'menu:portfolio')])

        text = format_section(
            self._t(user, 'btn.remove_asset'),
            self._t(user, 'msg.choose_remove', count=str(len(order))),
        )
        return UIMessage(text=text, buttons=buttons)

    async def _portfolio_remove_symbol(self, user: UserContext, payload: str | None) -> UIMessage:
        symbol = (payload or '').upper().strip()
        if not symbol:
            return await self._portfolio_remove_menu(user, '1')
        removed = await self.portfolio.remove_asset(user, symbol)
        menu = await self._portfolio_remove_menu(user, '1')
        prefix = self._t(user, 'msg.asset_removed', count=str(removed))
        menu.text = f"{prefix}\n\n{menu.text}"
        return menu

    async def _portfolio_list(self, user: UserContext) -> UIMessage:
        items = await self.portfolio.list_assets(user)
        if not items:
            return UIMessage(text=self._t(user, 'msg.no_holdings'))
        lines = [f"*{self._t(user, 'section.holdings')}*"]
        for item in items[:25]:
            asset_type = item.get('asset_type', 'N/A')
            symbol = item.get('symbol', 'N/A')
            amount = item.get('amount', 'N/A')
            cost = item.get('cost_basis', 'N/A')
            lines.append(
                f"{symbol} | {self._t(user, 'label.asset_type')}: {asset_type} | "
                f"{self._t(user, 'label.amount')}: {amount} | {self._t(user, 'label.cost_basis')}: {cost}"
            )
        return UIMessage(text="\n".join(lines))

    async def _portfolio_pnl(self, user: UserContext) -> UIMessage:
        if not has_access(user, 'portfolio_pnl'):
            return UIMessage(text=missing_access_message('portfolio_pnl', user.language))
        data = await self.portfolio.get_pnl(user)
        return UIMessage(text=format_section(self._t(user, 'btn.pnl'), format_kv(list(data.items()))))

    async def _portfolio_allocation(self, user: UserContext) -> UIMessage:
        data = await self.portfolio.get_allocation(user)
        return UIMessage(text=format_section(self._t(user, 'btn.allocation'), format_kv(list(data.items()))))

    async def _portfolio_link_exchange(self, user: UserContext) -> UIMessage:
        return UIMessage(text=self._t(user, 'msg.sync_exchange_hint'), expect_input='portfolio_link_exchange', input_hint='binance KEY SECRET')

    async def _portfolio_link_wallet(self, user: UserContext) -> UIMessage:
        return UIMessage(text=self._t(user, 'msg.sync_wallet_hint'), expect_input='portfolio_link_wallet', input_hint='ton EQB... MyWallet')

    async def _portfolio_import_csv(self, user: UserContext) -> UIMessage:
        return UIMessage(text=self._t(user, 'msg.import_csv_hint'), expect_input='portfolio_import_csv', input_hint='asset_type,symbol,amount,cost_basis')

    async def _portfolio_export_csv(self, user: UserContext) -> UIMessage:
        csv_text = await self.portfolio.export_csv(user)
        text = f"{self._t(user, 'msg.export_csv')}\n```\n{csv_text.strip()}\n```"
        return UIMessage(text=text)

    async def _portfolio_links(self, user: UserContext) -> UIMessage:
        links = await self.links.list_links(user)
        if not links:
            return UIMessage(text=self._t(user, 'msg.sync_no_links'))
        lines = [f"*{self._t(user, 'section.sync_links')}*"]
        buttons: list[list[ButtonSpec]] = []
        for link in links[:10]:
            link_id = link.get('id')
            label = link.get('label')
            kind = link.get('kind')
            provider = link.get('provider')
            lines.append(f"• #{link_id} {label} ({kind}:{provider})")
            buttons.append([ButtonSpec(f"❌ #{link_id} {label}", f"action:portfolio_link_remove:{link_id}")])
        buttons.append([self._btn(user, 'btn.back', 'menu:portfolio_sync')])
        return UIMessage(text="\n".join(lines), buttons=buttons)

    async def _portfolio_link_remove(self, user: UserContext, payload: str | None) -> UIMessage:
        try:
            link_id = int(payload or '0')
        except Exception:
            link_id = 0
        if link_id:
            await self.links.remove_link(user, link_id)
        message = await self._portfolio_links(user)
        message.text = f"{self._t(user, 'msg.sync_removed')}\n\n{message.text}"
        return message

    async def _portfolio_sync_run(self, user: UserContext) -> UIMessage:
        links = await self.links.list_links(user)
        if not links:
            return UIMessage(text=self._t(user, 'msg.sync_no_links'))
        total_assets = 0
        synced_wallets = 0
        synced_exchanges = 0
        for link in links:
            kind = str(link.get('kind'))
            provider = str(link.get('provider'))
            data = link.get('data') or {}
            link_id = link.get('id')
            if kind == 'wallet' and provider == 'ton':
                address = str(data.get('address') or '')
                if not address:
                    continue
                items = await self._sync_ton_wallet(address)
                source = f"wallet:ton:{link_id}"
                total_assets += await self.portfolio.replace_assets(user, items, source)
                synced_wallets += 1
            if kind == 'exchange':
                api_key = str(data.get('api_key') or '')
                api_secret = str(data.get('api_secret') or '')
                passphrase = data.get('passphrase')
                if not api_key or not api_secret:
                    continue
                try:
                    balances = await self.exchanges.fetch_balances(provider, api_key, api_secret, passphrase)
                except RuntimeError:
                    return UIMessage(text=self._t(user, 'msg.sync_exchange_missing'))
                except ValueError:
                    return UIMessage(text=self._t(user, 'msg.sync_exchange_unknown', provider=provider))
                except Exception:
                    return UIMessage(text=self._t(user, 'msg.sync_exchange_failed'))
                items = [{'asset_type': 'crypto', 'symbol': b['symbol'], 'amount': b['amount'], 'cost_basis': 0} for b in balances]
                source = f"exchange:{provider}:{link_id}"
                total_assets += await self.portfolio.replace_assets(user, items, source)
                synced_exchanges += 1

        return UIMessage(text=self._t(
            user,
            'msg.sync_done',
            wallets=str(synced_wallets),
            exchanges=str(synced_exchanges),
            assets=str(total_assets),
        ))

    async def _sync_ton_wallet(self, address: str) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        try:
            wallet = await self.ton.lookup_wallet(address)
            balance_text = wallet.get('Balance') if isinstance(wallet, dict) else None
            balance_value = None
            if isinstance(balance_text, str) and 'TON' in balance_text:
                try:
                    balance_value = float(balance_text.split()[0])
                except Exception:
                    balance_value = None
            if balance_value and balance_value > 0:
                items.append({'asset_type': 'ton', 'symbol': 'TON', 'amount': balance_value, 'cost_basis': 0})
        except Exception:
            pass
        try:
            jettons = await self.ton.get_wallet_jettons(address)
            for j in jettons:
                symbol = j.get('symbol') or j.get('name') or 'JETTON'
                amount = j.get('amount')
                if amount and amount > 0:
                    items.append({'asset_type': 'jetton', 'symbol': str(symbol).upper(), 'amount': amount, 'cost_basis': 0})
        except Exception:
            pass
        return items

    async def link_exchange_from_input(self, user: UserContext, text: str) -> UIMessage:
        parts = text.strip().split()
        if len(parts) < 3:
            return UIMessage(text=self._t(user, 'msg.sync_exchange_hint'))
        provider = parts[0].lower()
        api_key = parts[1]
        api_secret = parts[2]
        passphrase = parts[3] if len(parts) > 3 else None
        if provider not in ('binance', 'bybit', 'okx'):
            return UIMessage(text=self._t(user, 'msg.sync_exchange_unknown', provider=provider))
        label = f"{provider.upper()} #{user.user_id}"
        link_id = await self.links.add_link(
            user,
            kind='exchange',
            provider=provider,
            label=label,
            data={'api_key': api_key, 'api_secret': api_secret, 'passphrase': passphrase},
        )
        return UIMessage(text=self._t(user, 'msg.sync_exchange_added', label=f"{provider.upper()} ({link_id})"))

    async def link_wallet_from_input(self, user: UserContext, text: str) -> UIMessage:
        parts = text.strip().split()
        if len(parts) < 2:
            return UIMessage(text=self._t(user, 'msg.sync_wallet_hint'))
        provider = parts[0].lower()
        address = parts[1]
        label = " ".join(parts[2:]) if len(parts) > 2 else address[:8]
        if provider != 'ton':
            return UIMessage(text=self._t(user, 'msg.sync_wallet_unknown', provider=provider))
        link_id = await self.links.add_link(
            user,
            kind='wallet',
            provider='ton',
            label=label,
            data={'address': address},
        )
        return UIMessage(text=self._t(user, 'msg.sync_wallet_added', label=f"TON ({link_id})"))

    async def import_csv_from_text(self, user: UserContext, text: str) -> UIMessage:
        count = await self.portfolio.import_csv(user, text, replace=True, source='csv')
        if not count:
            return UIMessage(text=self._t(user, 'msg.invalid_csv'))
        return UIMessage(text=self._t(user, 'msg.import_csv_done', count=str(count)))

    async def _education_lessons(self, user: UserContext, payload: str | None = None) -> UIMessage:
        page = int(payload or '1')
        lessons = await self.education.get_lessons(user.language)
        page_items, page, total = paginate(lessons, page)
        text = format_section(self._t(user, 'btn.mini_lessons'), "\n".join(page_items))
        buttons = []
        if page > 1:
            buttons.append([self._btn(user, 'btn.prev', f'page:education_lessons:{page-1}')])
        if page < total:
            buttons.append([self._btn(user, 'btn.next', f'page:education_lessons:{page+1}')])
        buttons.append([self._btn(user, 'btn.back', 'menu:education')])
        return UIMessage(text=text, buttons=buttons)

    async def _education_glossary(self, user: UserContext) -> UIMessage:
        items = await self.education.get_glossary(user.language)
        return UIMessage(text=format_section(self._t(user, 'btn.glossary'), "\n".join(items)))

    async def _education_quiz(self, user: UserContext) -> UIMessage:
        if not has_access(user, 'education_quiz'):
            return UIMessage(text=missing_access_message('education_quiz', user.language))
        item = await self.education.get_quiz()
        return UIMessage(text=format_section(self._t(user, 'btn.quizzes'), item))

    async def _news_headlines(self, user: UserContext, payload: str | None = None) -> UIMessage:
        page, mode = self._parse_page_mode(payload)
        items = await self.news.get_headlines()
        page_items, page, total = paginate(items, page)
        text = await self._format_news_page(user, page_items, mode, self._t(user, 'btn.headlines'))
        buttons = []
        buttons.extend(self._news_toggle_buttons(user, page, mode, 'news_headlines'))
        if page > 1:
            buttons.append([self._btn(user, 'btn.prev', f'page:news_headlines:{page-1}:{mode}')])
        if page < total:
            buttons.append([self._btn(user, 'btn.next', f'page:news_headlines:{page+1}:{mode}')])
        buttons.append([self._btn(user, 'btn.back', 'menu:news')])
        return UIMessage(text=text, buttons=buttons, parse_mode='HTML')

    async def _news_project(self, user: UserContext, payload: str | None = None) -> UIMessage:
        if not has_access(user, 'news_project'):
            return UIMessage(text=missing_access_message('news_project', user.language))
        page, mode = self._parse_page_mode(payload)
        items = await self.news.get_project_news('ton')
        page_items, page, total = paginate(items, page)
        text = await self._format_news_page(user, page_items, mode, self._t(user, 'btn.project_news'))
        buttons = []
        buttons.extend(self._news_toggle_buttons(user, page, mode, 'news_project'))
        if page > 1:
            buttons.append([self._btn(user, 'btn.prev', f'page:news_project:{page-1}:{mode}')])
        if page < total:
            buttons.append([self._btn(user, 'btn.next', f'page:news_project:{page+1}:{mode}')])
        buttons.append([self._btn(user, 'btn.back', 'menu:news')])
        return UIMessage(text=text, buttons=buttons, parse_mode='HTML')

    def _parse_page_mode(self, payload: str | None) -> tuple[int, str]:
        if not payload:
            return 1, 'orig'
        raw = str(payload)
        parts = raw.split(':', 1)
        try:
            page = int(parts[0])
        except ValueError:
            page = 1
        mode = parts[1] if len(parts) > 1 else 'orig'
        if mode not in ('orig', 'tr'):
            mode = 'orig'
        return page, mode

    def _news_toggle_buttons(self, user: UserContext, page: int, mode: str, action_key: str) -> list[list[ButtonSpec]]:
        buttons: list[list[ButtonSpec]] = []
        row: list[ButtonSpec] = []
        if mode != 'tr':
            row.append(self._btn(user, 'btn.translate', f'page:{action_key}:{page}:tr'))
        if mode != 'orig':
            row.append(self._btn(user, 'btn.original', f'page:{action_key}:{page}:orig'))
        if row:
            buttons.append(row)
        return buttons

    async def _format_news_page(self, user: UserContext, items: list[dict[str, object]], mode: str, title: str) -> str:
        if not items:
            return f"<b>{escape(title)}</b>\n{escape(self._t(user, 'msg.news_empty'))}"

        translated = mode == 'tr'
        titles = [str(i.get('title') or '') for i in items]
        summaries = [str(i.get('summary') or '') for i in items]
        if translated:
            target_lang = 'ru' if user.language == 'ru' else 'en'
            if not self.translator.is_configured():
                return f"<b>{escape(title)}</b>\n{escape(self._t(user, 'msg.translate_unavailable'))}"
            if not await self.translator.is_available(target_lang):
                return f"<b>{escape(title)}</b>\n{escape(self._t(user, 'msg.translate_offline'))}"
            titles, ok1 = await self.translator.try_translate_texts(titles, target_lang, None)
            summaries, ok2 = await self.translator.try_translate_texts(summaries, target_lang, None)
            if not (ok1 and ok2):
                return f"<b>{escape(title)}</b>\n{escape(self._t(user, 'msg.translate_failed'))}"

        lines = [f"<b>{escape(title)}</b>"]
        for idx, item in enumerate(items, start=1):
            raw_url = str(item.get('url') or '')
            url = escape(raw_url, quote=True)
            title_text = escape(titles[idx - 1] or str(item.get('title') or 'N/A'))
            summary_text = escape(self._truncate(summaries[idx - 1] or str(item.get('summary') or ''), 220))
            source = escape(str(item.get('source') or 'N/A'))
            date_label = self._format_news_date(item.get('datetime'))
            if url:
                headline = f"<a href=\"{url}\">{title_text}</a>"
            else:
                headline = title_text
            meta = f"{source}"
            if date_label:
                meta = f"{meta} · {date_label}"
            lines.append(f"\n<b>{idx}.</b> {headline}\n<i>{meta}</i>")
            if summary_text:
                lines.append(f"{summary_text}")
        return "\n".join(lines)

    def _truncate(self, text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + '…'

    def _format_news_date(self, value: object) -> str:
        if isinstance(value, (int, float)):
            try:
                return datetime.utcfromtimestamp(value).strftime('%Y-%m-%d')
            except Exception:
                return ''
        if isinstance(value, str) and value:
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            except Exception:
                return ''
        return ''

    async def _subscription_status(self, user: UserContext) -> UIMessage:
        status = await self.payments.get_subscription_status(user)
        return UIMessage(text=format_section(self._t(user, 'btn.subscription'), status))

    async def _subscription_manage(self, user: UserContext) -> UIMessage:
        link = await self.payments.get_manage_link(user)
        return UIMessage(text=self._t(user, 'msg.subscription_manage', link=link))

    async def _subscription_upgrade(self, user: UserContext, tier: str) -> UIMessage:
        link = await self.payments.create_checkout_link(user, tier)
        return UIMessage(text=self._t(user, 'msg.subscription_upgrade', tier=tier.upper(), link=link))

    async def _set_language(self, user: UserContext, language: str) -> UIMessage:
        await self.users.update_language(user.user_id, language)
        user.language = language
        label = self._t(user, 'btn.lang_ru') if language == 'ru' else self._t(user, 'btn.lang_en')
        return UIMessage(text=self._t(user, 'msg.language_set', language=label))

    async def _admin_broadcast(self, user: UserContext) -> UIMessage:
        if not is_admin_allowed(user):
            return UIMessage(text=self._t(user, 'msg.admin_required'))
        return UIMessage(text=self._t(user, 'btn.broadcast'), expect_input='admin_broadcast', input_hint='Type your message')

    async def _admin_stats(self, user: UserContext) -> UIMessage:
        if not is_admin_allowed(user):
            return UIMessage(text=self._t(user, 'msg.admin_required'))
        stats = await self.users.get_user_stats()
        return UIMessage(text=format_section(self._t(user, 'btn.user_stats'), format_kv(list(stats.items()))))

    async def _admin_toggle(self, user: UserContext) -> UIMessage:
        if not is_admin_allowed(user):
            return UIMessage(text=self._t(user, 'msg.admin_required'))
        return UIMessage(text=self._t(user, 'btn.feature_toggle'), expect_input='admin_toggle', input_hint='Example: education_quiz')

    async def _admin_verify(self, user: UserContext) -> UIMessage:
        if not is_admin_allowed(user):
            return UIMessage(text=self._t(user, 'msg.admin_required'))
        return UIMessage(text=self._t(user, 'msg.verify_hint'), expect_input='admin_verify', input_hint='123456789 major')


ACTION_BACK_MENU = {
    'stocks_price': 'stocks',
    'stocks_fundamentals': 'stocks',
    'stocks_fundamentals_input': 'stocks',
    'stocks_fundamentals_portfolio': 'stocks',
    'stocks_fundamentals_symbol': 'stocks',
    'stocks_ratios': 'stocks',
    'stocks_ratios_input': 'stocks',
    'stocks_ratios_portfolio': 'stocks',
    'stocks_ratios_symbol': 'stocks',
    'stocks_earnings': 'stocks',
    'stocks_earnings_input': 'stocks',
    'stocks_earnings_portfolio': 'stocks',
    'stocks_earnings_symbol': 'stocks',
    'stocks_dividends': 'stocks',
    'stocks_dividends_input': 'stocks',
    'stocks_dividends_portfolio': 'stocks',
    'stocks_dividends_symbol': 'stocks',
    'stocks_find': 'stocks',
    'stocks_find_input': 'stocks',
    'stocks_profile': 'stocks',
    'stocks_top': 'stocks',
    'stocks_valuation': 'stocks',
    'etfs': 'etfs',
    'etf_top': 'etfs',
    'etf_profile': 'etfs',
    'forex_rates': 'forex',
    'forex_top': 'forex',
    'forex_find_input': 'forex',
    'forex_profile': 'forex',
    'crypto_prices': 'crypto',
    'crypto_dominance': 'crypto',
    'crypto_onchain': 'crypto',
    'crypto_top': 'crypto',
    'crypto_find': 'crypto',
    'crypto_profile': 'crypto',
    'alerts_crypto': 'crypto',
    'ton_price': 'ton',
    'ton_nfts': 'ton',
    'ton_wallet': 'ton',
    'ton_usernames': 'ton',
    'ton_gifts': 'ton',
    'ton_projects': 'ton',
    'nft_floor': 'nft',
    'nft_collections': 'nft',
    'nft_search': 'nft',
    'portfolio_add': 'portfolio',
    'portfolio_add_type': 'portfolio',
    'portfolio_add_custom': 'portfolio',
    'portfolio_remove': 'portfolio',
    'portfolio_remove_symbol': 'portfolio',
    'portfolio_list': 'portfolio',
    'portfolio_pnl': 'portfolio',
    'portfolio_allocation': 'portfolio',
    'portfolio_link_exchange': 'portfolio_sync',
    'portfolio_link_wallet': 'portfolio_sync',
    'portfolio_sync_run': 'portfolio_sync',
    'portfolio_links': 'portfolio_sync',
    'portfolio_link_remove': 'portfolio_sync',
    'portfolio_import_csv': 'portfolio_sync',
    'portfolio_export_csv': 'portfolio_sync',
    'alerts_price_add': 'alerts',
    'alerts_percent_add': 'alerts',
    'alerts_list': 'alerts',
    'education_lessons': 'education',
    'education_glossary': 'education',
    'education_quiz': 'education',
    'news_headlines': 'news',
    'news_project': 'news',
    'subscription_status': 'settings',
    'subscription_manage': 'settings',
    'subscription_upgrade_pro': 'settings',
    'subscription_upgrade_elite': 'settings',
    'admin_broadcast': 'admin',
    'admin_stats': 'admin',
    'admin_toggle': 'admin',
    'admin_verify': 'admin',
    'language_set_ru': 'language',
    'language_set_en': 'language',
}


def _num(value: object) -> float | None:
    try:
        if value is None:
            return None
        if isinstance(value, str):
            value = value.replace(',', '').strip()
        return float(value)
    except Exception:
        return None


def _calc_graham_value(eps: float | None, growth: float | None) -> tuple[float | None, str]:
    if eps is None:
        return None, 'N/A'
    g = growth or 0.0
    if g > 1:
        g = g / 100.0
    g_percent = max(0.0, min(0.20, g)) * 100.0
    intrinsic = eps * (8.5 + 2 * g_percent)
    note = f"{g_percent:.1f}%"
    return intrinsic, note


def _calc_margin_of_safety(intrinsic: float | None, price: float | None) -> float | None:
    if intrinsic is None or price in (None, 0):
        return None
    return (intrinsic - price) / price * 100.0


def _looks_like_address(value: str) -> bool:
    v = value.strip()
    return v.startswith('0:') or v.startswith('EQ') or len(v) > 40


def _normalize_domain(value: str) -> str:
    v = value.strip().lstrip('@')
    if '.' not in v:
        return f"{v}.ton"
    return v


def _extract_wallet_from_record(record: dict[str, object]) -> str | None:
    wallet = record.get('wallet') if isinstance(record, dict) else None
    if isinstance(wallet, dict):
        return wallet.get('address') or (wallet.get('account') or {}).get('address')
    return None


def _nft_display_name(item: dict[str, object]) -> str:
    meta = item.get('metadata') or {}
    return str(meta.get('name') or item.get('dns') or item.get('address') or 'NFT')


def _nft_collection_name(item: dict[str, object]) -> str:
    collection = item.get('collection') or {}
    return str(collection.get('name') or '')


def _is_gift_nft(item: dict[str, object]) -> bool:
    meta = item.get('metadata') or {}
    name = str(meta.get('name') or '').lower()
    desc = str(meta.get('description') or '').lower()
    collection = str((item.get('collection') or {}).get('name') or '').lower()
    keywords = ('gift', 'present', 'telegram', 'gifts', 'подар', 'сувенир')
    hay = ' '.join([name, desc, collection])
    return any(k in hay for k in keywords)


def _parse_sort_page(payload: str | None, default_sort: str) -> tuple[str, int]:
    if not payload:
        return default_sort, 1
    parts = str(payload).split(':')
    sort = parts[0] or default_sort
    try:
        page = int(parts[1]) if len(parts) > 1 else 1
    except Exception:
        page = 1
    return sort, max(1, page)


def _sort_quotes(items: list[dict[str, object]], sort: str) -> list[dict[str, object]]:
    if sort == 'losers':
        return sorted(items, key=lambda x: (x.get('change_pct') or 0))
    if sort == 'volume':
        return sorted(items, key=lambda x: -(x.get('volume') or 0))
    if sort == 'popular':
        return items
    return sorted(items, key=lambda x: -(x.get('change_pct') or 0))


def _sort_buttons(user: UserContext, action: str, sort: str, page: int, include_volume: bool = True) -> list[list[ButtonSpec]]:
    buttons: list[list[ButtonSpec]] = []
    row: list[ButtonSpec] = []
    if sort != 'gainers':
        row.append(ButtonSpec(t('btn.top_gainers', user.language), f"action:{action}:gainers:{page}"))
    if sort != 'losers':
        row.append(ButtonSpec(t('btn.top_losers', user.language), f"action:{action}:losers:{page}"))
    if include_volume and sort != 'volume':
        row.append(ButtonSpec(t('btn.top_volume', user.language), f"action:{action}:volume:{page}"))
    if row:
        buttons.append(row)
    return buttons


def _page_buttons(user: UserContext, action: str, sort: str, page: int, total: int) -> list[list[ButtonSpec]]:
    buttons: list[list[ButtonSpec]] = []
    row: list[ButtonSpec] = []
    if page > 1:
        row.append(ButtonSpec(t('btn.prev', user.language), f"action:{action}:{sort}:{page-1}"))
    if page < total:
        row.append(ButtonSpec(t('btn.next', user.language), f"action:{action}:{sort}:{page+1}"))
    if row:
        buttons.append(row)
    return buttons
