from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.db import (
    get_user, get_service, create_order, update_order_api_id,
    get_user_orders, update_user_balance, get_promo, use_promo,
    get_setting, get_categories, get_subcategories,
    get_services_by_subcategory, get_services_by_category
)
from utils.keyboards import (
    categories_kb, subcategories_kb, services_kb,
    confirm_order_kb, cancel_kb, main_menu_kb
)
from utils.api import place_order

router = Router()

class OrderState(StatesGroup):
    waiting_link = State()
    waiting_quantity = State()
    confirming = State()

class PromoState(StatesGroup):
    waiting_code = State()

@router.message(F.text == "🛒 Xizmatlarga buyurtma berish")
async def services_menu(message: Message):
    user = await get_user(message.from_user.id)
    if not user or user['is_banned']:
        return
    kb = await categories_kb()
    if not kb:
        await message.answer("😔 Hozircha xizmatlar mavjud emas.")
        return
    await message.answer("📁 Bo'limni tanlang:", reply_markup=kb)

@router.callback_query(F.data.startswith("cat:"))
async def category_selected(callback: CallbackQuery):
    cat_id = int(callback.data.split(":")[1])
    subs = await get_subcategories(cat_id)
    if subs:
        kb = await subcategories_kb(cat_id)
        await callback.message.edit_text("📂 Ichki bo'lim tanlang:", reply_markup=kb)
    else:
        kb, services = await services_kb(cat_id, 'cat')
        if not services:
            await callback.answer("😔 Xizmatlar yo'q.", show_alert=True)
            return
        currency = await get_setting('currency') or 'UZS'
        text = "📋 <b>Xizmatlar:</b>\n\n"
        for i, srv in enumerate(services):
            text += (
                f"{i+1}. {srv['name']}\n"
                f"   💰 {srv['price_per_1000']:,.0f} {currency} / 1000\n"
                f"   📊 Min: {srv['min_quantity']} | Max: {srv['max_quantity']}\n\n"
            )
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data.startswith("sub:"))
async def subcategory_selected(callback: CallbackQuery):
    sub_id = int(callback.data.split(":")[1])
    kb, services = await services_kb(sub_id, 'sub')
    if not services:
        await callback.answer("😔 Xizmatlar yo'q.", show_alert=True)
        return
    currency = await get_setting('currency') or 'UZS'
    text = "📋 <b>Xizmatlar:</b>\n\n"
    for i, srv in enumerate(services):
        text += (
            f"{i+1}. {srv['name']}\n"
            f"   💰 {srv['price_per_1000']:,.0f} {currency} / 1000\n"
            f"   📊 Min: {srv['min_quantity']} | Max: {srv['max_quantity']}\n\n"
        )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data.startswith("back:"))
async def back_handler(callback: CallbackQuery):
    parts = callback.data.split(":")
    if parts[1] == "cats":
        kb = await categories_kb()
        await callback.message.edit_text("📁 Bo'lim tanlang:", reply_markup=kb)
    elif parts[1] == "cat" and len(parts) > 2:
        kb = await subcategories_kb(int(parts[2]))
        await callback.message.edit_text("📂 Ichki bo'lim tanlang:", reply_markup=kb)

@router.callback_query(F.data.startswith("srv:"))
async def service_selected(callback: CallbackQuery, state: FSMContext):
    srv_id = int(callback.data.split(":")[1])
    srv = await get_service(srv_id)
    if not srv:
        await callback.answer("❌ Topilmadi", show_alert=True)
        return
    currency = await get_setting('currency') or 'UZS'
    await state.update_data(service_id=srv_id)
    await state.set_state(OrderState.waiting_link)
    text = (
        f"📌 <b>{srv['name']}</b>\n\n"
        f"💰 {srv['price_per_1000']:,.0f} {currency} / 1000 ta\n"
        f"📊 Min: {srv['min_quantity']} | Max: {srv['max_quantity']}\n\n"
        f"🔗 Havolani yuboring:"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=cancel_kb())

@router.message(OrderState.waiting_link)
async def got_link(message: Message, state: FSMContext):
    if not message.text or not message.text.startswith("http"):
        await message.answer("❌ To'g'ri havola kiriting (http... bilan boshlansin)!")
        return
    await state.update_data(link=message.text.strip())
    data = await state.get_data()
    srv = await get_service(data['service_id'])
    await state.set_state(OrderState.waiting_quantity)
    await message.answer(
        f"✅ Havola qabul qilindi!\n\n"
        f"📊 Miqdor kiriting ({srv['min_quantity']} - {srv['max_quantity']}):",
        reply_markup=cancel_kb()
    )

@router.message(OrderState.waiting_quantity)
async def got_quantity(message: Message, state: FSMContext):
    try:
        qty = int(message.text.strip())
    except:
        await message.answer("❌ Raqam kiriting!")
        return
    data = await state.get_data()
    srv = await get_service(data['service_id'])
    if qty < srv['min_quantity'] or qty > srv['max_quantity']:
        await message.answer(
            f"❌ {srv['min_quantity']} va {srv['max_quantity']} orasida bo'lishi kerak!"
        )
        return
    charge = (qty / 1000) * srv['price_per_1000']
    user = await get_user(message.from_user.id)
    currency = await get_setting('currency') or 'UZS'
    await state.update_data(quantity=qty, charge=charge)
    await state.set_state(OrderState.confirming)
    bal_ok = "✅" if user['balance'] >= charge else "❌"
    text = (
        f"📋 <b>Buyurtma:</b>\n\n"
        f"🛍 {srv['name']}\n"
        f"🔗 {data['link']}\n"
        f"📊 {qty:,} ta\n"
        f"💰 {charge:,.0f} {currency}\n"
        f"💳 Balans: {user['balance']:,.0f} {currency} {bal_ok}\n\n"
    )
    if user['balance'] < charge:
        text += "❌ Balans yetarli emas!"
        await message.answer(text, parse_mode="HTML", reply_markup=cancel_kb())
        await state.clear()
    else:
        text += "Tasdiqlaysizmi?"
        await message.answer(text, parse_mode="HTML", reply_markup=confirm_order_kb(data['service_id']))

