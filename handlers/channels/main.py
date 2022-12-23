import asyncio

from aiogram import types, exceptions
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from filters import IsSuperAdmin, IsChannelExist
from loader import dp, bot, db


@dp.message_handler(IsSuperAdmin(), commands=['start'], state='*')
async def bot_start(message: types.Message, state: FSMContext):
    await state.finish()
    channels_btn = InlineKeyboardMarkup(row_width=1)
    channels = await db.select_channel(added_by=message.from_user.id)
    bot_username = (await bot.me).username
    if channels:
        for channel in channels:
            channels_btn.add(InlineKeyboardButton(text=channel['name'], callback_data=f"channel_{channel['id']}"))
        channels_btn.add(
            InlineKeyboardButton(text="➕ Guruhga qo'shish", url=f"https://t.me/{bot_username}?startgroup=new"))
        channels_btn.add(InlineKeyboardButton(text="♻️ Tekshirish", callback_data="check"))
        await message.answer('Sizning kanallaringiz:', reply_markup=channels_btn)

    else:
        channels_btn.add(InlineKeyboardButton(text="➕ Guruhga qo'shish",
                                              url=f"https://t.me/{bot_username}?startgroup=new"))

        channels_btn.add(InlineKeyboardButton(text="♻️ Tekshirish", callback_data="check"))
        await message.answer("Sizda hech qanday kanal yo'q istasangiz qo'shishingiz mumkin", reply_markup=channels_btn)


@dp.callback_query_handler(IsSuperAdmin(), text='check', state='*')
async def check_channels(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup()
    await call.message.answer("Kanaldan istalgan xabarni forward qilib yuboring...")
    await state.set_state("check")


@dp.message_handler(state="check", content_types=types.ContentTypes.ANY)
async def check_message(message: types.Message, state: FSMContext):
    try:
        bot_chat_id = (await bot.me).id
        status = await bot.get_chat_member(message.forward_from_chat.id, bot_chat_id)
        channel_name = message.forward_from_chat.full_name
        if status.status == "administrator":
            await message.answer("Kanal admin qilindi")
            await message.answer("Foydalanuvchini qancha kechikish bilan qabul qilishni xohlaysiz?\n"
                                 "Masalan: 10\n"
                                 "Buyerda 10 soniyada korsatiladi")
            await state.update_data(chat_id=message.forward_from_chat.id,
                                    channel_name=channel_name)
            await state.set_state("set_time")
        else:
            await message.answer("Kanal admin emas")
            await state.set_state(None)
            return
    except exceptions.Unauthorized:
        await message.answer("Bot Kanal yoki guruhga qo'shilmagan")
        await state.finish()
        return
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi {e}")
        await state.finish()
        return


@dp.message_handler(state="set_time")
async def set_time(message: types.Message, state: FSMContext):
    try:
        time_sleep = int(message.text)
        await state.update_data(time=time_sleep)
    except ValueError:
        await message.answer("Son kiriting")
        return
    await message.answer("Salomlashish xabarini kiriting")
    await state.set_state("set_text")


@dp.message_handler(state="set_text")
async def set_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    channel_name = data.get("channel_name")
    time_sleep = data.get("time")
    text = message.text
    try:
        await db.add_channel(id=chat_id, name=channel_name, sleep_time=time_sleep, added_by=message.from_user.id, hello_message=text)
        await message.answer("✅ Kanal qo'shildi")
        link = await bot.create_chat_invite_link(chat_id=chat_id, creates_join_request=True)
        link = link.invite_link
        await message.answer(f"Kanalga kirish uchun link: {link}")
    except Exception as e:
        await message.answer(f"Bu kanal allaqachon qo'shilgan")
    await state.finish()
    user_id = message.from_user.id
    message.from_user.id = user_id
    await bot_start(message, state)


@dp.callback_query_handler(IsSuperAdmin(), text_contains='channel_', state='*')
async def channel_settings(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup()
    channel_id = call.data.split('_')[1]
    channel = await db.select_channel(id=int(channel_id))
    channel = channel[0]

    channel_btn = InlineKeyboardMarkup(row_width=1)
    if channel['auto_approve']:

        channel_btn.add(InlineKeyboardButton(text="❌ Avtomatik tasdiqlashni o'chirish",
                                             callback_data=f"enable_auto_approve_{channel_id}"))
    else:
        channel_btn.add(InlineKeyboardButton(text="✅ Avtomatik tasdiqlashni yoqish",
                                             callback_data=f"enable_auto_approve_{channel_id}"))
    channel_btn.add(InlineKeyboardButton(text="✍️ Salomlashish xabarini o'zgartirish",
                                         callback_data=f"change_hello_message_{channel_id}"))
    channel_btn.add(InlineKeyboardButton(text="⏱ Qabul qilishdagi kechikishni o'zgartirish",
                                         callback_data=f"change_sleep_time_{channel_id}"))
    channel_btn.add(InlineKeyboardButton(text="🗑 Kanalni o'chirish",
                                         callback_data=f"delete_{channel_id}"))
    channel_btn.add(InlineKeyboardButton(text="🔙 Orqaga",
                                         callback_data="back"))

    auto_approve = "✅ Yoqilgan" if channel['auto_approve'] else "❌O'chirilgan"

    await call.message.answer(f"📣 Kanal: {channel['name']}\n"
                              f"⏱ Qabul qilishdagi kechikish: {channel['sleep_time']} sekund\n"
                              f"🔔 Salomlashish xabari: {channel['hello_message']}\n"
                              f"🔎 Avtomatik tasdiqlash: {auto_approve}", reply_markup=channel_btn)

    channel_btn.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="back"))
    await state.finish()


