import aiohttp
import logging
from database.db import get_setting

logger = logging.getLogger(__name__)

async def api_request(action, params=None):
    api_url = await get_setting('api_url')
    api_key = await get_setting('api_key')
    
    if not api_url or not api_key:
        return None, "API sozlanmagan"
    
    data = {"key": api_key, "action": action}
    if params:
        data.update(params)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, data=data, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                result = await resp.json()
                if isinstance(result, dict) and 'error' in result:
                    return None, result['error']
                return result, None
    except Exception as e:
        logger.error(f"API xato: {e}")
        return None, str(e)

async def get_api_balance():
    result, err = await api_request("balance")
    if err:
        return None, err
    return result.get('balance', 0), None

async def get_api_services():
    result, err = await api_request("services")
    if err:
        return [], err
    return result if isinstance(result, list) else [], None

async def place_order(service_id, link, quantity):
    result, err = await api_request("add", {
        "service": service_id,
        "link": link,
        "quantity": quantity
    })
    if err:
        return None, err
    return result.get('order'), None

async def check_order_status(api_order_id):
    result, err = await api_request("status", {"order": api_order_id})
    if err:
        return None, err
    return result, None