@router.callback_query(F.data.startswith("confirm_order:"))
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get('service_id'):
        await callback.answer("❌ Ma'lumot topilmadi", show_alert=True)
        return
    srv = await get_service(data['service_id'])
    user = await get_user(callback.from_user.id)
    currency = await get_setting('currency') or 'UZS'
    if user['balance'] < data['charge']:
        await callback.answer("❌ Balans yetarli emas!", show_alert=True)
        return
    await update_user_balance(callback.from_user.id, -data['charge'])
    order_id = await create_order(
        callback.from_user.id, data['service_id'],
        srv['api_service_id'], data['link'],
        data['quantity'], data['charge']
    )
    api_order_id, err = await place_order(
        srv['api_service_id'], data['link'], data['quantity']
    )
    if err or not api_order_id:
        await update_user_balance(callback.from_user.id, data['charge'])
        await callback.message.edit_text(f"❌ Xato: {err}\nPulingiz qaytarildi.")
        await state.clear()
        return
    await update_order_api_id(order_id, int(api_order_id))
    await state.clear()
    await callback.message.edit_text(
        f"✅ <b>Buyurtma qabul qilindi!</b>\n\n"
        f"🆔 #{order_id}\n"
        f"🛍 {srv['name']}\n"
        f"📊 {data['quantity']:,} ta\n"
        f"💰 {data['charge']:,.0f} {currency}\n\n"
        f"⏳ Ishlanmoqda...",
        parse_mode="HTML"
    )

@router.callback_query(F.data == "cancel")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")

@router.message(F.text == "👤 Mening hisobim")
async def my_account(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        return
    currency = await get_setting('currency') or 'UZS'
    orders = await get_user_orders(message.from_user.id, 100)
    vip = "⭐️ VIP" if user['is_vip'] else "👤 Oddiy"
    await message.answer(
        f"👤 <b>Mening hisobim</b>\n\n"
        f"🆔 ID: <code>{user['user_id']}</code>\n"
        f"👑 Status: {vip}\n"
        f"💰 Balans: <b>{user['balance']:,.0f} {currency}</b>\n"
        f"📋 Buyurtmalar: {len(orders)} ta\n"
        f"👥 Referallar: {user['referral_count']} ta\n"
        f"💸 Jami to'ldirilgan: {user['total_deposited']:,.0f} {currency}",
        parse_mode="HTML"
    )

@router.message(F.text == "📋 Buyurtmalarim")
async def my_orders(message: Message):
    orders = await get_user_orders(message.from_user.id, 10)
    if not orders:
        await message.answer("📋 Buyurtmalar mavjud emas.")
        return
    currency = await get_setting('currency') or 'UZS'
    status_map = {
        'pending': '⏳ Kutilmoqda',
        'processing': '🔄 Jarayonda',
        'completed': '✅ Tugallandi',
        'partial': '⚠️ Qisman',
        'canceled': '❌ Bekor'
    }
    text = "📋 <b>So'nggi buyurtmalar:</b>\n\n"
    for o in orders:
        status = status_map.get(o['status'], o['status'])
        text += f"#{o['id']} | {o['service_name'] or 'NA'}\n{status} | {o['quantity']:,} ta | {o['charge']:,.0f} {currency}\n\n"
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "👥 Referal tizimi")
async def referral_menu(message: Message):
    user = await get_user(message.from_user.id)
    bonus = await get_setting('referral_bonus') or '100'
    currency = await get_setting('currency') or 'UZS'
    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    await message.answer(
        f"👥 <b>Referal tizimi</b>\n\n"
        f"🔗 {ref_link}\n\n"
        f"🎁 Har bir referal: <b>{bonus} {currency}</b>\n"
        f"👥 Referallaringiz: <b>{user['referral_count']} ta</b>",
        parse_mode="HTML"
    )

@router.message(F.text == "🎁 Promokod")
async def promo_start(message: Message, state: FSMContext):
    await state.set_state(PromoState.waiting_code)
    await message.answer("🎟 Promokodni kiriting:", reply_markup=cancel_kb())

@router.message(PromoState.waiting_code)
async def promo_entered(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    promo = await get_promo(code)
    currency = await get_setting('currency') or 'UZS'
    if not promo:
        await message.answer("❌ Promokod topilmadi yoki muddati o'tgan.")
        await state.clear()
        return
    used = await use_promo(message.from_user.id, promo['id'])
    if not used:
        await message.answer("❌ Bu promokodni allaqachon ishlatgansiz.")
        await state.clear()
        return
    await update_user_balance(message.from_user.id, promo['amount'])
    await state.clear()
    await message.answer(f"✅ +{promo['amount']:,.0f} {currency} balansingizga tushdi!")

@router.message(F.text == "📞 Murojaat")
async def contact_menu(message: Message):
    await message.answer(
        "📞 <b>Murojaat</b>\n\nAdmin bilan bog'laning: @admin_username",
        parse_mode="HTML"
    )
