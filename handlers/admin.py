from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Filter

from database.db import (
    get_user, get_all_users, get_user_count, get_order_count,
    get_payment_count, get_total_revenue, get_setting, set_setting,
    get_admins, add_admin, remove_admin, is_admin,
    get_payment_methods, add_payment_method, delete_payment_method,
    get_categories, get_category, add_category, update_category,
    delete_category, toggle_category,
    get_subcategories, get_subcategory, add_subcategory, delete_subcategory,
    get_service, add_service, delete_service, toggle_service,
    get_services_by_subcategory, get_services_by_category,
    get_channels, add_channel, delete_channel,
    get_all_promos, create_promo, delete_promo,
    ban_user, set_user_vip, update_user_balance
)
from utils.keyboards import (
    admin_menu_kb, admin_settings_kb, base_settings_kb,
    admins_manage_kb, wallets_kb, api_settings_kb, design_kb,
    admin_category_actions_kb, admin_subcategory_actions_kb,
    user_manage_kb, cancel_kb, main_menu_kb, payment_confirm_kb
)
from utils.api import get_api_balance, get_api_services
from config import ADMIN_IDS

router = Router()

class AdminFilter(Filter):
    async def __call__(self, event) -> bool:
        user_id = event.from_user.id if hasattr(event, 'from_user') else None
        return user_id and await is_admin(user_id)

class AdminState(StatesGroup):
    set_currency = State()
    set_vip_price = State()
    set_referral_bonus = State()
    set_transfer_fee = State()
    add_admin_id = State()
    del_admin_id = State()
    add_wallet_name = State()
    add_wallet_emoji = State()
    add_wallet_details = State()
    set_api_url = State()
    set_api_key = State()
    set_design_val = State()
    set_design_key = State()
    add_cat_name = State()
    add_cat_emoji = State()
    add_sub_name = State()
    add_sub_emoji = State()
    add_sub_cat_id = State()
    add_srv_api_id = State()
    add_srv_parent = State()
    add_promo_code = State()
    add_promo_amount = State()
    add_promo_uses = State()
    add_ch_id = State()
    add_ch_name = State()
    add_ch_link = State()
    broadcast_text = State()
    user_search = State()
    add_balance_amount = State()

# ============ ASOSIY ============
@router.message(AdminFilter(), F.text == "◀️ Orqaga")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu", reply_markup=main_menu_kb())

@router.message(AdminFilter(), F.text == "🔘 Tugmalar")
async def admin_panel_btn(message: Message):
    await message.answer("🔐 Admin paneliga xush kelibsiz!", reply_markup=admin_menu_kb())

@router.message(AdminFilter(), F.text == "⚙️ Asosiy sozlamalar")
async def admin_main_settings(message: Message):
    await message.answer(
        "⚙️ <b>Asosiy sozlamalar</b>\n\nNimani o'zgartiramiz?",
        parse_mode="HTML",
        reply_markup=admin_settings_kb()
    )

@router.callback_query(AdminFilter(), F.data == "adm:settings")
async def adm_settings_cb(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚙️ <b>Asosiy sozlamalar</b>",
        parse_mode="HTML",
        reply_markup=admin_settings_kb()
    )

@router.callback_query(AdminFilter(), F.data == "adm:back")
async def adm_back(callback: CallbackQuery):
    await callback.message.delete()

@router.callback_query(AdminFilter(), F.data == "cancel")
async def admin_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
# ============ BIRLAMCHI SOZLAMALAR ============
@router.callback_query(AdminFilter(), F.data == "adm:base_settings")
async def adm_base_settings(callback: CallbackQuery):
    currency = await get_setting('currency') or 'UZS'
    vip = await get_setting('vip_price') or '15000'
    ref = await get_setting('referral_bonus') or '100'
    fee = await get_setting('transfer_fee') or '0'
    text = (
        f"✳️ <b>Birlamchi sozlamalar:</b>\n\n"
        f"1. Valyuta: {currency}\n"
        f"2. VIP narxi: {vip} {currency}\n"
        f"3. Taklif foizi: {ref} {currency}\n"
        f"4. O'tkazma narxi: {fee} {currency}"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=base_settings_kb())

