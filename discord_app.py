from __future__ import annotations

import asyncio

import discord
from discord import app_commands

from config import load_config
from database import init_db
from core.router import Router
from core.ui import UIMessage
from core.permissions import UserContext, has_access, missing_access_message
from core.i18n import t
from core.ratelimit import RateLimiter
from services.stocks_service import StocksService
from services.crypto_service import CryptoService
from services.ton_service import TonService
from services.nft_service import NftService
from services.forex_service import ForexService
from services.news_service import NewsService
from services.education_service import EducationService
from services.portfolio_service import PortfolioService
from services.alert_service import AlertService
from services.user_service import UserService
from services.payment_service import PaymentService
from services.translation_service import TranslationService
from services.link_service import LinkService
from services.exchange_service import ExchangeService

rate_limiter = RateLimiter()


def _build_router() -> Router:
    return Router(
        stocks=StocksService(),
        crypto=CryptoService(),
        ton=TonService(),
        nft=NftService(),
        forex=ForexService(),
        news=NewsService(),
        education=EducationService(),
        portfolio=PortfolioService(),
        alerts=AlertService(),
        users=UserService(),
        payments=PaymentService(),
        links=LinkService(),
        exchanges=ExchangeService(),
        webapp_url=load_config().telegram_webapp_url,
        discord_url=load_config().discord_server_url,
        translator=TranslationService(),
    )


class MenuView(discord.ui.View):
    def __init__(self, message: UIMessage, router: Router, user: UserContext):
        super().__init__(timeout=180)
        self.router = router
        self.user = user
        if message.buttons:
            for row in message.buttons:
                for btn in row:
                    if btn.action.startswith('webapp:'):
                        url = btn.action.replace('webapp:', '')
                        self.add_item(discord.ui.Button(label=btn.label, url=url))
                    elif btn.action.startswith('url:'):
                        url = btn.action.replace('url:', '')
                        self.add_item(discord.ui.Button(label=btn.label, url=url))
                    else:
                        self.add_item(MenuButton(label=btn.label, action=btn.action))


def _button_style(label: str, action: str) -> discord.ButtonStyle:
    l = label.lower()
    if 'back' in l or 'назад' in l:
        return discord.ButtonStyle.secondary
    if 'remove' in l or 'toggle' in l or 'удал' in l:
        return discord.ButtonStyle.danger
    if 'upgrade' in l or 'add' in l or 'start' in l or 'апгрейд' in l or 'добав' in l:
        return discord.ButtonStyle.success
    if action.startswith('menu:settings') or action.startswith('menu:admin'):
        return discord.ButtonStyle.secondary
    return discord.ButtonStyle.primary


class MenuButton(discord.ui.Button):
    def __init__(self, label: str, action: str):
        super().__init__(label=label, style=_button_style(label, action))
        self.action = action

    async def callback(self, interaction: discord.Interaction) -> None:
        bot: InvestmentBot = interaction.client  # type: ignore
        user = bot.user_cache.get(str(interaction.user.id))
        if not await rate_limiter.allow(f"dc:{interaction.user.id}"):
            lang = user.language if user else 'ru'
            await interaction.response.send_message(t('msg.rate_limited', lang), ephemeral=True)
            return
        if not user:
            user = await bot.router.users.get_or_create_user('discord', str(interaction.user.id), interaction.user.name, interaction.user.id in bot.admin_ids, None)
            bot.user_cache[str(interaction.user.id)] = user
        if self.action == 'action:alerts_percent_add' and not has_access(user, 'alerts_advanced'):
            await interaction.response.send_message(missing_access_message('alerts_advanced', user.language), ephemeral=True)
            return
        if self.action in MODAL_ACTIONS:
            await interaction.response.send_modal(MODAL_ACTIONS[self.action](bot, user))
            return
        await bot.render_action(interaction, self.action, user)


