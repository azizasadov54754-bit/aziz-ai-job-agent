from aiogram import Bot,Dispatcher,F,Router
from aiogram.filters import CommandStart
from aiogram.types import Message,CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select,desc
from .config import settings
from .db import SessionLocal
from .models import Job,Application,Message as DBMessage
router=Router()
def menu():
 b=InlineKeyboardBuilder();items=[('💼 Bugungi vakansiyalar','jobs'),('🔥 Top moslik','top'),('🛠 IT xizmatlar','services'),('📨 Arizalar','apps'),('💬 Xabarlar','msgs'),('✅ Tasdiqlashlar','approve'),('🔖 Saqlanganlar','saved'),('📊 Statistika','stats'),('⚙️ Sozlamalar','settings')]
 for t,d in items:b.button(text=t,callback_data=d)
 b.adjust(2,2,2,2,1);return b.as_markup()
@router.message(CommandStart())
async def start(m:Message):
 if m.from_user.id!=settings.telegram_admin_id:return
 await m.answer('🤖 <b>Aziz AI Job Agent</b>\n\nLIVE rejim. Har kuni 09:00 da qidiruv, scoring, ariza va Gmail agent ishlaydi.',parse_mode='HTML',reply_markup=menu())
@router.callback_query(F.data.in_({'jobs','top'}))
async def jobs(c:CallbackQuery):
 async with SessionLocal() as db:rows=(await db.scalars(select(Job).order_by(desc(Job.score)).limit(10))).all()
 text='🔥 <b>Top 10</b>\n\n'+'\n\n'.join([f"<b>{i+1}. {j.title}</b>\n{j.company} · {j.score:.0f}%\n{j.salary}\n<a href='{j.url}'>Ochish</a>" for i,j in enumerate(rows)]) or 'Hozircha vakansiya yo‘q.'
 await c.message.edit_text(text,parse_mode='HTML',disable_web_page_preview=True,reply_markup=menu())
@router.callback_query(F.data=='stats')
async def stats(c:CallbackQuery):
 async with SessionLocal() as db:
  j=len((await db.scalars(select(Job))).all());a=len((await db.scalars(select(Application))).all());m=len((await db.scalars(select(DBMessage))).all())
 await c.message.edit_text(f'📊 <b>Statistika</b>\n\nVakansiya: {j}\nAriza: {a}\nXabar: {m}',parse_mode='HTML',reply_markup=menu())
@router.callback_query()
async def generic(c:CallbackQuery):
 if c.data in {'services','apps','msgs','approve','saved','settings'}:await c.answer('Admin panelda live boshqaruv mavjud.',show_alert=True)
async def run_bot():
 bot=Bot(settings.telegram_bot_token);dp=Dispatcher();dp.include_router(router);await dp.start_polling(bot)
