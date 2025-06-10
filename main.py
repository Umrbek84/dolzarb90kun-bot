# import telebot
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# from datetime import datetime, date
# from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date
# from sqlalchemy.orm import sessionmaker, declarative_base
# import pytz
# import os

# # ==============================================================================
# # КОНФИГУРАЦИЯЛАР (БУ ЕРНИ ЎЗГАРТИРИНГ)
# # ==============================================================================

# # 1. Google Sheets маълумотлари
# # Сизнинг Google Sheets жадвалингизнинг номи
# GOOGLE_SHEET_NAME = "Dolzarp" # 'Dolzarp' деб ёзилган, агар бошқа ном бўлса ўзгартиринг
# # Google Cloud'дан юклаб олган JSON калит файлингизнинг номи
# GSPREAD_CREDENTIALS_PATH = "sonorous-summer-461704-v1-ceef67c76f20.json" # Аниқ файлингиз номини ёзинг

# # 2. Telegram Bot Token
# # BotFather'дан олган бот токенингизни киритинг
# BOT_TOKEN = "7538436807:AAHdiZ_yO2-juhREMVgQf8jJo4jtuYQ_BdY" # Сизнинг бот токенингиз

# # 3. Вақт зонаси
# TIMEZONE = 'Asia/Tashkent'
# UZB_TZ = pytz.timezone(TIMEZONE)

# # 4. Расмларни сақлаш учун асосий папка
# PHOTOS_ROOT_DIR = "bot_rasmlari" # Расмлар шу папкага сақланади

# # ==============================================================================
# # Google Sheets билан боғланиш
# # ==============================================================================
# try:
#     scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#     creds = ServiceAccountCredentials.from_json_keyfile_name(GSPREAD_CREDENTIALS_PATH, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open(GOOGLE_SHEET_NAME).sheet1 # Биринчи листни танлаш
#     print("Google Sheets билан муваффақиятли уланди!")
# except Exception as e:
#     print(f"Google Sheets билан уланишда хатолик: {e}")
#     sheet = None # Хато бўлса sheet ни None қилиб қўямиз

# # ==============================================================================
# # Маълумотлар базаси (SQLite) конфигурацияси
# # ==============================================================================
# DATABASE_URL = "sqlite:///bot_data.db" # Бу сизнинг папкада bot_data.db файлини яратади
# engine = create_engine(DATABASE_URL)
# Base = declarative_base()

# class User(Base):
#     __tablename__ = 'users'
#     id = Column(Integer, primary_key=True)
#     telegram_id = Column(Integer, unique=True, nullable=False)
#     institution_type = Column(String, nullable=True) # Янги: 'school' ёки 'preschool'
#     institution_number = Column(String, nullable=True) # Мактаб ёки Мактабгача рақами
#     phone_number = Column(String, nullable=True) # Телефон рақами

# class DailyEntry(Base):
#     __tablename__ = 'daily_entries'
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
#     entry_date = Column(Date, nullable=False) # Маълумот киритилган сана

# Base.metadata.create_all(engine)
# Session = sessionmaker(bind=engine)

# # ==============================================================================
# # Telegram Bot инициализацияси
# # ==============================================================================
# bot = telebot.TeleBot(BOT_TOKEN)

# # ==============================================================================
# # Фойдаланувчи ҳолатлари ва маълумотлари
# # ==============================================================================
# user_states = {}
# user_data = {}

# # Қадам номлари
# STEP_INITIAL = "initial"
# STEP_GET_INSTITUTION_TYPE = "get_institution_type" # Янги қадам
# STEP_GET_SCHOOL_NUMBER = "get_school_number"
# STEP_GET_PRESCHOOL_NUMBER = "get_preschool_number" # Янги қадам
# STEP_GET_PHONE = "get_phone"
# STEP_GET_EVENT_COUNT = "get_event_count"
# STEP_GET_PARTICIPANT_COUNT = "get_participant_count"
# STEP_GET_PHOTOS = "get_photos"

# # ==============================================================================
# # Муассасалар рўйхати
# # ==============================================================================
# SCHOOL_LIST = [f"{i}-мактаб" for i in range(1, 55)] + ["1-ИМИ", "4-ИМ"]
# PRESCHOOL_LIST = [f"{i}-МТТ" for i in range(1, 30)] # 1 дан 29 гача МТТ (сиз ўзгартиришингиз мумкин)

# # ==============================================================================
# # Ёрдамчи функциялар
# # ==============================================================================

# def start_data_collection(chat_id, user_telegram_id, institution_type, institution_number, user_phone_number):
#     """Маълумот киритиш жараёнини бошлайди."""
#     session = Session()
#     user = session.query(User).filter_by(telegram_id=user_telegram_id).first()
    
#     today = date.today()
    