@dp.callback_query_handler(IsSuperAdmin(), text_contains='enable_auto_approve_', state='*')
async def enable_auto_approve(call: types.CallbackQuery, state: FSMContext):
    channel_id = int(call.data.split('_')[-1])
    channel = await db.select_channel(id=channel_id)
    channel = channel[0]
    if channel['auto_approve']:
        await db.update_channel(id=channel_id, auto_approve=False)
        await call.message.answer("✅ Avtomatik tasdiqlash o'chirildi")
    else:
        await db.update_channel(id=channel_id, auto_approve=True)
        await call.message.answer("✅ Avtomatik tasdiqlash yoqildi")

    call.data = f"channel_{channel_id}"
    await channel_settings(call, state)


@dp.callback_query_handler(IsSuperAdmin(), text_contains='change_hello_message_', state='*')
async def change_hello_message(call: types.CallbackQuery, state: FSMContext):
    channel_id = int(call.data.split('_')[-1])
    await call.message.answer("Salomlashish xabarini kiriting")
    await state.update_data(channel_id=channel_id)
    await state.set_state("change_hello_message")


@dp.message_handler(state="change_hello_message")
async def change_hello_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    channel_id = data.get("channel_id")
    await db.update_channel(id=channel_id, hello_message=message.text)
    await message.answer("✅ Salomlashish xabari o'zgartirildi")
    await state.finish()
    user_id = message.from_user.id
    message.from_user.id = user_id
    await bot_start(message, state)


@dp.callback_query_handler(IsSuperAdmin(), text_contains='change_sleep_time_', state='*')
async def change_sleep_time(call: types.CallbackQuery, state: FSMContext):
    channel_id = call.data.split('_')[-1]
    await call.message.answer("Qabul qilishdagi kechikishni kiriting")
    await state.update_data(channel_id=channel_id)
    await state.set_state("change_sleep_time")


@dp.message_handler(state="change_sleep_time")
async def change_sleep_time(message: types.Message, state: FSMContext):
    data = await state.get_data()
    channel_id = int(data.get("channel_id"))
    await db.update_channel(id=channel_id, sleep_time=int(message.text))
    await message.answer("✅ Qabul qilishdagi kechikish o'zgartirildi")
    await state.finish()
    user_id = message.from_user.id
    message.from_user.id = user_id
    await bot_start(message, state)


@dp.callback_query_handler(IsSuperAdmin(), text_contains='delete_', state='*')
async def delete_channel(call: types.CallbackQuery, state: FSMContext):
    channel_id = int(call.data.split('_')[-1])
    await db.delete_channel(id=channel_id)
    await call.message.answer("✅ Kanal o'chirildi")
    await state.finish()
    user_id = call.from_user.id
    message = call.message
    message.from_user.id = user_id
    await bot_start(message, state)


@dp.chat_join_request_handler(IsChannelExist())
async def join_request(message: types.ChatInviteLink, state: FSMContext):
    user_id = message['from']['id']
    user_full_name = message['from']['first_name']
    try:
        data = await db.select_channel(id=message['chat']['id'])
        data = data[0]
        if data:
            if data['auto_approve']:
                await asyncio.sleep(data['sleep_time'])
                await bot.approve_chat_join_request(chat_id=message['chat']['id'], user_id=message['from']['id'])
                print("✅ Kanalga qo'shildi")
                if data['hello_message']:
                    try:
                        await bot.send_message(chat_id=message['from']['id'], text=data['hello_message'])
                        print("✅ Salomlashish xabari yuborildi")
                    except Exception as e:
                        print(e)
                        print(f"❌ Salomlashish xabari yuborilmadi{e}")
                        pass
                    try:
                        await asyncio.sleep(3)
                        await db.add_user(id=user_id, full_name=user_full_name, joined_channel_id=message['chat']['id'])
                    except Exception as e:
                        if e.args[0] == 'повторяющееся значение ключа нарушает ограничение уникальности "users_id_key"':
                            pass
                        else:
                            print(f"❌ Foydalanuvchi bazaga qo'shilmadi {e}")
                            pass
            else:
                try:
                    await bot.send_message(chat_id=message['from']['id'],
                                           text="Kanalga kirish uchun adminlar tomonidan tasdiqlash kerak")
                    print("✅ Tasdiqlash xabari yuborildi")
                except Exception as e:
                    print(f"❌ Tasdiqlash xabari yuborilmadi{e}")
                    pass
        else:
            try:
                await bot.send_message(chat_id=message['from']['id'],
                                       text="Kanalga kirish uchun adminlar tomonidan tasdiqlash kerak")
                print("✅ Tasdiqlash xabari yuborildi")
            except Exception as e:
                print(f"❌ Tasdiqlash xabari yuborilmadi {e}")
                pass
    except Exception as e:
        print(e)


@dp.callback_query_handler(IsSuperAdmin(), text='back', state='*')
async def back(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    user_id = call.from_user.id
    message = call.message
    message.from_user.id = user_id
    await state.set_state(None)
    await bot_start(message, state)


@dp.message_handler(commands=['start'], state='*')
async def bot_start_guest(message: types.Message, state: FSMContext):
    await message.answer("Assalom alaykum")
