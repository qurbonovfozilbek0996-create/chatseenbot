from aiogram import Router
import asyncio
import logging

from database.db import get_pending_orders, update_order_status, get_setting
from utils.api import check_order_status

router = Router()
logger = logging.getLogger(__name__)

async def update_orders_loop(bot):
    while True:
        try:
            bot_active = await get_setting('bot_active')
            if bot_active == '1':
                orders = await get_pending_orders()
                for order in orders:
                    if not order['api_order_id']:
                        continue
                    result, err = await check_order_status(order['api_order_id'])
                    if err or not result:
                        continue
                    status = result.get('status', '').lower()
                    start_count = int(result.get('start_count', 0) or 0)
                    remains = int(result.get('remains', 0) or 0)
                    status_map = {
                        'completed': 'completed',
                        'partial': 'partial',
                        'canceled': 'canceled',
                        'cancelled': 'canceled',
                        'processing': 'processing',
                        'in progress': 'processing',
                        'pending': 'pending',
                    }
                    new_status = status_map.get(status, status)
                    if new_status != order['status']:
                        await update_order_status(
                            order['id'], new_status, start_count, remains
                        )
                        if new_status in ('completed', 'partial', 'canceled'):
                            text_map = {
                                'completed': '✅ Buyurtma bajarildi!',
                                'partial': '⚠️ Buyurtma qisman bajarildi.',
                                'canceled': '❌ Buyurtma bekor qilindi.',
                            }
                            try:
                                await bot.send_message(
                                    order['user_id'],
                                    f"{text_map[new_status]}\n\n"
                                    f"🆔 #{order['id']}\n"
                                    f"📊 {order['quantity']:,} ta\n"
                                    f"📈 Start: {start_count:,} | Qoldi: {remains:,}"
                                )
                            except:
                                pass
                    await asyncio.sleep(0.3)
        except Exception as e:
            logger.error(f"Order check xato: {e}")
        await asyncio.sleep(300)