#     # Маълумотларни инициализация қилиш
#     user_data[chat_id] = {
#         'vaqt': today.strftime("%Y-%m-%d"), # Сана автоматик
#         'institution_type': institution_type,
#         'institution_number': institution_number,
#         'phone_number': user_phone_number,
#         'photo_files': [] # Расмлар файл ID'ларини сақлаш учун янги рўйхат
#     }
#     user_states[chat_id] = STEP_GET_EVENT_COUNT # Тўғридан-тўғри Тадбир сонига ўтамиз
    
#     # Санани фойдаланувчига кўрсатиш
#     formatted_date = today.strftime("%Y.%m.%d")
#     bot.send_message(chat_id, f"Бугунги {formatted_date} даги ўтказилган тадбирлар сонини киритинг (рақамда):", reply_markup=telebot.types.ReplyKeyboardRemove())
#     session.close()


# # ==============================================================================
# # Хэндлер функциялари
# # ==============================================================================

# @bot.message_handler(commands=['start'])
# def send_welcome(message):
#     chat_id = message.chat.id
#     session = Session()
#     user = session.query(User).filter_by(telegram_id=chat_id).first()

#     user_states[chat_id] = STEP_INITIAL # Ҳолатни бошланғич ҳолатга қайтариш
#     user_data[chat_id] = {} # Маълумотларни тозалаш

#     if not user or not user.institution_type or not user.institution_number:
#         # Муассаса тури ёки рақами йўқ ёки биринчи марта киритилмоқда
#         markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
#         markup.add(telebot.types.KeyboardButton("Мактаб"), telebot.types.KeyboardButton("Мактабгача"))
        
#         bot.send_message(chat_id, "Ассалому алайкум! Илтимос, муассасангиз турини танланг:", reply_markup=markup)
#         user_states[chat_id] = STEP_GET_INSTITUTION_TYPE # Муассаса турини киритиш қадами
#     elif not user.phone_number:
#         # Муассаса тури ва рақами мавжуд, лекин телефон рақами йўқ
#         markup = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
#         markup.add(telebot.types.KeyboardButton("☎️ Телефон рақамини юбориш", request_contact=True))
#         bot.send_message(chat_id, "Илтимос, телефон рақамингизни юборинг:", reply_markup=markup)
#         user_states[chat_id] = STEP_GET_PHONE # Телефон рақами киритиш қадами
#     else:
#         # Ҳамма маълумотлар мавжуд, маълумот киритишни бошлаймиз
#         start_data_collection(chat_id, user.telegram_id, user.institution_type, user.institution_number, user.phone_number)
#     session.close()


# @bot.message_handler(content_types=['text', 'contact'])
# def handle_message(message):
#     chat_id = message.chat.id
#     session = Session()
#     user = session.query(User).filter_by(telegram_id=chat_id).first()

#     # Агар фойдаланувчи ҳолати йўқ бўлса ёки /start юбормаган бўлса
#     if chat_id not in user_states or user_states[chat_id] == STEP_INITIAL:
#         bot.send_message(chat_id, "Илтимос, ботни бошлаш учун /start буйруғини юборинг.")
#         session.close()
#         return

#     current_step = user_states[chat_id]

#     if current_step == STEP_GET_INSTITUTION_TYPE: # Муассаса турини киритиш қадами
#         text = message.text.strip()
#         if text == "Мактаб":
#             user_data[chat_id]['institution_type'] = 'school'
#             markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
#             for school in SCHOOL_LIST:
#                 markup.add(telebot.types.KeyboardButton(school))
#             bot.send_message(chat_id, "Мактабингизни танланг:", reply_markup=markup)
#             user_states[chat_id] = STEP_GET_SCHOOL_NUMBER
#         elif text == "Мактабгача":
#             user_data[chat_id]['institution_type'] = 'preschool'
#             markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
#             for preschool in PRESCHOOL_LIST:
#                 markup.add(telebot.types.KeyboardButton(preschool))
#             bot.send_message(chat_id, "Мактабгача таълим муассасангизни танланг (МТТ):", reply_markup=markup)
#             user_states[chat_id] = STEP_GET_PRESCHOOL_NUMBER
#         else:
#             markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
#             markup.add(telebot.types.KeyboardButton("Мактаб"), telebot.types.KeyboardButton("Мактабгача"))
#             bot.send_message(chat_id, "❗ Илтимос, фақат 'Мактаб' ёки 'Мактабгача' тугмачаларидан бирини танланг.", reply_markup=markup)
#         session.close()

#     elif current_step == STEP_GET_SCHOOL_NUMBER: # Мактаб рақамини киритиш қадами
#         text = message.text.strip()
#         if text in SCHOOL_LIST:
#             user_data[chat_id]['institution_number'] = text
#             user_data[chat_id]['institution_type'] = 'school' # Қайта текшириш учун
            