class InvestmentBot(discord.Client):
    def __init__(self, router: Router, admin_ids: set[int], **kwargs):
        super().__init__(**kwargs)
        self.tree = app_commands.CommandTree(self)
        self.router = router
        self.admin_ids = admin_ids
        self.user_cache: dict[str, UserContext] = {}

    async def setup_hook(self) -> None:
        await self.tree.sync()

    async def on_ready(self) -> None:
        print(f"Discord bot logged in as {self.user}")

    async def render_message(self, interaction: discord.Interaction, message: UIMessage, user: UserContext) -> None:
        view = MenuView(message, self.router, user)
        if interaction.response.is_done():
            await interaction.followup.send(message.text, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(message.text, view=view, ephemeral=True)

    async def render_action(self, interaction: discord.Interaction, action: str, user: UserContext) -> None:
        if action.startswith('menu:'):
            menu_id = action.split(':', 1)[1]
            message = self.router.menu(menu_id, user)
            await self.render_message(interaction, message, user)
            return
        if action.startswith('action:'):
            act_payload = action.split(':', 1)[1]
            if ':' in act_payload:
                act, payload = act_payload.split(':', 1)
            else:
                act, payload = act_payload, None
            message = await self.router.handle_action(act, user, payload)
            await self.render_message(interaction, message, user)
            return
        if action.startswith('page:'):
            _, key, page = action.split(':', 2)
            message = await self.router.handle_action(key, user, page)
            await self.render_message(interaction, message, user)


class AddAssetModal(discord.ui.Modal, title='Add Asset'):
    asset_type = discord.ui.TextInput(label='Type (stock/crypto/forex/nft)', max_length=10)
    symbol = discord.ui.TextInput(label='Symbol', max_length=15)
    amount = discord.ui.TextInput(label='Amount', max_length=20)
    cost = discord.ui.TextInput(label='Cost Basis', max_length=20)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            await self.bot.router.portfolio.add_asset(
                self.user,
                self.asset_type.value.lower(),
                self.symbol.value.upper(),
                float(self.amount.value),
                float(self.cost.value),
            )
            await interaction.response.send_message(t('msg.asset_added', self.user.language), ephemeral=True)
        except Exception:
            await interaction.response.send_message(t('msg.asset_invalid', self.user.language), ephemeral=True)


class RemoveAssetModal(discord.ui.Modal, title='Remove Asset'):
    symbol = discord.ui.TextInput(label='Symbol', max_length=15)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        removed = await self.bot.router.portfolio.remove_asset(self.user, self.symbol.value.upper())
        await interaction.response.send_message(t('msg.asset_removed', self.user.language, count=removed), ephemeral=True)


class TonWalletModal(discord.ui.Modal, title='TON Wallet'):
    address = discord.ui.TextInput(label='Wallet Address', max_length=80)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        data = await self.bot.router.ton.lookup_wallet(self.address.value)
        lines = '\n'.join([f"**{k}:** {v}" for k, v in data.items()])
        await interaction.response.send_message(lines, ephemeral=True)


class TonUsernamesModal(discord.ui.Modal, title='TON Usernames'):
    query = discord.ui.TextInput(label='Username or Wallet', max_length=80)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        message = await self.bot.router.build_ton_usernames(self.user, self.query.value)
        await interaction.response.send_message(message.text, ephemeral=True)


class TonGiftsModal(discord.ui.Modal, title='TON NFT Gifts'):
    query = discord.ui.TextInput(label='Username or Wallet', max_length=80)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        message = await self.bot.router.build_ton_gifts(self.user, self.query.value)
        await interaction.response.send_message(message.text, ephemeral=True)


class NftSearchModal(discord.ui.Modal, title='NFT Search'):
    query = discord.ui.TextInput(label='Collection Name', max_length=60)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        items = await self.bot.router.nft.search_collection(self.query.value)
        await interaction.response.send_message('\n'.join(items), ephemeral=True)


class AdminBroadcastModal(discord.ui.Modal, title='Admin Broadcast'):
    message = discord.ui.TextInput(label='Message', max_length=500, style=discord.TextStyle.long)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(t('msg.broadcast_queued', self.user.language), ephemeral=True)


class AdminToggleModal(discord.ui.Modal, title='Feature Toggle'):
    feature = discord.ui.TextInput(label='Feature Key', max_length=60)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(t('msg.feature_toggled', self.user.language, feature=self.feature.value), ephemeral=True)


class CryptoFindModal(discord.ui.Modal, title='Find Crypto'):
    symbol = discord.ui.TextInput(label='Ticker (BTC, ETH, SOL)', max_length=15)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        sym = self.symbol.value.upper()
        quote = await self.bot.router.crypto.get_asset(sym)
        if not quote or all(quote.get(k) is None for k in ('price', 'change_24h', 'market_cap')):
            await interaction.response.send_message(t('msg.crypto_not_found', self.user.language), ephemeral=True)
            return
        price = _fmt_price(quote.get('price'))
        change = _fmt_pct(quote.get('change_24h'))
        cap = _fmt_cap(quote.get('market_cap'))
        await interaction.response.send_message(
            f"**{sym}**\n"
            f"{t('label.price', self.user.language)}: {price}\n"
            f"{t('label.change_24h', self.user.language)}: {change}\n"
            f"{t('label.market_cap', self.user.language)}: {cap}",
            ephemeral=True,
        )


class StockFindModal(discord.ui.Modal, title='Find Stock'):
    symbol = discord.ui.TextInput(label='Ticker (AAPL, TSLA, NVDA)', max_length=15)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        message = await self.bot.router.build_stock_profile(self.user, self.symbol.value.upper())
        await interaction.response.send_message(message.text, ephemeral=True)


class StockFundamentalsModal(discord.ui.Modal, title='Stock Fundamentals'):
    symbol = discord.ui.TextInput(label='Ticker (AAPL, TSLA, SPY)', max_length=15)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        message = await self.bot.router.build_stock_fundamentals(self.user, self.symbol.value.upper())
        await interaction.response.send_message(message.text, ephemeral=True)


class StockRatiosModal(discord.ui.Modal, title='Stock Ratios'):
    symbol = discord.ui.TextInput(label='Ticker (AAPL, TSLA, SPY)', max_length=15)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        message = await self.bot.router.build_stock_ratios(self.user, self.symbol.value.upper())
        await interaction.response.send_message(message.text, ephemeral=True)


class StockDividendsModal(discord.ui.Modal, title='Stock Dividends'):
    symbol = discord.ui.TextInput(label='Ticker (AAPL, TSLA, SPY)', max_length=15)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        message = await self.bot.router.build_stock_dividends(self.user, self.symbol.value.upper())
        await interaction.response.send_message(message.text, ephemeral=True)


class ForexFindModal(discord.ui.Modal, title='Find Forex Pair'):
    pair = discord.ui.TextInput(label='Pair (EUR/USD)', max_length=12)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        message = await self.bot.router.build_forex_profile(self.user, self.pair.value.upper())
        await interaction.response.send_message(message.text, ephemeral=True)


class ExchangeLinkModal(discord.ui.Modal, title='Connect Exchange'):
    provider = discord.ui.TextInput(label='Provider (binance/bybit/okx)', max_length=12)
    api_key = discord.ui.TextInput(label='API Key', max_length=120)
    api_secret = discord.ui.TextInput(label='API Secret', max_length=120)
    passphrase = discord.ui.TextInput(label='Passphrase (optional)', max_length=120, required=False)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        parts = [self.provider.value.strip(), self.api_key.value.strip(), self.api_secret.value.strip()]
        if self.passphrase.value:
            parts.append(self.passphrase.value.strip())
        message = await self.bot.router.link_exchange_from_input(self.user, " ".join(parts))
        await interaction.response.send_message(message.text, ephemeral=True)


class WalletLinkModal(discord.ui.Modal, title='Connect Wallet'):
    provider = discord.ui.TextInput(label='Provider (ton)', max_length=12)
    address = discord.ui.TextInput(label='Wallet address', max_length=120)
    label = discord.ui.TextInput(label='Label (optional)', max_length=50, required=False)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        parts = [self.provider.value.strip(), self.address.value.strip()]
        if self.label.value:
            parts.append(self.label.value.strip())
        message = await self.bot.router.link_wallet_from_input(self.user, " ".join(parts))
        await interaction.response.send_message(message.text, ephemeral=True)


class CsvImportModal(discord.ui.Modal, title='Import CSV'):
    csv_text = discord.ui.TextInput(label='CSV', style=discord.TextStyle.long)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        message = await self.bot.router.import_csv_from_text(self.user, self.csv_text.value)
        await interaction.response.send_message(message.text, ephemeral=True)


class ValuationModal(discord.ui.Modal, title='Shiller & Graham'):
    symbol = discord.ui.TextInput(label='Ticker (AAPL, TSLA, NVDA)', max_length=15)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        message = await self.bot.router.build_stock_valuation(self.user, self.symbol.value.upper())
        await interaction.response.send_message(message.text, ephemeral=True)


class PriceAlertModal(discord.ui.Modal, title='Price Alert'):
    asset_type = discord.ui.TextInput(label='Type (stock/crypto/forex/nft)', max_length=10)
    symbol = discord.ui.TextInput(label='Symbol', max_length=15)
    target = discord.ui.TextInput(label='Target Price', max_length=20)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            await self.bot.router.alerts.add_alert(
                self.user,
                self.asset_type.value.lower(),
                self.symbol.value.upper(),
                'price',
                float(self.target.value),
            )
            await interaction.response.send_message(t('msg.alert_price_created', self.user.language), ephemeral=True)
        except Exception:
            await interaction.response.send_message(t('msg.alert_price_invalid', self.user.language), ephemeral=True)


class PercentAlertModal(discord.ui.Modal, title='% Move Alert'):
    asset_type = discord.ui.TextInput(label='Type (stock/crypto/forex/nft)', max_length=10)
    symbol = discord.ui.TextInput(label='Symbol', max_length=15)
    percent = discord.ui.TextInput(label='Percent Move', max_length=20)

    def __init__(self, bot: InvestmentBot, user: UserContext) -> None:
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            await self.bot.router.alerts.add_alert(
                self.user,
                self.asset_type.value.lower(),
                self.symbol.value.upper(),
                'percent',
                float(self.percent.value),
            )
            await interaction.response.send_message(t('msg.alert_percent_created', self.user.language), ephemeral=True)
        except Exception:
            await interaction.response.send_message(t('msg.alert_percent_invalid', self.user.language), ephemeral=True)


MODAL_ACTIONS = {
    'action:portfolio_add': AddAssetModal,
    'action:ton_wallet': TonWalletModal,
    'action:ton_usernames': TonUsernamesModal,
    'action:ton_gifts': TonGiftsModal,
    'action:nft_search': NftSearchModal,
    'action:admin_broadcast': AdminBroadcastModal,
    'action:admin_toggle': AdminToggleModal,
    'action:crypto_find': CryptoFindModal,
    'action:stocks_find_input': StockFindModal,
    'action:stocks_fundamentals_input': StockFundamentalsModal,
    'action:stocks_ratios_input': StockRatiosModal,
    'action:stocks_dividends_input': StockDividendsModal,
    'action:forex_find_input': ForexFindModal,
    'action:portfolio_link_exchange': ExchangeLinkModal,
    'action:portfolio_link_wallet': WalletLinkModal,
    'action:portfolio_import_csv': CsvImportModal,
    'action:stocks_valuation': ValuationModal,
    'action:alerts_price_add': PriceAlertModal,
    'action:alerts_percent_add': PercentAlertModal,
}


def _fmt_price(value: object) -> str:
    if isinstance(value, (int, float)):
        if value >= 1:
            return f"${value:,.2f}"
        return f"${value:,.6f}"
    return 'N/A'


def _fmt_pct(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value:+.2f}%"
    return 'N/A'


def _fmt_cap(value: object) -> str:
    if not isinstance(value, (int, float)):
        return 'N/A'
    if value >= 1_000_000_000_000:
        return f"${value/1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    return f"${value:,.0f}"


async def run_discord() -> None:
    cfg = load_config()
    await init_db()
    intents = discord.Intents.default()
    bot = InvestmentBot(router=_build_router(), admin_ids=cfg.admin_user_ids, intents=intents)

    @bot.tree.command(name='start', description='Open the main menu')
    async def start(interaction: discord.Interaction) -> None:
        if not await rate_limiter.allow(f"dc:{interaction.user.id}"):
            await interaction.response.send_message(t('msg.rate_limited', 'ru'), ephemeral=True)
            return
        user = await bot.router.users.get_or_create_user('discord', str(interaction.user.id), interaction.user.name, interaction.user.id in cfg.admin_user_ids, None)
        bot.user_cache[str(interaction.user.id)] = user
        message = bot.router.main_menu(user)
        await bot.render_message(interaction, message, user)

    await bot.start(cfg.discord_bot_token)


if __name__ == '__main__':
    asyncio.run(run_discord())
