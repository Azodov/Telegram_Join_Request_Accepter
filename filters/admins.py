from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from data.config import ADMINS
from loader import db


class IsSuperAdmin(BoundFilter):
    async def check(self, message: types.Message):
        return True


class IsChannelExist(BoundFilter):
    async def check(self, message: types.Message):
        channel = await db.select_channel(id=message['chat']['id'])
        if channel:
            return True
        else:
            return False
