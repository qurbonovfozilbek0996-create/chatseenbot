from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.db import (
    get_user, create_user, get_setting,
    get_channels, add_referral_count, is_admin
)
from utils.keyboards import main_menu_kb, subscription_check_kb, admin_menu_kb
from config import BOT_NAME, REFERRAL_BONUS

router = Router()

async def check_subscription(bot, user_id, channels):
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch['channel_id'], user_id)
            if member.status in ['left', 'kicked', 'restricted']:
                return False
        except:
            pass
    return True

async def send_main_menu(message, text=None):
    bot_active = await get_setting('bot_active')
    if bot_active == '0':
        await message.answer("🔧 Bot hozirda texnik ishlar uchun o'chirilgan.")
        return
    welcome = await get_setting('welcome_text') or f"{BOT_NAME} ga xush kelibsiz!"
    await message.answer(text or welcome, reply_markup=main_menu_kb())

@router.message(CommandStart())
async def start_handler(message: Message, bot):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    full_name = message.from_user.full_name or ""

    referral_id = None
    args = message.text.split()
    if len(args) > 1:
        try:
            referral_id = int(args[1])
            if referral_id == user_id:
                referral_id = None
        except:
            pass

    user = await get_user(user_id)
    is_new = user is None
    await create_user(user_id, username, full_name, referral_id)

    if is_new and referral_id:
        ref_bonus = float(await get_setting('referral_bonus') or REFERRAL_BONUS)
        await add_referral_count(referral_id, ref_bonus)
        try:
            await bot.send_message(
                referral_id,
                f"🎉 Yangi referal! +{ref_bonus:.0f} so'm hisobingizga tushdi!"
            )
        except:
            pass

    user = await get_user(user_id)
    if user and user['is_banned']:
        await message.answer("🚫 Siz botdan bloklangansiz.")
        return

    channels = await get_channels()
    if channels:
        subscribed = await check_subscription(bot, user_id, channels)
        if not subscribed:
            kb = await subscription_check_kb(channels)
            await message.answer(
                f"📢 Botdan foydalanish uchun kanallarga obuna bo'ling:",
                reply_markup=kb
            )
            return

    await send_main_menu(message)

@router.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery, bot):
    channels = await get_channels()
    subscribed = await check_subscription(bot, callback.from_user.id, channels)
    if subscribed:
        await callback.message.delete()
        await send_main_menu(callback.message)
    else:
        await callback.answer("❌ Hali obuna bo'lmadingiz!", show_alert=True)

@router.message(Command("admin"))
async def admin_command(message: Message):
    if not await is_admin(message.from_user.id):
        return
    await message.answer("🔐 Admin paneliga xush kelibsiz!", reply_markup=admin_menu_kb())