@router.callback_query(AdminFilter(), F.data == "adm:currency")
async def adm_set_currency(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.set_currency)
    await callback.message.edit_text("💱 Yangi valyutani kiriting:", reply_markup=cancel_kb())

@router.message(AdminFilter(), AdminState.set_currency)
async def got_currency(message: Message, state: FSMContext):
    await set_setting('currency', message.text.strip().upper())
    await state.clear()
    await message.answer(f"✅ Valyuta {message.text.strip().upper()} ga o'zgartirildi!")

@router.callback_query(AdminFilter(), F.data == "adm:vip_price")
async def adm_vip_price(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.set_vip_price)
    await callback.message.edit_text("💎 VIP narxini kiriting:", reply_markup=cancel_kb())

@router.message(AdminFilter(), AdminState.set_vip_price)
async def got_vip_price(message: Message, state: FSMContext):
    try:
        val = float(message.text.strip())
        await set_setting('vip_price', str(val))
        await state.clear()
        await message.answer(f"✅ VIP narxi {val:,.0f} ga o'zgartirildi!")
    except:
        await message.answer("❌ Raqam kiriting!")

@router.callback_query(AdminFilter(), F.data == "adm:referral_bonus")
async def adm_ref_bonus(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.set_referral_bonus)
    await callback.message.edit_text("🤝 Referal bonusini kiriting:", reply_markup=cancel_kb())

@router.message(AdminFilter(), AdminState.set_referral_bonus)
async def got_ref_bonus(message: Message, state: FSMContext):
    try:
        val = float(message.text.strip())
        await set_setting('referral_bonus', str(val))
        await state.clear()
        await message.answer(f"✅ Referal bonus {val:,.0f} ga o'zgartirildi!")
    except:
        await message.answer("❌ Raqam kiriting!")

@router.callback_query(AdminFilter(), F.data == "adm:transfer_fee")
async def adm_transfer_fee(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.set_transfer_fee)
    await callback.message.edit_text("🔄 O'tkazma narxini kiriting:", reply_markup=cancel_kb())

@router.message(AdminFilter(), AdminState.set_transfer_fee)
async def got_transfer_fee(message: Message, state: FSMContext):
    try:
        val = float(message.text.strip())
        await set_setting('transfer_fee', str(val))
        await state.clear()
        await message.answer(f"✅ O'tkazma narxi {val:,.0f} ga o'zgartirildi!")
    except:
        await message.answer("❌ Raqam kiriting!")

# ============ ADMINLAR ============
@router.callback_query(AdminFilter(), F.data == "adm:admins")
async def adm_admins(callback: CallbackQuery):
    await callback.message.edit_text(
        "🗂 <b>Adminlar</b>", parse_mode="HTML",
        reply_markup=admins_manage_kb()
    )

@router.callback_query(AdminFilter(), F.data == "adm:add_admin")
async def adm_add_admin(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.add_admin_id)
    await callback.message.edit_text("👤 Admin ID sini yuboring:", reply_markup=cancel_kb())

@router.message(AdminFilter(), AdminState.add_admin_id)
async def got_add_admin(message: Message, state: FSMContext, bot):
    try:
        target_id = int(message.text.strip())
        try:
            chat = await bot.get_chat(target_id)
            await add_admin(target_id, chat.username or '', chat.full_name or str(target_id))
        except:
            await add_admin(target_id, '', str(target_id))
        await state.clear()
        await message.answer(f"✅ {target_id} admin qilindi!")
    except:
        await message.answer("❌ To'g'ri ID kiriting!")

@router.callback_query(AdminFilter(), F.data == "adm:admin_list")
async def adm_admin_list(callback: CallbackQuery):
    admins = await get_admins()
    if not admins:
        await callback.answer("Admin yo'q", show_alert=True)
        return
    text = "🗂 <b>Adminlar:</b>\n\n"
    for a in admins:
        text += f"• {a['full_name']} (@{a['username'] or 'NA'}) - <code>{a['user_id']}</code>\n"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admins_manage_kb())

@router.callback_query(AdminFilter(), F.data == "adm:del_admin")
async def adm_del_admin(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.del_admin_id)
    await callback.message.edit_text("❌ O'chirish uchun admin ID sini yuboring:", reply_markup=cancel_kb())

