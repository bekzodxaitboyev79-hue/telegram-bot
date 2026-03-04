import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from docx import Document
from openpyxl import load_workbook
from PyPDF2 import PdfReader

API_TOKEN = "8674624753:AAHKQI_Cn6QenQdFNtenjDTH0USLoHT_dAA"
ADMIN_ID = 8027087107
CHANNEL = "@krilchadan_lotinchaga"

bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# ================= USERS =================

def get_users():
    try:
        with open("users.txt","r") as f:
            return set(int(x.strip()) for x in f.readlines())
    except:
        return set()

def save_user(user_id):
    users = get_users()
    if user_id not in users:
        with open("users.txt","a") as f:
            f.write(str(user_id)+"\n")

# ================= TRANSLITERATION =================

def kiril_lotin(text):

    mapping = {
        "а":"a","б":"b","в":"v","г":"g","д":"d","е":"e",
        "ё":"yo","ж":"j","з":"z","и":"i","й":"y","к":"k",
        "л":"l","м":"m","н":"n","о":"o","п":"p","р":"r",
        "с":"s","т":"t","у":"u","ф":"f","х":"x","ч":"ch",
        "ш":"sh","ю":"yu","я":"ya"
    }

    for k,v in mapping.items():
        text=text.replace(k,v)

    return text

# ================= MENU =================

menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika",callback_data="stats")],
        [InlineKeyboardButton(text="ℹ️ Yordam",callback_data="help")]
    ]
)

# ================= START =================

@dp.message(CommandStart())
async def start(message: types.Message):

    user_id = message.from_user.id
    save_user(user_id)

    member = await bot.get_chat_member(CHANNEL,user_id)

    if member.status=="left":
        await message.answer(
            f"Botdan foydalanish uchun kanalga obuna bo‘ling\n\n{CHANNEL}"
        )
        return

    await message.answer(
        "Salom 👋\n\n"
        "Kiril ↔ Lotin transliteratsiya bot.\n"
        "Matn yoki fayl yuboring.",
        reply_markup=menu
    )

# ================= CALLBACK =================

@dp.callback_query()
async def callback(call: types.CallbackQuery):

    if call.data=="stats":

        users = get_users()

        await call.message.answer(
            f"👥 Foydalanuvchilar soni: {len(users)}"
        )

    elif call.data=="help":

        await call.message.answer(
            "Matn yoki fayl yuboring.\n\n"
            "Bot kiril yozuvini lotinga o‘giradi."
        )

# ================= BROADCAST =================

@dp.message(lambda message: message.text.startswith("/send"))
async def broadcast(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.replace("/send ","")

    users = get_users()

    for user in users:
        try:
            await bot.send_message(user,text)
        except:
            pass

    await message.answer("Xabar yuborildi.")

# ================= FILES =================

@dp.message(lambda msg: msg.document)
async def file_handler(message: types.Message):

    file_id = message.document.file_id
    file_name = message.document.file_name

    await message.answer("Fayl qabul qilindi...")

    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path,file_name)

    ext = file_name.split(".")[-1]

    if ext=="txt":

        with open(file_name,"r",encoding="utf-8",errors="ignore") as f:
            text=f.read()

        result=kiril_lotin(text)

        with open("result.txt","w",encoding="utf-8") as f:
            f.write(result)

        await message.answer_document(types.FSInputFile("result.txt"))

    elif ext=="docx":

        doc=Document(file_name)

        for p in doc.paragraphs:
            p.text=kiril_lotin(p.text)

        doc.save("result.docx")

        await message.answer_document(types.FSInputFile("result.docx"))

    elif ext=="xlsx":

        wb=load_workbook(file_name)

        for sheet in wb.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    if isinstance(cell.value,str):
                        cell.value=kiril_lotin(cell.value)

        wb.save("result.xlsx")

        await message.answer_document(types.FSInputFile("result.xlsx"))

    elif ext=="pdf":

        reader=PdfReader(file_name)

        text=""

        for page in reader.pages:
            text+=page.extract_text()

        result=kiril_lotin(text)

        with open("result.txt","w",encoding="utf-8") as f:
            f.write(result)

        await message.answer_document(types.FSInputFile("result.txt"))

# ================= TEXT =================

@dp.message()
async def all_messages(message: types.Message):

    user = message.from_user

    save_user(user.id)

    await bot.send_message(
        ADMIN_ID,
        f"👤 Yangi xabar\n\n"
        f"Ism: {user.first_name}\n"
        f"Username: @{user.username}\n"
        f"ID: {user.id}\n"
        f"Xabar: {message.text}"
    )

    result = kiril_lotin(message.text.lower())

    await message.answer(result)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
