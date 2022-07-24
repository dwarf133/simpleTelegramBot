# 5417331331:AAFdGoDLDsKau3EYL_NkuT8BCRlLuToxFsU
#sudo docker run -d --name bot-data -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
#89991054057
import logging
import json
import redis
from warnings import filters
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler

# прдключаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# подключаем редис
r = redis.Redis(host='localhost', port=6379, db=0)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Привет, я бот для заметок, напиши /help что бы увидеть список команд")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
    text="""
    /add имя_заметки текст - добавляет либо изменяет содержимое заметки
    /delete имя_заметки - удаляет заметку
    /search поисковое_слово - ищет заметку содержащую слово
    /search_by_tag имя_заметки - ищет заметку по названию
    /help 
    """)

async def bad_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Извини данный тип контента не поддерживается')

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = {}
    tag = context.args[0]
    note = context.args[1:]
    userId = update.effective_user['id']
    data["tag"] = tag
    data["content"] = ' '.join(note)
    if r.set(f'{userId}:{tag}', json.dumps(data)): resp = 'Запись успешно добавлена'
    else: resp = 'Упс, возникла какая-то ошибка :('
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=resp)

async def search_by_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tag = context.args[0]
    userId = update.effective_user['id']
    notes = r.get(f'{userId}:{tag}')
    note = []
    exist = False
    if notes != None:
        unmarshaledNotes = json.loads(notes.decode('utf8'))
        if unmarshaledNotes['tag'] == tag:
            note = unmarshaledNotes
            exist = True
    if exist: 
        resp = f'Тэг: {note["tag"]}\n {note["content"]}'
    else: resp = 'Запись не найдена'

    await context.bot.send_message(chat_id=update.effective_chat.id, text=resp)

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tag = context.args[0]
    userId = update.effective_user['id']
    sc = r.delete(f'{userId}:{tag}')
    if sc == 1: resp = 'Запись успешно удалена'
    else: resp = 'Упс, возникла какая-то ошибка :('
    await context.bot.send_message(chat_id=update.effective_chat.id, text=resp)

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    userId = update.effective_user['id']
    search_word = ' '.join(context.args)
    keys = r.keys(f'{userId}:*')
    data = []
    with r.pipeline() as pipe:
        for t in keys:
            pipe.get(t)
        data = pipe.execute()
    find = 0
    for t in data:
        temp = json.loads(t.decode('utf8'))
        if temp['tag'] == search_word or search_word in temp['content']:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Тэг: {temp["tag"]}\n {temp["content"]}')
            find += 1
    
    if find == 0: resp = 'Записей не найденно'
    else: resp = f'Найденно надписей: {find}'
    await context.bot.send_message(chat_id=update.effective_chat.id, text=resp)


if __name__ == '__main__':
    application = ApplicationBuilder().token('5417331331:AAFdGoDLDsKau3EYL_NkuT8BCRlLuToxFsU').build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    help_handler = CommandHandler('help', help)
    application.add_handler(help_handler)

    add_handler = CommandHandler('add', add)
    application.add_handler(add_handler)

    search_by_tag_handler = CommandHandler('search_by_tag', search_by_tag)
    application.add_handler(search_by_tag_handler)

    delete_handler = CommandHandler('delete', delete)
    application.add_handler(delete_handler)
    
    search_handler = CommandHandler('search', search)
    application.add_handler(search_handler)

    badTypeHandler = MessageHandler(~filters.COMMAND, bad_type)
    application.add_handler(badTypeHandler)

    application.run_polling()