import requests
import json
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand
import glob
import os

API_TOKEN = 'https://t.me/botfather' # токен телеграм-боту

# налаштування базової конфігурації бота
logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.Handler)

bot = Bot(token=API_TOKEN) #ініціалізація/розгортання боту
storage = MemoryStorage() #змінна для кінцевих автоматів
dp = Dispatcher(bot, storage=storage) #автоперезапуск бота

class ConvertDocxToPdfForm(StatesGroup): # клас для конвертації docx в pdf
    	get_file = State() 

main_kb = ['Convert DOCX to PDF'] #назва кнопки
# команда старт
@dp.message_handler(commands="start") 
async def cmd_start(message: types.Message):
	keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True) #створюємо клавіатуру
	keyboard.add(*main_kb)  # додаємо назву до клавіатури 
	await message.answer("Please touch me!!!!!!", reply_markup=keyboard) #повертаємо повідомлення і створюємо кнопку

# отримання файлового повідомлення від користувача
@dp.message_handler(lambda message: message.text == main_kb[0]) 
async def start_convert_docx_pdf(message: types.Message):
	keyboard = types.ReplyKeyboardRemove() # отримуємо стан кнопки 
	await ConvertDocxToPdfForm.get_file.set() #передача конвертеру docx файлу
	await message.answer("Please send .docx document", reply_markup=keyboard) # повідомлення для отримання від користувача docx файлу

# конвертація файлу та надіслання його користувачу 
@dp.message_handler(state=ConvertDocxToPdfForm.get_file, content_types=["document"]) 
async def get_docx_file(message: types.Message, state: FSMContext):
	await state.finish() # вимикаємо кінцевий автомат
	await message.document.download(destination_file=f"") #завантажуємо файл надісланий користувачем
	list_of_files = glob.glob('documents/*.docx') # * means all if need specific format then *.docx 
	latest_file = max(list_of_files, key=os.path.getmtime)
	latest_file = latest_file.replace('.docx', '') #отримання останньому файлу .docx
	filename = message.document.file_name.replace('.docx', '') # заміна формату docx файлу на пропуск
	await convert_docx_to_pdf(latest_file , filename) # виконуємо конвертацію файлу 
	doc = open(f'pdfs/{filename}' + '.pdf', 'rb') #зберігаємо отриманий файл у форматі pdf
	await message.reply_document(doc, 'aaaaa') #відповідь на повідомлення користувача де міститься docx файл

# створюємо функцію для конвертації docx в pdf
async def convert_docx_to_pdf(docx_name, pdf_name): 
	instructions = { #формат надісланих даних
	  'parts': [
	    {
	      'file': 'document'
	    }
	  ]
	}
	#надсилаємо post-запит на конвертацію файлу з docx в pdf
	response = requests.post(
	  'https://api.pspdfkit.com/build', #URL-адреса api
	  headers = { #заголовок з токеном доступа для авторизації
	    'Authorization': 'Bearer https://api.pspdfkit.com/build'
	  },
	  files = { #надсилаємо файли для конвертації
	    'document': open(f'{docx_name}.docx', 'rb')
	  },
	  data = { #відправляємо формат з типом даних у вигляді json формату
	    'instructions': json.dumps(instructions)
	  },
	  stream = True
	)

#якшо запит пройшов успішно, то ми зберігаємо даний файл
	if response.ok:
		with open(f'pdfs/{pdf_name}.pdf', 'wb') as fd: 
			for chunk in response.iter_content(chunk_size=8096):
				fd.write(chunk)
	else: #якшо ні, видаємо помилку
		print(response.text)
		exit()

# запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)