#             if not user:
#                 new_user = User(telegram_id=chat_id, institution_type='school', institution_number=text)
#                 session.add(new_user)
#                 session.commit()
#                 user = new_user
#                 bot.send_message(chat_id, f"Мактабингиз ({text}) сақланди.")
#             else:
#                 user.institution_type = 'school'
#                 user.institution_number = text
#                 session.commit()
#                 bot.send_message(chat_id, f"Мактабингиз ({text}) янгиланди.")
            
#             markup = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
#             markup.add(telebot.types.KeyboardButton("☎️ Телефон рақамини юбориш", request_contact=True))
#             bot.send_message(chat_id, "Илтимос, телефон рақамингизни юборинг:", reply_markup=markup)
#             user_states[chat_id] = STEP_GET_PHONE
#         else:
#             markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
#             for school in SCHOOL_LIST:
#                 markup.add(telebot.types.KeyboardButton(school))
#             bot.send_message(chat_id, "❗ Илтимос, рўйхатдан мактаб номини танланг:", reply_markup=markup)
#         session.close()

#     elif current_step == STEP_GET_PRESCHOOL_NUMBER: # Мактабгача таълим муассасаси рақамини киритиш қадами
#         text = message.text.strip()
#         if text in PRESCHOOL_LIST:
#             user_data[chat_id]['institution_number'] = text
#             user_data[chat_id]['institution_type'] = 'preschool' # Қайта текшириш учун

#             if not user:
#                 new_user = User(telegram_id=chat_id, institution_type='preschool', institution_number=text)
#                 session.add(new_user)
#                 session.commit()
#                 user = new_user
#                 bot.send_message(chat_id, f"МТТ рақамингиз ({text}) сақланди.")
#             else:
#                 user.institution_type = 'preschool'
#                 user.institution_number = text
#                 session.commit()
#                 bot.send_message(chat_id, f"МТТ рақамингиз ({text}) янгиланди.")
            
#             markup = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
#             markup.add(telebot.types.KeyboardButton("☎️ Телефон рақамини юбориш", request_contact=True))
#             bot.send_message(chat_id, "Илтимос, телефон рақамингизни юборинг:", reply_markup=markup)
#             user_states[chat_id] = STEP_GET_PHONE
#         else:
#             markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
#             for preschool in PRESCHOOL_LIST:
#                 markup.add(telebot.types.KeyboardButton(preschool))
#             bot.send_message(chat_id, "❗ Илтимос, рўйхатдан МТТ номини танланг:", reply_markup=markup)
#         session.close()

#     elif current_step == STEP_GET_PHONE: # Телефон рақамини киритиш қадами
#         if message.contact:
#             phone_number = message.contact.phone_number
#             user_data[chat_id]['phone_number'] = phone_number
#             if user:
#                 user.phone_number = phone_number
#                 session.commit()
#                 bot.send_message(chat_id, f"Телефон рақамингиз ({phone_number}) сақланди.")
#                 # Муассаса тури ва рақами аллақачон user обектида мавжуд
#                 start_data_collection(chat_id, user.telegram_id, user.institution_type, user.institution_number, user.phone_number)
#             else:
#                 bot.send_message(chat_id, "Хатолик юз берди, илтимос /start буйруғини қайта юборинг.")
#             session.close()
#         else:
#             markup = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
#             markup.add(telebot.types.KeyboardButton("☎️ Телефон рақамини юбориш", request_contact=True))
#             bot.send_message(chat_id, "❗ Илтимос, пастдаги тугмача орқали телефон рақамингизни юборинг.", reply_markup=markup)
#             session.close()

#     elif current_step == STEP_GET_EVENT_COUNT: # Тадбирлар сони қадами
#         text = message.text.strip()
#         if text.isdigit():
#             user_data[chat_id]["tadbir_soni"] = int(text)
#             bot.send_message(chat_id, "Тадбирларга қатнашган жами ўқувчилар сонини киритинг (рақамда):")
#             user_states[chat_id] = STEP_GET_PARTICIPANT_COUNT
#         else:
#             today = date.today()
#             formatted_date = today.strftime("%Y.%m.%d")
#             bot.send_message(chat_id, f"❗ Илтимос, бугунги {formatted_date} даги ўтказилган тадбирлар сонини рақамда киритинг.")
#         session.close()

#     elif current_step == STEP_GET_PARTICIPANT_COUNT: # Ўқувчилар сони қадами
#         text = message.text.strip()
#         if text.isdigit():
#             user_data[chat_id]["o'quvchilar_soni"] = int(text)

#             data = user_data[chat_id]
#             try:
#                 if sheet:
#                     # Устунлар тартиби: vaqt, institution_type, institution_number, phone_number, tadbir_soni, o'quvchilar_soni
#                     sheet.append_row([
#                         data.get("vaqt"),
#                         data.get("institution_type"), # Янги
#                         data.get("institution_number"),
#                         data.get("phone_number"), 
#                         data.get("tadbir_soni"),
#                         data.get("o'quvchilar_soni")
#                     ])
#                     bot.send_message(chat_id, "✅ Маълумот муваффақиятли сақланди.")
                    
