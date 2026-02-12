from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

from config import load_config
from database import init_db
from core.router import Router, ACTION_BACK_MENU
from core.ui import UIMessage, ButtonSpec
from core.permissions import UserContext
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

log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'telegram.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(),
    ],
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger('telegram_app')

rate_limiter = RateLimiter()


def _infer_style(btn: ButtonSpec) -> str | None:
    text = (btn.label or '').lower()
    action = (btn.action or '').lower()
    danger_keys = ['remove', 'delete', 'cancel', 'toggle', 'off', 'stop', 'unsubscribe', 'danger', 'удал', 'отмен', 'стоп']
    success_keys = ['add', 'create', 'start', 'open', 'upgrade', 'buy', 'confirm', 'success', 'добав', 'созд', 'нач', 'откры', 'апгрейд']

    if any(k in text or k in action for k in danger_keys):
        return 'danger'
    if any(k in text or k in action for k in success_keys):
        return 'success'
    if action.startswith('menu:') or action.startswith('page:'):
        return 'primary'
    return 'primary'


def _keyboard_from_buttons(buttons: list[list[ButtonSpec]] | None, webapp_url: str) -> InlineKeyboardMarkup | None:
    if not buttons:
        return None
    rows: list[list[InlineKeyboardButton]] = []
    for row in buttons:
        btn_row: list[InlineKeyboardButton] = []
        for btn in row:
            style = btn.style or _infer_style(btn)
            if btn.action.startswith('webapp:'):
                url = btn.action.replace('webapp:', '') or webapp_url
                btn_row.append(InlineKeyboardButton(btn.label, web_app=WebAppInfo(url=url), api_kwargs={'style': style}))
            elif btn.action.startswith('url:'):
                url = btn.action.replace('url:', '')
                btn_row.append(InlineKeyboardButton(btn.label, url=url, api_kwargs={'style': style}))
            else:
                btn_row.append(InlineKeyboardButton(btn.label, callback_data=btn.action, api_kwargs={'style': style}))
        rows.append(btn_row)
    return InlineKeyboardMarkup(rows)


async def _send_ui(update: Update, context: ContextTypes.DEFAULT_TYPE, message: UIMessage) -> None:
    cfg = load_config()
    keyboard = _keyboard_from_buttons(message.buttons, cfg.telegram_webapp_url)
    if update.callback_query:
        await update.callback_query.edit_message_text(message.text, reply_markup=keyboard, parse_mode=message.parse_mode)
        if update.callback_query.message:
            context.user_data['menu_message_id'] = update.callback_query.message.message_id
            context.user_data['menu_chat_id'] = update.callback_query.message.chat_id
    else:
        sent = await update.message.reply_text(message.text, reply_markup=keyboard, parse_mode=message.parse_mode)
        context.user_data['menu_message_id'] = sent.message_id
        context.user_data['menu_chat_id'] = sent.chat_id


async def _edit_menu_message(update: Update, context: ContextTypes.DEFAULT_TYPE, message: UIMessage) -> None:
    cfg = load_config()
    keyboard = _keyboard_from_buttons(message.buttons, cfg.telegram_webapp_url)
    chat_id = context.user_data.get('menu_chat_id') or update.effective_chat.id
    msg_id = context.user_data.get('menu_message_id')
    if msg_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=message.text,
                reply_markup=keyboard,
                parse_mode=message.parse_mode,
            )
            return
        except Exception:
            pass
    await _send_ui(update, context, message)


async def _delete_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        await context.bot.delete_message(
            chat_id=update.message.chat_id,
            message_id=update.message.message_id,
        )
    except Exception:
        pass


def _ensure_buttons(user: UserContext, message: UIMessage, back_menu: str) -> UIMessage:
    if message.buttons is None:
        message.buttons = [
            [ButtonSpec(t('btn.back', user.language), f'menu:{back_menu}')],
            [ButtonSpec(t('btn.main_menu', user.language), 'menu:main')],
        ]
    return message


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

async def _ensure_user_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> UserContext:
    router: Router = context.bot_data['router']
    cfg = load_config()
    if not update.effective_user:
        raise RuntimeError('missing_user')
    is_admin = update.effective_user.id in cfg.admin_user_ids
    user = await router.users.get_or_create_user(
        'telegram',
        str(update.effective_user.id),
        update.effective_user.username,
        is_admin,
        update.effective_user.language_code,
    )
    context.user_data['user'] = user
    if update.effective_user and not context.user_data.get('mention'):
        context.user_data['mention'] = update.effective_user.mention_markdown()
    return user


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    router: Router = context.bot_data['router']
    logger.info("Received /start from user_id=%s", update.effective_user.id if update.effective_user else 'unknown')
    if not await rate_limiter.allow(f"tg:{update.effective_user.id}"):
        return
    user = await _ensure_user_context(update, context)
    mention = context.user_data.get('mention') or (user.username or 'Investor')
    message = router.main_menu(user, mention)
    await _send_ui(update, context, message)


