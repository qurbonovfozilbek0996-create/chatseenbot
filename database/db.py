import aiosqlite
import logging
from config import DB_PATH

logger = logging.getLogger(__name__)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            balance REAL DEFAULT 0,
            total_deposited REAL DEFAULT 0,
            referral_id INTEGER,
            referral_count INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            is_vip INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            emoji TEXT DEFAULT '📁',
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS subcategories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            emoji TEXT DEFAULT '📂',
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subcategory_id INTEGER,
            category_id INTEGER,
            api_service_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price_per_1000 REAL NOT NULL,
            min_quantity INTEGER DEFAULT 10,
            max_quantity INTEGER DEFAULT 10000,
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            api_service_id INTEGER NOT NULL,
            api_order_id INTEGER,
            link TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            charge REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            start_count INTEGER DEFAULT 0,
            remains INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            payment_details TEXT,
            status TEXT DEFAULT 'pending',
            admin_id INTEGER,
            receipt_file_id TEXT,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confirmed_at TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS payment_methods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            details TEXT NOT NULL,
            emoji TEXT DEFAULT '💳',
            is_active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT
        );
        CREATE TABLE IF NOT EXISTS promo_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            amount REAL NOT NULL,
            max_uses INTEGER DEFAULT 1,
            used_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS promo_uses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            promo_id INTEGER NOT NULL,
            UNIQUE(user_id, promo_id)
        );
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL,
            channel_name TEXT NOT NULL,
            channel_link TEXT,
            is_required INTEGER DEFAULT 1
        );
        INSERT OR IGNORE INTO settings VALUES ('api_url', '');
        INSERT OR IGNORE INTO settings VALUES ('api_key', '');
        INSERT OR IGNORE INTO settings VALUES ('currency', 'UZS');
        INSERT OR IGNORE INTO settings VALUES ('vip_price', '15000');
        INSERT OR IGNORE INTO settings VALUES ('referral_bonus', '100');
        INSERT OR IGNORE INTO settings VALUES ('transfer_fee', '0');
        INSERT OR IGNORE INTO settings VALUES ('bot_active', '1');
        INSERT OR IGNORE INTO settings VALUES ('categories_per_row', '2');
        INSERT OR IGNORE INTO settings VALUES ('subcategories_per_row', '1');
        INSERT OR IGNORE INTO settings VALUES ('services_per_row', '5');
        INSERT OR IGNORE INTO settings VALUES ('payment_per_row', '2');
        INSERT OR IGNORE INTO settings VALUES ('welcome_text', 'Chat Seen Bot ga xush kelibsiz!');
        INSERT OR IGNORE INTO settings VALUES ('min_deposit', '1000');
        """)
        await db.commit()
    logger.info("Database tayyor!")
async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
            return await cur.fetchone()

async def create_user(user_id, username, full_name, referral_id=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name, referral_id) VALUES (?,?,?,?)",
            (user_id, username, full_name, referral_id)
        )
        await db.commit()

async def update_user_balance(user_id, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amount, user_id))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users") as cur:
            return await cur.fetchall()

async def get_user_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            return (await cur.fetchone())[0]

async def ban_user(user_id, banned):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned=? WHERE user_id=?", (1 if banned else 0, user_id))
        await db.commit()

async def set_user_vip(user_id, is_vip):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_vip=? WHERE user_id=?", (1 if is_vip else 0, user_id))
        await db.commit()

async def add_referral_count(referral_id, bonus):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET referral_count=referral_count+1, balance=balance+? WHERE user_id=?",
            (bonus, referral_id)
        )
        await db.commit()

async def get_setting(key):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key=?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else None

async def set_setting(key, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, value))
        await db.commit()

async def is_admin(user_id):
    from config import ADMIN_IDS
    if user_id in ADMIN_IDS:
        return True
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM admins WHERE user_id=?", (user_id,)) as cur:
            return await cur.fetchone() is not None

async def get_admins():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM admins") as cur:
            return await cur.fetchall()

async def add_admin(user_id, username, full_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO admins (user_id,username,full_name) VALUES (?,?,?)",
            (user_id, username, full_name)
        )
        await db.commit()

async def remove_admin(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM admins WHERE user_id=?", (user_id,))
        await db.commit()

async def get_categories(active_only=True):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM categories" + (" WHERE is_active=1" if active_only else "")
        q += " ORDER BY sort_order, id"
        async with db.execute(q) as cur:
            return await cur.fetchall()

async def get_category(cat_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM categories WHERE id=?", (cat_id,)) as cur:
            return await cur.fetchone()

async def add_category(name, emoji='📁'):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("INSERT INTO categories (name,emoji) VALUES (?,?)", (name, emoji))
        await db.commit()
        return cur.lastrowid

async def update_category(cat_id, name, emoji):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE categories SET name=?,emoji=? WHERE id=?", (name, emoji, cat_id))
        await db.commit()

async def toggle_category(cat_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE categories SET is_active=CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE id=?", (cat_id,))
        await db.commit()

async def delete_category(cat_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM categories WHERE id=?", (cat_id,))
        await db.commit()

async def get_subcategories(cat_id, active_only=True):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM subcategories WHERE category_id=?"
        if active_only:
            q += " AND is_active=1"
        q += " ORDER BY sort_order, id"
        async with db.execute(q, (cat_id,)) as cur:
            return await cur.fetchall()

async def get_subcategory(sub_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM subcategories WHERE id=?", (sub_id,)) as cur:
            return await cur.fetchone()

async def add_subcategory(cat_id, name, emoji='📂'):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO subcategories (category_id,name,emoji) VALUES (?,?,?)", (cat_id, name, emoji)
        )
        await db.commit()
        return cur.lastrowid

async def delete_subcategory(sub_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM subcategories WHERE id=?", (sub_id,))
        await db.commit()

async def get_services_by_subcategory(sub_id, active_only=True):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM services WHERE subcategory_id=?"
        if active_only:
            q += " AND is_active=1"
        q += " ORDER BY sort_order, id"
        async with db.execute(q, (sub_id,)) as cur:
            return await cur.fetchall()

async def get_services_by_category(cat_id, active_only=True):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM services WHERE category_id=? AND subcategory_id IS NULL"
        if active_only:
            q += " AND is_active=1"
        q += " ORDER BY sort_order, id"
        async with db.execute(q, (cat_id,)) as cur:
            return await cur.fetchall()

async def get_service(srv_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM services WHERE id=?", (srv_id,)) as cur:
            return await cur.fetchone()

async def add_service(api_service_id, name, price, min_q, max_q, subcategory_id=None, category_id=None, description=''):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO services (api_service_id,name,price_per_1000,min_quantity,max_quantity,subcategory_id,category_id,description) VALUES (?,?,?,?,?,?,?,?)",
            (api_service_id, name, price, min_q, max_q, subcategory_id, category_id, description)
        )
        await db.commit()
        return cur.lastrowid

async def delete_service(srv_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM services WHERE id=?", (srv_id,))
        await db.commit()

async def toggle_service(srv_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE services SET is_active=CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE id=?", (srv_id,))
        await db.commit()

async def create_order(user_id, service_id, api_service_id, link, quantity, charge):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO orders (user_id,service_id,api_service_id,link,quantity,charge) VALUES (?,?,?,?,?,?)",
            (user_id, service_id, api_service_id, link, quantity, charge)
        )
        await db.commit()
        return cur.lastrowid

async def update_order_api_id(order_id, api_order_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET api_order_id=?,status='processing' WHERE id=?", (api_order_id, order_id))
        await db.commit()

async def update_order_status(order_id, status, start_count=0, remains=0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status=?,start_count=?,remains=? WHERE id=?", (status, start_count, remains, order_id))
        await db.commit()

async def get_user_orders(user_id, limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT o.*,s.name as service_name FROM orders o LEFT JOIN services s ON o.service_id=s.id WHERE o.user_id=? ORDER BY o.created_at DESC LIMIT ?",
            (user_id, limit)
        ) as cur:
            return await cur.fetchall()

async def get_pending_orders():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM orders WHERE status IN ('processing','pending') AND api_order_id IS NOT NULL") as cur:
            return await cur.fetchall()

async def get_order_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM orders") as cur:
            return (await cur.fetchone())[0]

async def create_payment(user_id, amount, method, details='', receipt_file_id=None):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO payments (user_id,amount,payment_method,payment_details,receipt_file_id) VALUES (?,?,?,?,?)",
            (user_id, amount, method, details, receipt_file_id)
        )
        await db.commit()
        return cur.lastrowid

async def get_payment(pay_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM payments WHERE id=?", (pay_id,)) as cur:
            return await cur.fetchone()

async def confirm_payment(pay_id, admin_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM payments WHERE id=?", (pay_id,)) as cur:
            pay = await cur.fetchone()
        if not pay or pay[5] != 'pending':
            return False
        await db.execute(
            "UPDATE payments SET status='confirmed',admin_id=?,confirmed_at=CURRENT_TIMESTAMP WHERE id=?",
            (admin_id, pay_id)
        )
        await db.execute(
            "UPDATE users SET balance=balance+?,total_deposited=total_deposited+? WHERE user_id=?",
            (pay[2], pay[2], pay[1])
        )
        await db.commit()
        return pay

async def reject_payment(pay_id, admin_id, comment=''):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM payments WHERE id=?", (pay_id,)) as cur:
            pay = await cur.fetchone()
        if not pay or pay[5] != 'pending':
            return False
        await db.execute(
            "UPDATE payments SET status='rejected',admin_id=?,comment=? WHERE id=?",
            (admin_id, comment, pay_id)
        )
        await db.commit()
        return pay

async def get_payment_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM payments WHERE status='confirmed'") as cur:
            return (await cur.fetchone())[0]

async def get_total_revenue():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT SUM(amount) FROM payments WHERE status='confirmed'") as cur:
            row = await cur.fetchone()
            return row[0] or 0

async def get_payment_methods(active_only=True):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM payment_methods" + (" WHERE is_active=1" if active_only else "")
        async with db.execute(q) as cur:
            return await cur.fetchall()

async def add_payment_method(name, details, emoji='💳'):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO payment_methods (name,details,emoji) VALUES (?,?,?)", (name, details, emoji))
        await db.commit()

async def delete_payment_method(pm_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM payment_methods WHERE id=?", (pm_id,))
        await db.commit()

async def get_promo(code):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM promo_codes WHERE code=? AND is_active=1 AND used_count<max_uses", (code,)
        ) as cur:
            return await cur.fetchone()

async def use_promo(user_id, promo_id):
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("INSERT INTO promo_uses (user_id,promo_id) VALUES (?,?)", (user_id, promo_id))
            await db.execute("UPDATE promo_codes SET used_count=used_count+1 WHERE id=?", (promo_id,))
            await db.commit()
            return True
        except:
            return False

async def create_promo(code, amount, max_uses=1):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO promo_codes (code,amount,max_uses) VALUES (?,?,?)", (code, amount, max_uses))
        await db.commit()

async def get_all_promos():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM promo_codes ORDER BY id DESC") as cur:
            return await cur.fetchall()

async def delete_promo(promo_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM promo_codes WHERE id=?", (promo_id,))
        await db.commit()

async def get_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM channels WHERE is_required=1") as cur:
            return await cur.fetchall()

async def add_channel(channel_id, name, link):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO channels (channel_id,channel_name,channel_link) VALUES (?,?,?)", (channel_id, name, link))
        await db.commit()

async def delete_channel(ch_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channels WHERE id=?", (ch_id,))
        await db.commit()