#                     if user:
#                         daily_entry = DailyEntry(user_id=user.id, entry_date=datetime.strptime(data["vaqt"], "%Y-%m-%d").date())
#                         session.add(daily_entry)
#                         session.commit()
                    
#                     bot.send_message(chat_id, "Энди, бугунги тадбирлардан **2 та расм** юборинг. Ҳар бир расмни алоҳида юборинг.", reply_markup=telebot.types.ReplyKeyboardRemove())
#                     user_states[chat_id] = STEP_GET_PHOTOS
                    
#                 else:
#                     bot.send_message(chat_id, "❌ Google Sheets билан уланишда муаммо бор. Маълумот сақланмади.")
#                     user_states.pop(chat_id, None)
#                     user_data.pop(chat_id, None)
#             except Exception as e:
#                 bot.send_message(chat_id, f"❌ Маълумотларни Google Sheets'га ёзишда хатолик: {e}")
#                 print(f"Google Sheets'ga ёзишда хатолик: {e}")
#                 user_states.pop(chat_id, None)
#                 user_data.pop(chat_id, None)
#         else:
#             bot.send_message(chat_id, "❗ Илтимос, ўқувчилар сонини рақамда киритинг.")
#         session.close()

# @bot.message_handler(content_types=['photo'])
# def handle_photos(message):
#     chat_id = message.chat.id
    
#     if chat_id not in user_states or user_states[chat_id] != STEP_GET_PHOTOS:
#         bot.send_message(chat_id, "Илтимос, ҳозир расм юбориш навбати эмас. /start буйруғини юбориб, қайтадан бошлашингиз мумкин.")
#         return

#     if not message.photo:
#         bot.send_message(chat_id, "❗ Илтимос, фақат расм юборинг.")
#         return
    
#     file_id = message.photo[-1].file_id 
#     user_data[chat_id]['photo_files'].append(file_id)
    
#     current_photo_count = len(user_data[chat_id]['photo_files'])
    
#     if current_photo_count < 2:
#         bot.send_message(chat_id, f"Расм қабул қилинди. Яна {2 - current_photo_count} та расм юборинг.")
#     else:
#         bot.send_message(chat_id, "Барча расмлар қабул қилинди. Файллар сақланмоқда, илтимос кутинг...")
        
#         saved_date = user_data[chat_id].get("vaqt") #YYYY-MM-DD
#         saved_institution_type = user_data[chat_id].get("institution_type") # 'school' ёки 'preschool'
#         saved_institution_number = user_data[chat_id].get("institution_number") # e.g., "1-мактаб" or "5-МТТ"

#         if not saved_date or not saved_institution_number or not saved_institution_type:
#             bot.send_message(chat_id, "Расмларни сақлаш учун керакли маълумотлар топилмади. /start буйруғини юбориб, қайтадан бошланг.")
#             user_states.pop(chat_id, None)
#             user_data.pop(chat_id, None)
#             return

#         # Папка йўлини яратиш: bot_rasmlari/YYYY-MM-DD/Муассаса_тури/Муассаса_номери
#         folder_name_institution_type = "maktablar" if saved_institution_type == 'school' else "maktabgacha"
#         folder_name_institution_number = saved_institution_number.replace(" ", "_").replace("-", "_") # Масалан, "1_мактаб" ёки "5_МТТ"
        
#         save_path = os.path.join(PHOTOS_ROOT_DIR, saved_date, folder_name_institution_type, folder_name_institution_number)

#         try:
#             os.makedirs(save_path, exist_ok=True)
            
#             for i, photo_file_id in enumerate(user_data[chat_id]['photo_files']):
#                 file_info = bot.get_file(photo_file_id)
#                 downloaded_file = bot.download_file(file_info.file_path)
                
#                 file_name = f"{chat_id}_{saved_date}_{i+1}.jpg"
#                 file_path = os.path.join(save_path, file_name)
                
#                 with open(file_path, 'wb') as new_file:
#                     new_file.write(downloaded_file)
#                 print(f"Расм сақланди: {file_path}")
            
#             bot.send_message(chat_id, f"✅ Барча расмлар муваффақиятли сақланди: {save_path} папкасида. Раҳмат!", reply_markup=telebot.types.ReplyKeyboardRemove())
            
#         except Exception as e:
#             bot.send_message(chat_id, f"❌ Расмларни сақлашда хатолик юз берди: {e}")
#             print(f"Расмларни сақлашда хатолик: {e}")
        
#         user_states.pop(chat_id, None)
#         user_data.pop(chat_id, None)


# # ==============================================================================
# # Ботни ишга тушириш
# # ==============================================================================
# if __name__ == '__main__':
#     print("Бот ишга тушди...")
#     bot.polling(non_stop=True)


