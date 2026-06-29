from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.db import (
    get_user, get_payment_methods, create_payment,
    confirm_payment, reject_payment, get_setting,
    is_admin, get_admins
)
from utils.keyboards import payment_methods_kb, cancel_kb, payment_confirm_kb
from config import ADMIN_IDS

router = Router()

class PaymentState(StatesGroup):
    choosing_method = State()
    entering_amount = State()
    uploading_receipt = State()

@router.message(F.text == "💰 Hisob to'ldirish")
async def deposit_start(message: Message):
    methods = await get_payment_methods()
    if not methods:
        await message.answer("❌ Hozircha to'lov tizimlari mavjud emas.")
        return
    kb = await payment_methods_kb()
    await message.answer("💳 To'lov usulini tanlang:", reply_markup=kb)

@router.callback_query(F.data.startswith("pay_method:"))
async def payment_method_selected(callback: CallbackQuery, state: FSMContext):
    method_id = int(callback.data.split(":")[1])
    methods = await get_payment_methods()
    method = next((m for m in methods if m['id'] == method_id), None)
    if not method:
        await callback.answer("❌ Topilmadi", show_alert=True)
        return

    currency = await get_setting('currency') or 'UZS'
    min_dep = await get_setting('min_deposit') or '1000'

    await state.update_data(
        method_id=method_id,
        method_name=method['name'],
        method_details=method['details']
    )
    await state.set_state(PaymentState.entering_amount)

    text = (
        f"💳 <b>{method['emoji']} {method['name']}</b>\n\n"
        f"📋 Rekvizit:\n<code>{method['details']}</code>\n\n"
        f"💰 Minimal: {min_dep} {currency}\n\n"
        f"Qancha to'ldirmoqchisiz?"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=cancel_kb())

@router.message(PaymentState.entering_amount)
async def payment_amount_entered(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(',', ''))
    except:
        await message.answer("❌ To'g'ri raqam kiriting!")
        return

    min_dep = float(await get_setting('min_deposit') or '1000')
    currency = await get_setting('currency') or 'UZS'

    if amount < min_dep:
        await message.answer(f"❌ Minimal miqdor: {min_dep:,.0f} {currency}")
        return

    await state.update_data(amount=amount)
    await state.set_state(PaymentState.uploading_receipt)
    data = await state.get_data()

    await message.answer(
        f"✅ Miqdor: <b>{amount:,.0f} {currency}</b>\n\n"
        f"📸 {data['method_name']} orqali to'lov qiling va chek rasmini yuboring:",
        parse_mode="HTML",
        reply_markup=cancel_kb()
    )

@router.message(PaymentState.uploading_receipt, F.photo)
async def receipt_uploaded(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    receipt_file_id = message.photo[-1].file_id
    currency = await get_setting('currency') or 'UZS'

    pay_id = await create_payment(
        message.from_user.id,
        data['amount'],
        data['method_name'],
        data.get('method_details', ''),
        receipt_file_id
    )

    user = await get_user(message.from_user.id)
    await state.clear()

    await message.answer(
        f"✅ <b>To'lov so'rovi yuborildi!</b>\n\n"
        f"🆔 To'lov ID: #{pay_id}\n"
        f"💰 Miqdor: {data['amount']:,.0f} {currency}\n"
        f"💳 Usul: {data['method_name']}\n\n"
        f"⏳ Admin tasdiqlashi kutilmoqda...",
        parse_mode="HTML"
    )

    admin_text = (
        f"💰 <b>Yangi to'lov so'rovi!</b>\n\n"
        f"🆔 To'lov ID: #{pay_id}\n"
        f"👤 {user['full_name']} (@{user['username'] or 'NA'})\n"
        f"🪪 ID: <code>{message.from_user.id}</code>\n"
        f"💰 Miqdor: {data['amount']:,.0f} {currency}\n"
        f"💳 Usul: {data['method_name']}"
    )

    all_admins = list(ADMIN_IDS)
    try:
        db_admins = await get_admins()
        for a in db_admins:
            all_admins.append(a['user_id'])
    except:
        pass

    for admin_id in set(all_admins):
        try:
            await bot.send_photo(
                admin_id,
                photo=receipt_file_id,
                caption=admin_text,
                parse_mode="HTML",
                reply_markup=payment_confirm_kb(pay_id)
            )
        except:
            pass

@router.message(PaymentState.uploading_receipt)
async def receipt_not_photo(message: Message):
    await message.answer("❌ Iltimos, to'lov cheki rasmini yuboring!")

@router.callback_query(F.data.startswith("pay_ok:"))
async def admin_confirm_payment(callback: CallbackQuery, bot):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    pay_id = int(callback.data.split(":")[1])
    pay = await confirm_payment(pay_id, callback.from_user.id)

    if not pay:
        await callback.answer("❌ Allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    currency = await get_setting('currency') or 'UZS'
    await callback.message.edit_caption(
        callback.message.caption + f"\n\n✅ TASDIQLANDI - @{callback.from_user.username or callback.from_user.id}",
        parse_mode="HTML"
    )

    try:
        await bot.send_message(
            pay[1],
            f"✅ <b>To'lovingiz tasdiqlandi!</b>\n\n"
            f"💰 +{pay[2]:,.0f} {currency} hisobingizga tushdi!\n"
            f"🆔 To'lov #{pay_id}",
            parse_mode="HTML"
        )
    except:
        pass

    await callback.answer("✅ Tasdiqlandi!")

@router.callback_query(F.data.startswith("pay_no:"))
async def admin_reject_payment(callback: CallbackQuery, bot):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    pay_id = int(callback.data.split(":")[1])
    pay = await reject_payment(pay_id, callback.from_user.id)

    if not pay:
        await callback.answer("❌ Allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    currency = await get_setting('currency') or 'UZS'
    await callback.message.edit_caption(
        callback.message.caption + f"\n\n❌ RAD ETILDI - @{callback.from_user.username or callback.from_user.id}",
        parse_mode="HTML"
    )

    try:
        await bot.send_message(
            pay[1],
            f"❌ <b>To'lovingiz rad etildi.</b>\n\n"
            f"💰 Miqdor: {pay[2]:,.0f} {currency}\n"
            f"🆔 To'lov #{pay_id}",
            parse_mode="HTML"
        )
    except:
        pass

    await callback.answer("❌ Rad etildi!")