async def valuation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    router: Router = context.bot_data['router']
    if not await rate_limiter.allow(f"tg:{update.effective_user.id}"):
        return
    user = await _ensure_user_context(update, context)
    message = await router.handle_action('stocks_valuation', user)
    context.user_data['awaiting'] = message.expect_input
    context.user_data['awaiting_action'] = 'stocks_valuation'
    await _send_ui(update, context, message)


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    router: Router = context.bot_data['router']
    if not await rate_limiter.allow(f"tg:{update.effective_user.id}"):
        return
    user = await _ensure_user_context(update, context)
    mention = context.user_data.get('mention') or (user.username or 'Investor')
    message = router.main_menu(user, mention)
    await _send_ui(update, context, message)


async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    router: Router = context.bot_data['router']
    if not await rate_limiter.allow(f"tg:{update.effective_user.id}"):
        return
    user = await _ensure_user_context(update, context)
    message = await router.handle_action('crypto_prices', user)
    await _send_ui(update, context, message)


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    router: Router = context.bot_data['router']
    if not await rate_limiter.allow(f"tg:{update.effective_user.id}"):
        return
    user = await _ensure_user_context(update, context)
    message = await router.handle_action('stocks_find', user)
    await _send_ui(update, context, message)


async def crypto_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    router: Router = context.bot_data['router']
    if not await rate_limiter.allow(f"tg:{update.effective_user.id}"):
        return
    user = await _ensure_user_context(update, context)
    message = router.menu('crypto', user)
    await _send_ui(update, context, message)


async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    router: Router = context.bot_data['router']
    if not await rate_limiter.allow(f"tg:{update.effective_user.id}"):
        return
    user = await _ensure_user_context(update, context)
    message = router.menu('onboarding', user)
    await _send_ui(update, context, message)


async def faq_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    router: Router = context.bot_data['router']
    if not await rate_limiter.allow(f"tg:{update.effective_user.id}"):
        return
    user = await _ensure_user_context(update, context)
    message = await router.handle_action('education_glossary', user)
    await _send_ui(update, context, message)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    router: Router = context.bot_data['router']
    logger.info("Callback from user_id=%s data=%s", update.effective_user.id if update.effective_user else 'unknown', update.callback_query.data if update.callback_query else None)
    if update.callback_query:
        data = update.callback_query.data or ''
        try:
            await update.callback_query.answer()
        except Exception:
            pass
        if _is_translate_request(data):
            lang = 'ru'
            user_ctx: UserContext | None = context.user_data.get('user')
            if user_ctx:
                lang = user_ctx.language
            try:
                await update.callback_query.edit_message_text(
                    t('msg.translating', lang),
                    reply_markup=update.callback_query.message.reply_markup if update.callback_query.message else None,
                )
            except Exception:
                pass
    if not await rate_limiter.allow(f"tg:{update.effective_user.id}"):
        return
    user: UserContext = context.user_data.get('user')
    if not user:
        await start(update, context)
        return
    data = update.callback_query.data or ''
    if data.startswith('menu:'):
        menu_id = data.split(':', 1)[1]
        if menu_id == 'main':
            mention = context.user_data.get('mention')
            if not mention and update.effective_user:
                mention = update.effective_user.mention_markdown()
                context.user_data['mention'] = mention
            message = router.main_menu(user, mention)
        else:
            message = router.menu(menu_id, user)
        await _send_ui(update, context, message)
        return
    if data.startswith('action:'):
        action_payload = data.split(':', 1)[1]
        if ':' in action_payload:
            action, payload = action_payload.split(':', 1)
        else:
            action, payload = action_payload, None
        message = await router.handle_action(action, user, payload)
        context.user_data['awaiting'] = message.expect_input
        context.user_data['awaiting_action'] = action if message.expect_input else None
        await _send_ui(update, context, message)
        return
    if data.startswith('page:'):
        _, key, page = data.split(':', 2)
        message = await router.handle_action(key, user, page)
        await _send_ui(update, context, message)
        return