import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, date
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import sessionmaker, declarative_base
import pytz
import os

# ==============================================================================
# КОНФИГУРАЦИЯЛАР (БУ ЕРНИ ЎЗГАРТИРИНГ)
# ==============================================================================

# 1. Google Sheets маълумотлари
# Сизнинг Google Sheets жадвалингизнинг номи
GOOGLE_SHEET_NAME = "Dolzarp" # 'Dolzarp' деб ёзилган, агар бошқа ном бўлса ўзгартиринг
# Google Cloud'дан юклаб олган JSON калит файлингизнинг номи

# GSPREAD_CREDENTIALS_PATH = "sonorous-summer-461704-v1-ceef67c76f20.json" # Аниқ файлингиз номини ёзинг

GSPREAD_CREDENTIALS_PATH = "E:\бот\sonorous-summer-461704-v1-ceef67c76f20.json" # Аниқ файлингиз номини ёзинг

# 2. Telegram Bot Token
# BotFather'дан олган бот токенингизни киритинг
BOT_TOKEN = "7538436807:AAHdiZ_yO2-juhREMVgQf8jJo4jtuYQ_BdY" # Сизнинг бот токенингиз

# 3. Вақт зонаси
TIMEZONE = 'Asia/Tashkent'
UZB_TZ = pytz.timezone(TIMEZONE)

# 4. Расмларни сақлаш учун асосий папка
PHOTOS_ROOT_DIR = "C:/Users/User/Desktop/Dolzarb 90 kun/main.py/bot_rasmlari" # Расмлар шу папкага сақланади

# 5. Тадбир санаси оралиғи
EVENT_START_DATE = date(2025, 5, 31)
EVENT_END_DATE = date(2025, 8, 31)


# ==============================================================================
# Google Sheets билан боғланиш
# ==============================================================================
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GSPREAD_CREDENTIALS_PATH, scope)
    client = gspread.authorize(creds)
    sheet = client.open(GOOGLE_SHEET_NAME).sheet1 # Биринчи листни танлаш
    print("Google Sheets билан муваффақиятли уланди!")
except Exception as e:
    print(f"Google Sheets билан уланишда хатолик: {e}")
    sheet = None # Хато бўлса sheet ни None қилиб қўямиз

# ==============================================================================
# Маълумотлар базаси (SQLite) конфигурацияси
# ==============================================================================
DATABASE_URL = "sqlite:///bot_data.db" # Бу сизнинг папкада bot_data.db файлини яратади
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    institution_type = Column(String, nullable=True) # Янги: 'school' ёки 'preschool'
    institution_number = Column(String, nullable=True) # Мактаб ёки Мактабгача рақами
    phone_number = Column(String, nullable=True) # Телефон рақами

class DailyEntry(Base):
    __tablename__ = 'daily_entries'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    entry_date = Column(Date, nullable=False) # Маълумот киритилган сана

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# ==============================================================================
# Telegram Bot инициализацияси
# ==============================================================================
bot = telebot.TeleBot(BOT_TOKEN)

# ==============================================================================
# Фойдаланувчи ҳолатлари ва маълумотлари
# ==============================================================================
user_states = {}
user_data = {}

# Қадам номлари
STEP_INITIAL = "initial"
STEP_GET_INSTITUTION_TYPE = "get_institution_type" # Янги қадам
STEP_GET_SCHOOL_NUMBER = "get_school_number"
STEP_GET_PRESCHOOL_NUMBER = "get_preschool_number" # Янги қадам
STEP_GET_PHONE = "get_phone"
STEP_GET_EVENT_COUNT = "get_event_count"
STEP_GET_PARTICIPANT_COUNT = "get_participant_count"
STEP_GET_PHOTOS = "get_photos"

# ==============================================================================
# Муассасалар рўйхати
# ==============================================================================
SCHOOL_LIST = [f"{i}-мактаб" for i in range(1, 55)] + ["1-ИМИ", "4-ИМ"]
PRESCHOOL_LIST = [f"{i}-МТТ" for i in range(1, 41)] # 1 дан 40 гача МТТ (сиз ўзгартиришингиз мумкин)

# ==============================================================================
# Ёрдамчи функциялар
# ==============================================================================

