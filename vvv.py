import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup

from docx import Document
from openpyxl import load_workbook
from PyPDF2 import PdfReader

API_TOKEN = "8674624753:AAHKQI_Cn6QenQdFNtenjDTH0USLoHT_dAA"

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

mode = {}

# ======================
# Transliteration
# ======================

def kirill_lotin(text):
    mapping = {
        "А":"A","а":"a","Б":"B","б":"b","В":"V","в":"v",
        "Г":"G","г":"g","Д":"D","д":"d","Е":"E","е":"e",
        "Ё":"Yo","ё":"yo","Ж":"J","ж":"j","З":"Z","з":"z",
        "И":"I","и":"i","Й":"Y","й":"y","К":"K","к":"k",
        "Л":"L","л":"l","М":"M","м":"m","Н":"N","н":"n",
        "О":"O","о":"o","П":"P","п":"p","Р":"R","р":"r",
        "С":"S","с":"s","Т":"T","т":"t","У":"U","у":"u",
        "Ф":"F","ф":"f","Х":"X","х":"x","Ч":"Ch","ч":"ch",
        "Ш":"Sh","ш":"sh","Ю":"Yu","ю":"yu","Я":"Ya","я":"ya",
        "Қ":"Q","қ":"q","Ғ":"G‘","ғ":"g‘","Ҳ":"H","ҳ":"h",
        "Ў":"O‘","ў":"o‘"
    }

    for k,v in mapping.items():
        text=text.replace(k,v)
    return text


def lotin_kirill(text):
    mapping = {
        "Sh":"Ш","sh":"ш","Ch":"Ч","ch":"ч","Ya":"Я","ya":"я",
        "Yu":"Ю","yu":"ю","Yo":"Ё","yo":"ё","O‘":"Ў","o‘":"ў",
        "G‘":"Ғ","g‘":"ғ","Q":"Қ","q":"қ"
    }

    for k,v in mapping.items():
        text=text.replace(k,v)
    return text


# ======================
# START
# ======================

@dp.message(CommandStart())
async def start(message: types.Message):

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔤 Kirill → Lotin", callback_data="k_l")],
        [InlineKeyboardButton(text="🔡 Lotin → Kirill", callback_data="l_k")]
    ])

    await message.answer("Transliteratsiya turini tanlang 👇", reply_markup=kb)


# ======================
# BUTTON HANDLER
# ======================

@dp.callback_query()
async def callback(call: types.CallbackQuery):

    if call.data=="k_l":
        mode[call.from_user.id]="k_l"
        await call.message.answer("📂 Fayl yuboring")

    if call.data=="l_k":
        mode[call.from_user.id]="l_k"
        await call.message.answer("📂 Fayl yuboring")

    await call.answer()


# ======================
# FILE HANDLER
# ======================

@dp.message(lambda msg: msg.document)
async def file_handler(message: types.Message):

    user_mode = mode.get(message.from_user.id)

    file = await bot.get_file(message.document.file_id)
    path = file.file_path

    filename = message.document.file_name
    await bot.download_file(path, filename)

    ext = filename.split(".")[-1]

    await message.answer("⏳ Fayl qayta ishlanyapti...")

    if ext=="txt":

        with open(filename,"r",encoding="utf-8",errors="ignore") as f:
            text=f.read()

        if user_mode=="k_l":
            result=kirill_lotin(text)
        else:
            result=lotin_kirill(text)

        out="result.txt"

        with open(out,"w",encoding="utf-8") as f:
            f.write(result)


    elif ext=="docx":

        doc=Document(filename)

        for p in doc.paragraphs:

            if user_mode=="k_l":
                p.text=kirill_lotin(p.text)
            else:
                p.text=lotin_kirill(p.text)

        out="result.docx"
        doc.save(out)


    elif ext=="xlsx":

        wb=load_workbook(filename)

        for sheet in wb.worksheets:
            for row in sheet.iter_rows():
                for cell in row:

                    if isinstance(cell.value,str):

                        if user_mode=="k_l":
                            cell.value=kirill_lotin(cell.value)
                        else:
                            cell.value=lotin_kirill(cell.value)

        out="result.xlsx"
        wb.save(out)


    elif ext=="pdf":

        reader=PdfReader(filename)

        text=""

        for page in reader.pages:
            text+=page.extract_text()

        if user_mode=="k_l":
            result=kirill_lotin(text)
        else:
            result=lotin_kirill(text)

        out="result.txt"

        with open(out,"w",encoding="utf-8") as f:
            f.write(result)

    else:
        await message.answer("❌ Bu format qo‘llab-quvvatlanmaydi")
        return


    await message.answer_document(FSInputFile(out),"✅ Tayyor")


# ======================
# RUN
# ======================

async def main():
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