def _is_translate_request(data: str) -> bool:
    return (
        data.startswith('page:news_headlines:') and data.endswith(':tr')
        or data.startswith('page:news_project:') and data.endswith(':tr')
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    router: Router = context.bot_data['router']
    logger.info("Message from user_id=%s text=%s awaiting=%s", update.effective_user.id if update.effective_user else 'unknown', update.message.text if update.message else None, context.user_data.get('awaiting'))
    if not await rate_limiter.allow(f"tg:{update.effective_user.id}"):
        return
    user: UserContext = context.user_data.get('user')
    if not user:
        await start(update, context)
        return

    text = (update.message.text or '').strip()
    awaiting = context.user_data.get('awaiting')
    if not awaiting:
        return

    await _delete_user_message(update, context)

    back_menu = ACTION_BACK_MENU.get(awaiting, 'main')

    if awaiting == 'portfolio_add':
        try:
            asset_type, symbol, amount, cost = text.split()[:4]
            await router.portfolio.add_asset(user, asset_type.lower(), symbol.upper(), float(amount), float(cost))
            response = await router.handle_action('portfolio_list', user)
        except Exception:
            response = UIMessage(text=t('msg.asset_invalid', user.language))
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'portfolio_remove':
        removed = await router.portfolio.remove_asset(user, text.upper())
        if removed:
            response = await router.handle_action('portfolio_list', user)
        else:
            response = UIMessage(text=t('msg.asset_removed', user.language, count=removed))
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'ton_wallet':
        data = await router.ton.lookup_wallet(text)
        response = UIMessage(text=format_kv_output('TON Wallet', data))
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'ton_usernames':
        response = await router.build_ton_usernames(user, text)
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'ton_gifts':
        response = await router.build_ton_gifts(user, text)
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'nft_search':
        items = await router.nft.search_collection(text)
        response = UIMessage(text='\n'.join(items))
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'admin_broadcast':
        response = UIMessage(text=t('msg.broadcast_queued', user.language))
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'admin_toggle':
        response = UIMessage(text=t('msg.feature_toggled', user.language, feature=text))
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'admin_verify':
        parts = text.strip().split()
        if len(parts) >= 2:
            target_id = parts[0]
            badge = parts[1].lower()
            if badge in ('major', 'hodl', 'verified', 'none'):
                await router.users.update_badge(target_id, badge)
                response = UIMessage(text=t('msg.verify_done', user.language, badge=t(f'badge.{badge}', user.language)))
            else:
                response = UIMessage(text=t('msg.verify_invalid', user.language))
        else:
            response = UIMessage(text=t('msg.verify_hint', user.language))
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'alert_price':
        try:
            asset_type, symbol, target = text.split()[:3]
            await router.alerts.add_alert(user, asset_type.lower(), symbol.upper(), 'price', float(target))
            response = UIMessage(text=t('msg.alert_price_created', user.language))
        except Exception:
            response = UIMessage(text=t('msg.alert_price_invalid', user.language))
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'alert_percent':
        try:
            asset_type, symbol, target = text.split()[:3]
            await router.alerts.add_alert(user, asset_type.lower(), symbol.upper(), 'percent', float(target))
            response = UIMessage(text=t('msg.alert_percent_created', user.language))
        except Exception:
            response = UIMessage(text=t('msg.alert_percent_invalid', user.language))
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'portfolio_link_exchange':
        response = await router.link_exchange_from_input(user, text)
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'portfolio_link_wallet':
        response = await router.link_wallet_from_input(user, text)
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'portfolio_import_csv':
        response = await router.import_csv_from_text(user, text)
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'crypto_find':
        symbol = text.split()[0].upper()
        response = await router.build_crypto_profile(user, symbol)
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'stocks_find':
        symbol = text.split()[0].upper()
        response = await router.build_stock_profile(user, symbol)
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'stocks_fundamentals_symbol':
        symbol = text.split()[0].upper()
        response = await router.build_stock_fundamentals(user, symbol)
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'stocks_ratios_symbol':
        symbol = text.split()[0].upper()
        response = await router.build_stock_ratios(user, symbol)
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'stocks_dividends_symbol':
        symbol = text.split()[0].upper()
        response = await router.build_stock_dividends(user, symbol)
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'stocks_earnings_symbol':
        symbol = text.split()[0].upper()
        response = await router.build_stock_earnings(user, symbol)
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'forex_find':
        pair = text.split()[0].upper()
        response = await router.build_forex_profile(user, pair)
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return

    if awaiting == 'stocks_valuation':
        symbol = text.split()[0].upper()
        response = await router.build_stock_valuation(user, symbol)
        context.user_data['awaiting'] = None
        response = _ensure_buttons(user, response, back_menu)
        await _edit_menu_message(update, context, response)
        return


def format_kv_output(title: str, data: dict[str, str]) -> str:
    lines = [f"*{k}:* {v}" for k, v in data.items()]
    return f"*{title}*\n" + "\n".join(lines)


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


def run_telegram() -> None:
    cfg = load_config()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    app = Application.builder().token(cfg.telegram_bot_token).build()
    app.bot_data['router'] = _build_router()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('menu', menu))
    app.add_handler(CommandHandler('dashboard', dashboard))
    app.add_handler(CommandHandler('price', price))
    app.add_handler(CommandHandler('crypto', crypto_menu))
    app.add_handler(CommandHandler('help', help_menu))
    app.add_handler(CommandHandler('faq', faq_menu))
    app.add_handler(CommandHandler('valuation', valuation))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    app.run_polling(drop_pending_updates=True, close_loop=False)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error", exc_info=context.error)


if __name__ == '__main__':
    run_telegram()