@router.message(AdminFilter(), AdminState.del_admin_id)
async def got_del_admin(message: Message, state: FSMContext):
    try:
        target_id = int(message.text.strip())
        await remove_admin(target_id)
        await state.clear()
        await message.answer(f"✅ {target_id} o'chirildi!")
    except:
        await message.answer("❌ To'g'ri ID kiriting!")# ============ HAMYONLAR ============
@router.callback_query(AdminFilter(), F.data == "adm:wallets")
async def adm_wallets(callback: CallbackQuery):
    await callback.message.edit_text(
        "💳 <b>Hamyonlar</b>", parse_mode="HTML",
        reply_markup=wallets_kb()
    )

@router.callback_query(AdminFilter(), F.data == "adm:add_wallet")
async def adm_add_wallet(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.add_wallet_name)
    await callback.message.edit_text("💳 To'lov tizimi nomini kiriting:", reply_markup=cancel_kb())

@router.message(AdminFilter(), AdminState.add_wallet_name)
async def got_wallet_name(message: Message, state: FSMContext):
    await state.update_data(wallet_name=message.text.strip())
    await state.set_state(AdminState.add_wallet_emoji)
    await message.answer("Emoji kiriting (masalan: 💳):")

@router.message(AdminFilter(), AdminState.add_wallet_emoji)
async def got_wallet_emoji(message: Message, state: FSMContext):
    await state.update_data(wallet_emoji=message.text.strip())
    await state.set_state(AdminState.add_wallet_details)
    await message.answer("Rekvizit kiriting (karta raqami yoki username):")

@router.message(AdminFilter(), AdminState.add_wallet_details)
async def got_wallet_details(message: Message, state: FSMContext):
    data = await state.get_data()
    await add_payment_method(
        data['wallet_name'],
        message.text.strip(),
        data.get('wallet_emoji', '💳')
    )
    await state.clear()
    await message.answer(f"✅ {data['wallet_name']} qo'shildi!")

@router.callback_query(AdminFilter(), F.data == "adm:wallet_list")
async def adm_wallet_list(callback: CallbackQuery):
    methods = await get_payment_methods(active_only=False)
    if not methods:
        await callback.answer("Hamyon yo'q", show_alert=True)
        return
    buttons = []
    for m in methods:
        buttons.append([InlineKeyboardButton(
            text=f"🗑 {m['emoji']} {m['name']}",
            callback_data=f"adm:del_wlt:{m['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm:wallets")])
    await callback.message.edit_text(
        "💳 Hamyonlar (o'chirish uchun bosing):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@router.callback_query(AdminFilter(), F.data.startswith("adm:del_wlt:"))
async def adm_delete_wallet(callback: CallbackQuery):
    wlt_id = int(callback.data.split(":")[2])
    await delete_payment_method(wlt_id)
    await callback.answer("✅ O'chirildi!")
    await adm_wallet_list(callback)

# ============ API ============
@router.callback_query(AdminFilter(), F.data == "adm:api")
async def adm_api(callback: CallbackQuery):
    api_url = await get_setting('api_url') or ''
    api_key = await get_setting('api_key') or ''
    balance_text = "Mavjud emas"
    if api_url and api_key:
        bal, err = await get_api_balance()
        balance_text = str(bal) if not err else f"Xato: {err}"
    text = (
        f"🔑 <b>API ma'lumotlari:</b>\n"
        f"{'─'*20}\n"
        f"API havola: {api_url or 'kiritilmagan'}\n\n"
        f"API kalit: {'✅ Kiritilgan' if api_key else 'kiritilmagan'}\n\n"
        f"API balans: {balance_text}\n"
        f"{'─'*20}"
    )
    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=api_settings_kb(bool(api_url and api_key))
    )

@router.callback_query(AdminFilter(), F.data == "adm:set_api")
async def adm_set_api(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.set_api_url)
    await callback.message.edit_text(
        "🔗 API havolani kiriting:\nMasalan: https://gramapi.uz/api/v2",
        reply_markup=cancel_kb()
    )

@router.message(AdminFilter(), AdminState.set_api_url)
async def got_api_url(message: Message, state: FSMContext):
    url = message.text.strip()
    if not url.startswith('http'):
        await message.answer("❌ To'g'ri URL kiriting!")
        return
    await set_setting('api_url', url)
    await state.set_state(AdminState.set_api_key)
    await message.answer("✅ URL saqlandi!\n\nEndi API kalitni kiriting:")

