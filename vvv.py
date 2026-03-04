import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from docx import Document
from openpyxl import load_workbook, Workbook
from PyPDF2 import PdfReader
import xlrd

API_TOKEN = "8697966421:AAGqq4JimRDrjP0rswZCZz92U1gYYQtROao"
ADMIN_ID = 8027087107
CHANNEL = "@krilchadan_lotinchaga"

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
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

kiril = {
"а":"a","б":"b","в":"v","г":"g","д":"d","е":"e",
"ё":"yo","ж":"j","з":"z","и":"i","й":"y","к":"k",
"қ":"q","л":"l","м":"m","н":"n","о":"o","п":"p",
"р":"r","с":"s","т":"t","у":"u","ф":"f","х":"x",
"ҳ":"h","ч":"ch","ш":"sh","ю":"yu","я":"ya",
"ғ":"g'","ў":"o'","и":"i","э":"e"
}

latin = {v:k for k,v in kiril.items()}

def kiril_lotin(text):
    for k,v in kiril.items():
        text=text.replace(k,v)
        text=text.replace(k.upper(),v.upper())
    return text

def lotin_kiril(text):
    for k,v in latin.items():
        text=text.replace(k,v)
        text=text.replace(k.upper(),v.upper())
    return text

def convert(text,mode):
    if mode=="kl":
        return kiril_lotin(text)
    else:
        return lotin_kiril(text)

# ================= MENU =================

menu = InlineKeyboardMarkup(
inline_keyboard=[
[InlineKeyboardButton(text="🔤 Kiril → Lotin",callback_data="kl")],
[InlineKeyboardButton(text="🔤 Lotin → Kiril",callback_data="lk")],
[InlineKeyboardButton(text="📊 Statistika",callback_data="stats")]
]
)

admin_menu = InlineKeyboardMarkup(
inline_keyboard=[
[InlineKeyboardButton(text="📊 Statistika",callback_data="admin_stats")],
[InlineKeyboardButton(text="👥 Users",callback_data="admin_users")],
[InlineKeyboardButton(text="📢 Broadcast",callback_data="admin_broadcast")]
]
)

user_mode = {}

# ================= START =================

@dp.message(CommandStart())
async def start(message: types.Message):

    user_id = message.from_user.id
    save_user(user_id)

    member = await bot.get_chat_member(CHANNEL,user_id)

    if member.status not in ["member","administrator","creator"]:

        btn = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📢 Kanalga o'tish",url=f"https://t.me/{CHANNEL.replace('@','')}")]
            ]
        )

        await message.answer(
            "Botdan foydalanish uchun kanalga obuna bo‘ling",
            reply_markup=btn
        )
        return

    await message.answer(
        "Assalomu alaykum 👋\n\n"
        "Transliteratsiya bot\n"
        "Matn yoki fayl yuboring",
        reply_markup=menu
    )

# ================= CALLBACK =================

@dp.callback_query()
async def callback(call: types.CallbackQuery):

    if call.data=="kl":
        user_mode[call.from_user.id]="kl"
        await call.message.answer("Kiril matn yoki fayl yuboring.")

    elif call.data=="lk":
        user_mode[call.from_user.id]="lk"
        await call.message.answer("Lotin matn yoki fayl yuboring.")

    elif call.data=="stats":

        users = get_users()

        await call.message.answer(
            f"👥 Foydalanuvchilar soni: {len(users)}"
        )

# ================= ADMIN PANEL =================

@dp.message(lambda message: message.text=="/admin")
async def admin_panel(message: types.Message):

    if message.from_user.id!=ADMIN_ID:
        return

    await message.answer(
        "⚙️ Admin panel",
        reply_markup=admin_menu
    )

@dp.callback_query(lambda c: c.data.startswith("admin"))
async def admin_callbacks(call: types.CallbackQuery):

    if call.from_user.id!=ADMIN_ID:
        return

    if call.data=="admin_stats":

        users = get_users()

        await call.message.answer(
            f"👥 Foydalanuvchilar: {len(users)}"
        )

    elif call.data=="admin_users":

        users = get_users()

        text="\n".join(str(u) for u in users)

        with open("users_list.txt","w") as f:
            f.write(text)

        await call.message.answer_document(types.FSInputFile("users_list.txt"))

    elif call.data=="admin_broadcast":

        await call.message.answer(
            "Xabar yuborish uchun:\n\n/send matn"
        )

# ================= BROADCAST =================

@dp.message(lambda m: m.text and m.text.startswith("/send"))
async def broadcast(message: types.Message):

    if message.from_user.id!=ADMIN_ID:
        return

    text = message.text.replace("/send ","")

    users = get_users()

    for user in users:
        try:
            await bot.send_message(user,text)
        except:
            pass

    await message.answer("Xabar yuborildi.")

# ================= FILE =================

@dp.message(lambda msg: msg.document)
async def file_handler(message: types.Message):

    user_id = message.from_user.id
    mode = user_mode.get(user_id,"kl")

    file_id = message.document.file_id
    file_name = message.document.file_name

    await message.answer("Fayl qabul qilindi...")

    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path,file_name)

    ext = file_name.split(".")[-1].lower()

# TXT

    if ext=="txt":

        with open(file_name,"r",encoding="utf-8",errors="ignore") as f:
            text=f.read()

        result = convert(text,mode)

        with open("result.txt","w",encoding="utf-8") as f:
            f.write(result)

        await message.answer_document(types.FSInputFile("result.txt"))

# WORD

    elif ext=="docx":

        doc = Document(file_name)

        for p in doc.paragraphs:
            p.text = convert(p.text,mode)

        doc.save("result.docx")

        await message.answer_document(types.FSInputFile("result.docx"))

# EXCEL

    elif ext in ["xlsx","xlsm"]:

        wb = load_workbook(file_name)

        for sheet in wb.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    if isinstance(cell.value,str):
                        cell.value = convert(cell.value,mode)

        wb.save("result.xlsx")

        await message.answer_document(types.FSInputFile("result.xlsx"))

# XLS

    elif ext=="xls":

        book = xlrd.open_workbook(file_name)

        new_wb = Workbook()
        sheet = new_wb.active

        row_i=1

        for sh in book.sheets():
            for r in range(sh.nrows):

                col_i=1

                for c in range(sh.ncols):

                    value = sh.cell_value(r,c)

                    if isinstance(value,str):
                        value = convert(value,mode)

                    sheet.cell(row=row_i,column=col_i,value=value)

                    col_i+=1

                row_i+=1

        new_wb.save("result.xlsx")

        await message.answer_document(types.FSInputFile("result.xlsx"))

# PDF

    elif ext=="pdf":

        reader = PdfReader(file_name)

        text=""

        for page in reader.pages:
            text+=page.extract_text() or ""

        result = convert(text,mode)

        with open("result.txt","w",encoding="utf-8") as f:
            f.write(result)

        await message.answer_document(types.FSInputFile("result.txt"))

# ================= TEXT =================

@dp.message()
async def text_handler(message: types.Message):

    user_id = message.from_user.id
    mode = user_mode.get(user_id,"kl")

    result = convert(message.text,mode)

    await message.answer(result)

# ================= RUN =================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

