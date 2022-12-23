from aiogram import executor

from loader import dp, db
import middlewares, filters, handlers
from utils.notify_admins import on_startup_notify
from utils.set_bot_commands import set_default_commands


async def on_startup(dispatcher):
    try:
        await db.create()
        await db.create_table_users()
        await db.create_table_channels()
        # await db.add_channel(id=int(-1001626261133), name="TashTrend⛔", sleep_time=1, added_by=1680443577, hello_message="Salom!")
        # await db.add_channel(id=int(-1001541001488), name="🌹TUNGI CHAT🌹", sleep_time=1, added_by=1680443577, hello_message="Salom!")
        # await db.add_channel(id=int(-1001640829813), name="Real Amlar", sleep_time=1, added_by=1680443577, hello_message="Salom!")
    except Exception as err:
        print(err)

    # Birlamchi komandalar (/star va /help)
    await set_default_commands(dispatcher)

    # Bot ishga tushgani haqida adminga xabar berish
    # await on_startup_notify(dispatcher)


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)