@router.message(AdminFilter(), AdminState.set_api_key)
async def got_api_key(message: Message, state: FSMContext):
    await set_setting('api_key', message.text.strip())
    await state.clear()
    bal, err = await get_api_balance()
    if err:
        await message.answer(f"⚠️ Saqlandi, lekin xato: {err}")
    else:
        await message.answer(f"✅ API sozlandi!\n💰 Balans: {bal}")

@router.callback_query(AdminFilter(), F.data == "adm:del_api")
async def adm_del_api(callback: CallbackQuery):
    await set_setting('api_url', '')
    await set_setting('api_key', '')
    await callback.answer("✅ API o'chirildi!")
    await adm_api(callback)

# ============ DIZAYN ============
@router.callback_query(AdminFilter(), F.data == "adm:design")
async def adm_design(callback: CallbackQuery):
    cat_row = await get_setting('categories_per_row') or '2'
    sub_row = await get_setting('subcategories_per_row') or '1'
    srv_row = await get_setting('services_per_row') or '5'
    pay_row = await get_setting('payment_per_row') or '2'
    text = (
        f"⭐️ <b>Bot dizayni</b>\n\n"
        f"1️⃣ Bo'limlar qatori: {cat_row}\n"
        f"2️⃣ Ichki bo'lim qatori: {sub_row}\n"
        f"3️⃣ Xizmatlar qatori: {srv_row}\n"
        f"4️⃣ To'lov tizim qatori: {pay_row}"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=design_kb())

@router.callback_query(AdminFilter(), F.data.startswith("adm:des:cat:"))
async def adm_design_select(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":")[3]
    keys = {
        '1': 'categories_per_row',
        '2': 'subcategories_per_row',
        '3': 'services_per_row',
        '4': 'payment_per_row',
    }
    key = keys.get(val)
    if not key:
        return
    await state.update_data(design_key=key)
    await state.set_state(AdminState.set_design_val)
    await callback.message.edit_text("📐 Raqam kiriting (1-5):", reply_markup=cancel_kb())

@router.message(AdminFilter(), AdminState.set_design_val)
async def got_design_val(message: Message, state: FSMContext):
    try:
        val = int(message.text.strip())
        if val < 1 or val > 5:
            raise ValueError
        data = await state.get_data()
        await set_setting(data['design_key'], str(val))
        await state.clear()
        await message.answer(f"✅ O'zgartirildi: {val}")
    except:
        await message.answer("❌ 1-5 orasidagi raqam kiriting!")# ============ STATISTIKA ============
@router.message(AdminFilter(), F.text == "📊 Statistika")
async def admin_stats(message: Message):
    users = await get_user_count()
    orders = await get_order_count()
    payments = await get_payment_count()
    revenue = await get_total_revenue()
    currency = await get_setting('currency') or 'UZS'
    await message.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{users}</b>\n"
        f"📋 Buyurtmalar: <b>{orders}</b>\n"
        f"💳 Tasdiqlangan to'lovlar: <b>{payments}</b>\n"
        f"💰 Jami daromad: <b>{revenue:,.0f} {currency}</b>",
        parse_mode="HTML"
    )