def start_data_collection(chat_id, user_telegram_id, institution_type, institution_number, user_phone_number):
    """Маълумот киритиш жараёнини бошлайди."""
    session = Session()
    user = session.query(User).filter_by(telegram_id=user_telegram_id).first()
    
    today = date.today()
    
    # Calculate the day number
    delta = today - EVENT_START_DATE
    day_number = delta.days + 1 # +1 because the first day is day 1

    # Маълумотларни инициализация қилиш
    user_data[chat_id] = {
        'vaqt': today.strftime("%Y-%m-%d"), # Сана автоматик
        'institution_type': institution_type,
        'institution_number': institution_number,
        'phone_number': user_phone_number,
        'photo_files': [] # Расмлар файл ID'ларини сақлаш учун янги рўйхат
    }
    user_states[chat_id] = STEP_GET_EVENT_COUNT # Тўғридан-тўғри Тадбир сонига ўтамиз
    
    # Санани фойдаланувчига кўрсатиш
    formatted_date = today.strftime("%d.%m.%Y")
    
    # Modified message to include the day number
    if today >= EVENT_START_DATE and today <= EVENT_END_DATE:
        bot.send_message(chat_id, f"Бугун тадбирларни  **{day_number}-куни**  сана : **{formatted_date}** даги  ўтказилган тадбирлар сонини киритинг (рақамда):", parse_mode='Markdown', reply_markup=telebot.types.ReplyKeyboardRemove())
    else:
        bot.send_message(chat_id, f"Бугун **{formatted_date}** даги ўтказилган тадбирлар сонини киритинг (рақамда):", parse_mode='Markdown', reply_markup=telebot.types.ReplyKeyboardRemove())
    
    session.close()


# ==============================================================================
# Хэндлер функциялари
# ==============================================================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    session = Session()
    user = session.query(User).filter_by(telegram_id=chat_id).first()

    user_states[chat_id] = STEP_INITIAL # Ҳолатни бошланғич ҳолатга қайтариш
    user_data[chat_id] = {} # Маълумотларни тозалаш

    if not user or not user.institution_type or not user.institution_number:
        # Муассаса тури ёки рақами йўқ ёки биринчи марта киритилмоқда
        markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
        markup.add(telebot.types.KeyboardButton("Мактаб"), telebot.types.KeyboardButton("Мактабгача"))
        
        bot.send_message(chat_id, "Ассалому алайкум! Илтимос, муассасангиз турини танланг:", reply_markup=markup)
        user_states[chat_id] = STEP_GET_INSTITUTION_TYPE # Муассаса турини киритиш қадами
    elif not user.phone_number:
        # Муассаса тури ва рақами мавжуд, лекин телефон рақами йўқ
        markup = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        markup.add(telebot.types.KeyboardButton("☎️ Телефон рақамини юбориш", request_contact=True))
        bot.send_message(chat_id, "Илтимос, телефон рақамингизни юборинг:", reply_markup=markup)
        user_states[chat_id] = STEP_GET_PHONE # Телефон рақами киритиш қадами
    else:
        # Ҳамма маълумотлар мавжуд, маълумот киритишни бошлаймиз
        start_data_collection(chat_id, user.telegram_id, user.institution_type, user.institution_number, user.phone_number)
    session.close()