# ============ XIZMATLAR ============
@router.message(AdminFilter(), F.text == "🛍 Xizmatlar")
async def admin_services(message: Message):
    cats = await get_categories(active_only=False)
    buttons = []
    for cat in cats:
        status = "✅" if cat['is_active'] else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {cat['emoji']} {cat['name']}",
            callback_data=f"adm_srv:cat:{cat['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="➕ Bo'lim qo'shish", callback_data="adm_srv:add_cat")])
    await message.answer(
        "🛍 <b>Xizmatlar boshqaruvi</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@router.callback_query(AdminFilter(), F.data == "adm_srv:categories")
async def adm_srv_cats(callback: CallbackQuery):
    cats = await get_categories(active_only=False)
    buttons = []
    for cat in cats:
        status = "✅" if cat['is_active'] else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {cat['emoji']} {cat['name']}",
            callback_data=f"adm_srv:cat:{cat['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="➕ Bo'lim qo'shish", callback_data="adm_srv:add_cat")])
    await callback.message.edit_text(
        "🛍 Bo'limlar:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@router.callback_query(AdminFilter(), F.data == "adm_srv:add_cat")
async def adm_add_cat(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.add_cat_name)
    await callback.message.edit_text("📁 Bo'lim nomini kiriting:", reply_markup=cancel_kb())

@router.message(AdminFilter(), AdminState.add_cat_name)
async def got_cat_name(message: Message, state: FSMContext):
    await state.update_data(cat_name=message.text.strip())
    await state.set_state(AdminState.add_cat_emoji)
    await message.answer("Emoji kiriting (masalan: 💙):")

@router.message(AdminFilter(), AdminState.add_cat_emoji)
async def got_cat_emoji(message: Message, state: FSMContext):
    data = await state.get_data()
    cat_id = await add_category(data['cat_name'], message.text.strip())
    await state.clear()
    await message.answer(f"✅ '{data['cat_name']}' bo'limi qo'shildi!")

@router.callback_query(AdminFilter(), F.data.startswith("adm_srv:cat:"))
async def adm_cat_detail(callback: CallbackQuery):
    cat_id = int(callback.data.split(":")[2])
    cat = await get_category(cat_id)
    if not cat:
        await callback.answer("Topilmadi", show_alert=True)
        return
    status = "✅ Faol" if cat['is_active'] else "❌ Nofaol"
    await callback.message.edit_text(
        f"📁 <b>{cat['emoji']} {cat['name']}</b>\nHolat: {status}",
        parse_mode="HTML",
        reply_markup=admin_category_actions_kb(cat_id)
    )

@router.callback_query(AdminFilter(), F.data.startswith("adm_srv:toggle_cat:"))
async def adm_toggle_cat(callback: CallbackQuery):
    cat_id = int(callback.data.split(":")[3])
    await toggle_category(cat_id)
    await callback.answer("✅ Holat o'zgartirildi!")
    await adm_cat_detail(callback)

@router.callback_query(AdminFilter(), F.data.startswith("adm_srv:del_cat:"))
async def adm_del_cat(callback: CallbackQuery):
    cat_id = int(callback.data.split(":")[3])
    await delete_category(cat_id)
    await callback.answer("✅ O'chirildi!")
    await adm_srv_cats(callback)

@router.callback_query(AdminFilter(), F.data.startswith("adm_srv:subs:"))
async def adm_subs(callback: CallbackQuery):
    cat_id = int(callback.data.split(":")[2])
    subs = await get_subcategories(cat_id, active_only=False)
    buttons = []
    for sub in subs:
        buttons.append([InlineKeyboardButton(
            text=f"{sub['emoji']} {sub['name']}",
            callback_data=f"adm_srv:sub:{sub['id']}:{cat_id}"
        )])
    buttons.append([InlineKeyboardButton(
        text="➕ Ichki bo'lim qo'shish",
        callback_data=f"adm_srv:add_sub:{cat_id}"
    )])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"adm_srv:cat:{cat_id}")])
    await callback.message.edit_text(
        "📂 Ichki bo'limlar:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@router.callback_query(AdminFilter(), F.data.startswith("adm_srv:add_sub:"))
async def adm_add_sub(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split(":")[3])
    await state.update_data(sub_cat_id=cat_id)
    await state.set_state(AdminState.add_sub_name)
    await callback.message.edit_text("📂 Ichki bo'lim nomini kiriting:", reply_markup=cancel_kb())

@router.message(AdminFilter(), AdminState.add_sub_name)
async def got_sub_name(message: Message, state: FSMContext):
    await state.update_data(sub_name=message.text.strip())
    await state.set_state(AdminState.add_sub_emoji)
    await message.answer("Emoji kiriting:")

@router.message(AdminFilter(), AdminState.add_sub_emoji)
async def got_sub_emoji(message: Message, state: FSMContext):
    data = await state.get_data()
    await add_subcategory(data['sub_cat_id'], data['sub_name'], message.text.strip())
    await state.clear()
    await message.answer(f"✅ '{data['sub_name']}' ichki bo'limi qo'shildi!")

@router.callback_query(AdminFilter(), F.data.startswith("adm_srv:sub:"))
async def adm_sub_detail(callback: CallbackQuery):
    parts = callback.data.split(":")
    sub_id = int(parts[2])
    cat_id = int(parts[3]) if len(parts) > 3 else 0
    sub = await get_subcategory(sub_id)
    if not sub:
        await callback.answer("Topilmadi", show_alert=True)
        return
    await callback.message.edit_text(
        f"📂 <b>{sub['emoji']} {sub['name']}</b>",
        parse_mode="HTML",
        reply_markup=admin_subcategory_actions_kb(sub_id, cat_id)
    )

@router.callback_query(AdminFilter(), F.data.startswith("adm_srv:del_sub:"))
async def adm_del_sub(callback: CallbackQuery):
    parts = callback.data.split(":")
    sub_id = int(parts[3])
    await delete_subcategory(sub_id)
    await callback.answer("✅ O'chirildi!")
    await callback.message.edit_text("✅ Ichki bo'lim o'chirildi.")

@router.callback_query(AdminFilter(), F.data.startswith("adm_srv:add_srv:"))
async def adm_add_srv(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    parent_type = parts[3]
    parent_id = int(parts[4])
    await state.update_data(srv_parent_type=parent_type, srv_parent_id=parent_id)
    await state.set_state(AdminState.add_srv_api_id)
    await callback.message.edit_text(
        "🆔 API xizmat ID sini kiriting\n(masalan: 123):",
        reply_markup=cancel_kb()
    )

@router.message(AdminFilter(), AdminState.add_srv_api_id)
async def got_srv_api_id(message: Message, state: FSMContext):
    try:
        api_id = int(message.text.strip())
    except:
        await message.answer("❌ Raqam kiriting!")
        return
    services, err = await get_api_services()
    srv_info = next((s for s in services if str(s.get('service')) == str(api_id)), None)
    data = await state.get_data()
    if srv_info:
        name = srv_info.get('name', f'Xizmat #{api_id}')
        rate = float(srv_info.get('rate', 0))
        min_q = int(srv_info.get('min', 10))
        max_q = int(srv_info.get('max', 10000))
        if data['srv_parent_type'] == 'sub':
            await add_service(api_id, name, rate, min_q, max_q, subcategory_id=data['srv_parent_id'])
        else:
            await add_service(api_id, name, rate, min_q, max_q, category_id=data['srv_parent_id'])
        await state.clear()
        await message.answer(
            f"✅ Xizmat qo'shildi!\n"
            f"📌 {name}\n"
            f"💰 {rate}\n"
            f"📊 Min: {min_q} | Max: {max_q}"
        )
    else:
        await state.update_data(api_service_id=api_id)
        await state.set_state(AdminState.add_srv_parent)
        await message.answer("⚠️ API dan topilmadi. Xizmat nomini kiriting:")

@router.message(AdminFilter(), AdminState.add_srv_parent)
async def got_srv_name_manual(message: Message, state: FSMContext):
    data = await state.get_data()
    if data['srv_parent_type'] == 'sub':
        await add_service(data['api_service_id'], message.text.strip(), 0, 10, 10000,
                         subcategory_id=data['srv_parent_id'])
    else:
        await add_service(data['api_service_id'], message.text.strip(), 0, 10, 10000,
                         category_id=data['srv_parent_id'])
    await state.clear()
    await message.answer("✅ Xizmat qo'shildi!")

# ============ FOYDALANUVCHI ============
@router.message(AdminFilter(), F.text == "🔍 Foydalanuvchini boshqarish")
async def admin_user_manage(message: Message, state: FSMContext):
    await state.set_state(AdminState.user_search)
    await message.answer("🔍 Foydalanuvchi ID sini kiriting:", reply_markup=cancel_kb())

@router.message(AdminFilter(), AdminState.user_search)
async def search_user(message: Message, state: FSMContext):
    try:
        target_id = int(message.text.strip())
    except:
        await message.answer("❌ To'g'ri ID kiriting!")
        return
    user = await get_user(target_id)
    if not user:
        await message.answer("❌ Foydalanuvchi topilmadi!")
        return
    await state.clear()
    currency = await get_setting('currency') or 'UZS'
    await message.answer(
        f"👤 <b>Foydalanuvchi</b>\n\n"
        f"🆔 ID: <code>{user['user_id']}</code>\n"
        f"👤 Ism: {user['full_name']}\n"
        f"📱 @{user['username'] or 'NA'}\n"
        f"💰 Balans: {user['balance']:,.0f} {currency}\n"
        f"🚫 Ban: {'Ha' if user['is_banned'] else 'Yoq'}\n"
        f"⭐️ VIP: {'Ha' if user['is_vip'] else 'Yoq'}",
        parse_mode="HTML",
        reply_markup=user_manage_kb(target_id, bool(user['is_banned']), bool(user['is_vip']))
    )

@router.callback_query(AdminFilter(), F.data.startswith("usr:ban:"))
async def usr_ban(callback: CallbackQuery):
    uid = int(callback.data.split(":")[2])
    await ban_user(uid, True)
    await callback.answer("✅ Ban qilindi!")

@router.callback_query(AdminFilter(), F.data.startswith("usr:unban:"))
async def usr_unban(callback: CallbackQuery):
    uid = int(callback.data.split(":")[2])
    await ban_user(uid, False)
    await callback.answer("✅ Bandan chiqarildi!")

@router.callback_query(AdminFilter(), F.data.startswith("usr:vip:"))
async def usr_vip(callback: CallbackQuery):
    uid = int(callback.data.split(":")[2])
    await set_user_vip(uid, True)
    await callback.answer("✅ VIP berildi!")

@router.callback_query(AdminFilter(), F.data.startswith("usr:unvip:"))
async def usr_unvip(callback: CallbackQuery):
    uid = int(callback.data.split(":")[2])
    await set_user_vip(uid, False)
    await callback.answer("✅ VIP olindi!")

@router.callback_query(AdminFilter(), F.data.startswith("usr:add_bal:"))
async def usr_add_bal(callback: CallbackQuery, state: FSMContext):
    uid = int(callback.data.split(":")[2])
    await state.update_data(add_bal_user=uid)
    await state.set_state(AdminState.add_balance_amount)
    await callback.message.edit_text("💰 Miqdorni kiriting:", reply_markup=cancel_kb())

@router.message(AdminFilter(), AdminState.add_balance_amount)
async def got_add_balance(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        data = await state.get_data()
        await update_user_balance(data['add_bal_user'], amount)
        await state.clear()
        currency = await get_setting('currency') or 'UZS'
        await message.answer(f"✅ +{amount:,.0f} {currency} qo'shildi!")
        try:
            await message.bot.send_message(
                data['add_bal_user'],
                f"💰 Hisobingizga +{amount:,.0f} {currency} qo'shildi!"
            )
        except:
            pass
    except:
        await message.answer("❌ Raqam kiriting!")

# ============ KANALLAR ============
@router.message(AdminFilter(), F.text == "📢 Kanallar")
async def admin_channels(message: Message):
    channels = await get_channels()
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(
            text=f"🗑 {ch['channel_name']}",
            callback_data=f"del_ch:{ch['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="add_ch")])
    await message.answer(
        "📢 <b>Majburiy kanallar:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@router.callback_query(AdminFilter(), F.data == "add_ch")
async def add_ch_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.add_ch_id)
    await callback.message.edit_text(
        "📢 Kanal ID yoki username kiriting\n(masalan: @mychannel):",
        reply_markup=cancel_kb()
    )

@router.message(AdminFilter(), AdminState.add_ch_id)
async def got_ch_id(message: Message, state: FSMContext):
    await state.update_data(ch_id=message.text.strip())
    await state.set_state(AdminState.add_ch_name)
    await message.answer("Kanal nomini kiriting:")

@router.message(AdminFilter(), AdminState.add_ch_name)
async def got_ch_name(message: Message, state: FSMContext):
    await state.update_data(ch_name=message.text.strip())
    await state.set_state(AdminState.add_ch_link)
    await message.answer("Kanal havolasini kiriting (https://t.me/...):")

@router.message(AdminFilter(), AdminState.add_ch_link)
async def got_ch_link(message: Message, state: FSMContext):
    data = await state.get_data()
    await add_channel(data['ch_id'], data['ch_name'], message.text.strip())
    await state.clear()
    await message.answer(f"✅ '{data['ch_name']}' kanali qo'shildi!")

@router.callback_query(AdminFilter(), F.data.startswith("del_ch:"))
async def del_ch(callback: CallbackQuery):
    ch_id = int(callback.data.split(":")[1])
    await delete_channel(ch_id)
    await callback.answer("✅ O'chirildi!")
    await callback.message.edit_text("✅ Kanal o'chirildi.")

# ============ PROMOKOD ============
@router.message(AdminFilter(), F.text == "🎟 Promokod")
async def admin_promo(message: Message):
    promos = await get_all_promos()
    buttons = [[InlineKeyboardButton(text="➕ Yangi promokod", callback_data="adm_promo:add")]]
    for p in promos:
        status = "✅" if p['is_active'] and p['used_count'] < p['max_uses'] else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {p['code']} | {p['amount']:,.0f} | {p['used_count']}/{p['max_uses']}",
            callback_data=f"adm_promo:del:{p['id']}"
        )])
    await message.answer(
        "🎟 <b>Promokodlar</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@router.callback_query(AdminFilter(), F.data == "adm_promo:add")
async def adm_add_promo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.add_promo_code)
    await callback.message.edit_text("🎟 Promokod matnini kiriting:", reply_markup=cancel_kb())

@router.message(AdminFilter(), AdminState.add_promo_code)
async def got_promo_code(message: Message, state: FSMContext):
    await state.update_data(promo_code=message.text.strip().upper())
    await state.set_state(AdminState.add_promo_amount)
    await message.answer("💰 Miqdorni kiriting:")

@router.message(AdminFilter(), AdminState.add_promo_amount)
async def got_promo_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        await state.update_data(promo_amount=amount)
        await state.set_state(AdminState.add_promo_uses)
        await message.answer("🔢 Necha marta ishlatilsin?")
    except:
        await message.answer("❌ Raqam kiriting!")

@router.message(AdminFilter(), AdminState.add_promo_uses)
async def got_promo_uses(message: Message, state: FSMContext):
    try:
        uses = int(message.text.strip())
        data = await state.get_data()
        await create_promo(data['promo_code'], data['promo_amount'], uses)
        await state.clear()
        currency = await get_setting('currency') or 'UZS'
        await message.answer(
            f"✅ Promokod yaratildi!\n"
            f"🎟 Kod: <code>{data['promo_code']}</code>\n"
            f"💰 {data['promo_amount']:,.0f} {currency}\n"
            f"🔢 {uses} marta",
            parse_mode="HTML"
        )
    except:
        await message.answer("❌ Raqam kiriting!")

@router.callback_query(AdminFilter(), F.data.startswith("adm_promo:del:"))
async def adm_del_promo(callback: CallbackQuery):
    promo_id = int(callback.data.split(":")[2])
    await delete_promo(promo_id)
    await callback.answer("✅ O'chirildi!")
    await callback.message.edit_text("✅ Promokod o'chirildi.")

# ============ XABARNOMA ============
@router.message(AdminFilter(), F.text == "📨 Xabarnoma")
async def admin_broadcast(message: Message, state: FSMContext):
    await state.set_state(AdminState.broadcast_text)
    await message.answer("📨 Xabarni kiriting:", reply_markup=cancel_kb())

@router.message(AdminFilter(), AdminState.broadcast_text)
async def broadcast_send(message: Message, state: FSMContext):
    await state.clear()
    users = await get_all_users()
    sent = 0
    failed = 0
    await message.answer(f"📨 Yuborilmoqda... ({len(users)} ta)")
    for user in users:
        try:
            await message.copy_to(user['user_id'])
            sent += 1
        except:
            failed += 1
    await message.answer(f"✅ Yuborildi!\n✅ {sent} ta\n❌ {failed} ta xato")

# ============ BOT ON/OFF ============
@router.message(AdminFilter(), F.text == "🔄 Botni o'chir/yoq")
async def admin_toggle_bot(message: Message):
    current = await get_setting('bot_active') or '1'
    new_val = '0' if current == '1' else '1'
    await set_setting('bot_active', new_val)
    status = "✅ Yoqildi" if new_val == '1' else "🔴 O'chirildi"
    await message.answer(f"🤖 Bot holati: <b>{status}</b>", parse_mode="HTML")