@bot.message_handler(content_types=['text', 'contact'])
def handle_message(message):
    chat_id = message.chat.id
    session = Session()
    user = session.query(User).filter_by(telegram_id=chat_id).first()

    # Агар фойдаланувчи ҳолати йўқ бўлса ёки /start юбормаган бўлса
    if chat_id not in user_states or user_states[chat_id] == STEP_INITIAL:
        bot.send_message(chat_id, "Илтимос, ботни бошлаш учун /start буйруғини юборинг.")
        session.close()
        return

    current_step = user_states[chat_id]

    if current_step == STEP_GET_INSTITUTION_TYPE: # Муассаса турини киритиш қадами
        text = message.text.strip()
        if text == "Мактаб":
            user_data[chat_id]['institution_type'] = 'school'
            markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
            for school in SCHOOL_LIST:
                markup.add(telebot.types.KeyboardButton(school))
            bot.send_message(chat_id, "Мактабингизни танланг:", reply_markup=markup)
            user_states[chat_id] = STEP_GET_SCHOOL_NUMBER
        elif text == "Мактабгача":
            user_data[chat_id]['institution_type'] = 'preschool'
            markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
            for preschool in PRESCHOOL_LIST:
                markup.add(telebot.types.KeyboardButton(preschool))
            bot.send_message(chat_id, "Мактабгача таълим муассасангизни танланг (МТТ):", reply_markup=markup)
            user_states[chat_id] = STEP_GET_PRESCHOOL_NUMBER
        else:
            markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
            markup.add(telebot.types.KeyboardButton("Мактаб"), telebot.types.KeyboardButton("Мактабгача"))
            bot.send_message(chat_id, "❗ Илтимос, фақат 'Мактаб' ёки 'Мактабгача' тугмачаларидан бирини танланг.", reply_markup=markup)
        session.close()

    elif current_step == STEP_GET_SCHOOL_NUMBER: # Мактаб рақамини киритиш қадами
        text = message.text.strip()
        if text in SCHOOL_LIST:
            user_data[chat_id]['institution_number'] = text
            user_data[chat_id]['institution_type'] = 'school' # Қайта текшириш учун
            
            if not user:
                new_user = User(telegram_id=chat_id, institution_type='school', institution_number=text)
                session.add(new_user)
                session.commit()
                user = new_user
                bot.send_message(chat_id, f"Мактабингиз ({text}) сақланди.")
            else:
                user.institution_type = 'school'
                user.institution_number = text
                session.commit()
                bot.send_message(chat_id, f"Мактабингиз ({text}) янгиланди.")
            
            markup = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
            markup.add(telebot.types.KeyboardButton("☎️ Телефон рақамини юбориш", request_contact=True))
            bot.send_message(chat_id, "Илтимос, телефон рақамингизни юборинг:", reply_markup=markup)
            user_states[chat_id] = STEP_GET_PHONE
        else:
            markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
            for school in SCHOOL_LIST:
                markup.add(telebot.types.KeyboardButton(school))
            bot.send_message(chat_id, "❗ Илтимос, рўйхатдан мактаб номини танланг:", reply_markup=markup)
        session.close()

    elif current_step == STEP_GET_PRESCHOOL_NUMBER: # Мактабгача таълим муассасаси рақамини киритиш қадами
        text = message.text.strip()
        if text in PRESCHOOL_LIST:
            user_data[chat_id]['institution_number'] = text
            user_data[chat_id]['institution_type'] = 'preschool' # Қайта текшириш учун

            if not user:
                new_user = User(telegram_id=chat_id, institution_type='preschool', institution_number=text)
                session.add(new_user)
                session.commit()
                user = new_user
                bot.send_message(chat_id, f"МТТ рақамингиз ({text}) сақланди.")
            else:
                user.institution_type = 'preschool'
                user.institution_number = text
                session.commit()
                bot.send_message(chat_id, f"МТТ рақамингиз ({text}) янгиланди.")
            
            markup = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
            markup.add(telebot.types.KeyboardButton("☎️ Телефон рақамини юбориш", request_contact=True))
            bot.send_message(chat_id, "Илтимос, телефон рақамингизни юборинг:", reply_markup=markup)
            user_states[chat_id] = STEP_GET_PHONE
        else:
            markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
            for preschool in PRESCHOOL_LIST:
                markup.add(telebot.types.KeyboardButton(preschool))
            bot.send_message(chat_id, "❗ Илтимос, рўйхатдан МТТ номини танланг:", reply_markup=markup)
        session.close()

    elif current_step == STEP_GET_PHONE: # Телефон рақамини киритиш қадами
        if message.contact:
            phone_number = message.contact.phone_number
            user_data[chat_id]['phone_number'] = phone_number
            if user:
                user.phone_number = phone_number
                session.commit()
                bot.send_message(chat_id, f"Телефон рақамингиз ({phone_number}) сақланди.")
                # Муассаса тури ва рақами аллақачон user обектида мавжуд
                start_data_collection(chat_id, user.telegram_id, user.institution_type, user.institution_number, user.phone_number)
            else:
                bot.send_message(chat_id, "Хатолик юз берди, илтимос /start буйруғини қайта юборинг.")
            session.close()
        else:
            markup = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
            markup.add(telebot.types.KeyboardButton("☎️ Телефон рақамини юбориш", request_contact=True))
            bot.send_message(chat_id, "❗ Илтимос, пастдаги тугмача орқали телефон рақамингизни юборинг.", reply_markup=markup)
            session.close()

    elif current_step == STEP_GET_EVENT_COUNT: # Тадбирлар сони қадами
        text = message.text.strip()
        if text.isdigit():
            user_data[chat_id]["tadbir_soni"] = int(text)
            bot.send_message(chat_id, "Тадбирларга қатнашган жами ўқувчилар(тарбияланувчилар) сонини киритинг (рақамда):")
            user_states[chat_id] = STEP_GET_PARTICIPANT_COUNT
        else:
            today = date.today()
            formatted_date = today.strftime("%Y.%m.%d")
            
            # Calculate the day number again for error message
            delta = today - EVENT_START_DATE
            day_number = delta.days + 1 

            if today >= EVENT_START_DATE and today <= EVENT_END_DATE:
                bot.send_message(chat_id, f"❗ Илтимос, бугунги **{formatted_date}** даги **{day_number}-кун** ўтказилган тадбирлар сонини рақамда киритинг.", parse_mode='Markdown')
            else:
                 bot.send_message(chat_id, f"❗ Илтимос, бугунги **{formatted_date}** даги ўтказилган тадбирлар сонини рақамда киритинг.", parse_mode='Markdown')
        session.close()

    elif current_step == STEP_GET_PARTICIPANT_COUNT: # Ўқувчилар сони қадами
        text = message.text.strip()
        if text.isdigit():
            user_data[chat_id]["o'quvchilar_soni"] = int(text)

            data = user_data[chat_id]
            try:
                if sheet:
                    # Устунлар тартиби: vaqt, institution_type, institution_number, phone_number, tadbir_soni, o'quvchilar_soni
                    sheet.append_row([
                        data.get("vaqt"),
                        data.get("institution_type"), # Янги
                        data.get("institution_number"),
                        data.get("phone_number"), 
                        data.get("tadbir_soni"),
                        data.get("o'quvchilar_soni")
                    ])
                    bot.send_message(chat_id, "✅ Маълумот муваффақиятли сақланди.")
                    
                    if user:
                        daily_entry = DailyEntry(user_id=user.id, entry_date=datetime.strptime(data["vaqt"], "%Y-%m-%d").date())
                        session.add(daily_entry)
                        session.commit()
                    
                    bot.send_message(chat_id, "Энди, бугунги тадбирлардан **4 та расм** юборинг. Ҳар бир расмни алоҳида юборинг.", reply_markup=telebot.types.ReplyKeyboardRemove(), parse_mode='Markdown')
                    user_states[chat_id] = STEP_GET_PHOTOS
                    
                else:
                    bot.send_message(chat_id, "❌ Google Sheets билан уланишда муаммо бор. Маълумот сақланмади.")
                    user_states.pop(chat_id, None)
                    user_data.pop(chat_id, None)
            except Exception as e:
                bot.send_message(chat_id, f"❌ Маълумотларни Google Sheets'га ёзишда хатолик: {e}")
                print(f"Google Sheets'ga ёзишда хатолик: {e}")
                user_states.pop(chat_id, None)
                user_data.pop(chat_id, None)
        else:
            bot.send_message(chat_id, "❗ Илтимос, ўқувчилар сонини рақамда киритинг.")
        session.close()

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    chat_id = message.chat.id
    
    if chat_id not in user_states or user_states[chat_id] != STEP_GET_PHOTOS:
        bot.send_message(chat_id, "Илтимос, ҳозир расм юбориш навбати эмас. /start буйруғини юбориб, қайтадан бошлашингиз мумкин.")
        return

    if not message.photo:
        bot.send_message(chat_id, "❗ Илтимос, фақат расм юборинг.")
        return
    
    file_id = message.photo[-1].file_id 
    user_data[chat_id]['photo_files'].append(file_id)
    
    current_photo_count = len(user_data[chat_id]['photo_files'])
    
    if current_photo_count <= 3:
        bot.send_message(chat_id, f"Расм қабул қилинди. Яна {3 - current_photo_count} та расм юборинг.")
    else:
        bot.send_message(chat_id, "Барча расмлар қабул қилинди. Файллар сақланмоқда, илтимос кутинг...")
        
        saved_date = user_data[chat_id].get("vaqt") #YYYY-MM-DD
        saved_institution_type = user_data[chat_id].get("institution_type") # 'school' ёки 'preschool'
        saved_institution_number = user_data[chat_id].get("institution_number") # e.g., "1-мактаб" or "5-МТТ"

        if not saved_date or not saved_institution_number or not saved_institution_type:
            bot.send_message(chat_id, "Расмларни сақлаш учун керакли маълумотлар топилмади. /start буйруғини юбориб, қайтадан бошланг.")
            user_states.pop(chat_id, None)
            user_data.pop(chat_id, None)
            return

        # Папка йўлини яратиш: bot_rasmlari/YYYY-MM-DD/Муассаса_тури/Муассаса_номери
        folder_name_institution_type = "maktablar" if saved_institution_type == 'school' else "maktabgacha"
        folder_name_institution_number = saved_institution_number.replace(" ", "_").replace("-", "_") # Масалан, "1_мактаб" ёки "5_МТТ"
        
        save_path = os.path.join(PHOTOS_ROOT_DIR, saved_date, folder_name_institution_type, folder_name_institution_number)

        try:
            os.makedirs(save_path, exist_ok=True)
            
            for i, photo_file_id in enumerate(user_data[chat_id]['photo_files']):
                file_info = bot.get_file(photo_file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                
                file_name = f"{chat_id}_{saved_date}_{i+1}.jpg"
                file_path = os.path.join(save_path, file_name)
                
                with open(file_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                print(f"Расм сақланди: {file_path}")
            
            bot.send_message(chat_id, f"✅ Барча расмлар муваффақиятли сақланди: {save_path} папкасида. Раҳмат!", reply_markup=telebot.types.ReplyKeyboardRemove())
            
        except Exception as e:
            bot.send_message(chat_id, f"❌ Расмларни сақлашда хатолик юз берди: {e}")
            print(f"Расмларни сақлашда хатолик: {e}")
        
        user_states.pop(chat_id, None)
        user_data.pop(chat_id, None)


# ==============================================================================
# Ботни ишга тушириш
# ==============================================================================
if __name__ == '__main__':
    print("Бот ишга тушди...")
    bot.polling(non_stop=True)
