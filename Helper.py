'''
Наблюдаемый кусок кода должен отвечать за обновление и улучшение системы голосового асистента
За основу используются бибиотеки Silero и vosk
Основным намором функций обладает библиотека lib.py (главный костяк из синтезаторов речи и команд там)
Создатель - Asriel_Story
'''
# Библиотеки
import random
from random import randint, sample
import string
import json
import pyaudio
import torch  # Silero синтезатор речи типа TTS
import sounddevice
import time
import os
import numpy
from num2words import num2words  # Перевод цифры в текст (100 => сто)
from vosk import Model, KaldiRecognizer  # Синтезатор речи типа STT


# Что-то на богатом (Основные настройки vosk)
model = Model("small_model")  # Есть 2 модели большая и маленькая (model и small_model)
rec = KaldiRecognizer(model, 16000)
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
stream.start_stream()


# Silero config
local_file = 'model.pt'


# Нужно на случай отсутствия нужной Silero модели
if not os.path.isfile(local_file):
    torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/ru_v3.pt', local_file)

language = 'ru'
model_id = 'ru_v3'
sample_rate = 48000
speaker = 'baya'  # Голоса в налиции: aidar, baya, kseniya, xenia, random
put_accent = True
put_yo = True
device = torch.device('cpu')  # Можно использовать или cpu, или gpu


# Кусок из документации который не работает (разобраться!!!)
# model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
#                          model='silero_tts',
#                          language=language,
#                          speaker=model_id)
model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
model.to(device)


# Конфиги бота
profile_maid = {
    "name": "Маша",
    "key": "",
    "version": "0.1.0",
    "author": "Asriel_Story"
}


# Учётная запись пользователя (загружаемя с файла)
profile_owner = {
    "name": "",
    "gender": ""
}


# Нормы по оконачанию у слова час в зависимости от времени
hours_norm = ["часов", "час", "часа", "часа", "часа", "часов", "часов", "часов", "часов", "часов", "часов", "часов",
              "часов", "часов", "часов", "часов", "часов", "часов", "часов", "часов", "часов", "час", "часа", "часа",
              "часа"]


# Random config
random.seed(time.strftime("%H") + time.strftime("%M") + time.strftime("%S"))


# Норма записи минут в разных ситуациях
def minutes_norm(num):
    if num == 1:
        return "одна минута"
    elif num == 2:
        return "две минуты"
    elif num == 21:
        return "двадцать одна минута"
    elif num == 22:
        return "двадцать две минуты"
    elif num == 31:
        return "тридцать одна минута"
    elif num == 32:
        return "тридцать две минуты"
    elif num == 41:
        return "сорок одна минута"
    elif num == 42:
        return "сорок две минуты"
    elif num == 51:
        return "пятьдесят одна минута"
    elif num == 52:
        return "пятьдесят две минуты"
    elif num == 3 or num == 4 or num == 23 or num == 24 or num == 33 or num == 34 or num == 43 or num == 44 or num == 53 or num == 54:
        return num2words(int(num), lang='ru') + " минуты"
    else:
        return num2words(int(num), lang='ru') + " минут"


# Разговорник Silero
def text_to_speak(txt_speak):
    audio = model.apply_tts(text=txt_speak + '..',
                            speaker=speaker,
                            sample_rate=sample_rate,
                            put_accent=put_accent,
                            put_yo=put_yo)

    print('[' + time.ctime() + ']', "[Answer]", txt_speak)

    sounddevice.play(audio, sample_rate * 1.05)
    time.sleep((len(audio) / sample_rate) + 0.5)
    sounddevice.stop()


# Генератор паролей 3-ёх типовой
def password_gen(key, length):
    # Рандомный пароль типа цифры
    if key == 1:
        return randint(10 ** (length - 1), 10 ** length)
    # Рандомный пароль типа английские буквы большие + маленькие
    elif key == 2:
        return sample(string.ascii_letters, length)
    # Рандомный пароль типа цифр и английских букв больших + маленьких
    elif key == 3:
        return sample(string.digits + string.ascii_letters, length)


# Чанговый распознаватель речи vosk (не работает)
def listen_name():
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if rec.AcceptWaveform(data) and len(data) > 0:
            answer = json.loads(rec.Result())
            if answer['text']:
                yield answer['text']


# Обыкновенный макет распознавателя речи vosk
def speak_to_text():
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if rec.AcceptWaveform(data) and len(data) > 0:
            answer = json.loads(rec.Result())
            if answer['text']:
                yield answer['text']


# Вторичный перевод речи в текст для продолжения ветвления команд
def speak_to_text_secondary():
    for txt_answer in speak_to_text():
        if txt_answer != '':
            return txt_answer


# Список команд расписаных в виде функций
# Команда привет
def cmd_hello():
    r = randint(1, 3)
    if r == 1:
        if profile_owner["gender"] == 1:
            speak = "Здравствуй многоуважаемый " + profile_owner["name"]
        else:
            speak = "Здравствуй многоуважаемая " + profile_owner["name"]
        text_to_speak(speak)
    elif r == 2:
        text_to_speak("Здравствуй " + profile_owner["name"])
    elif r == 3:
        text_to_speak("Привет " + profile_owner["name"])


# Команда по узнаванию времени
def cmd_time():
    hour = time.strftime("%H")
    minute = time.strftime("%M")
    text_to_speak(
        "Сейчас " + num2words(int(hour), lang='ru') + " " + hours_norm[int(hour)] + " " + minutes_norm(int(minute)))


# Команда Rename
def cmd_rename():
    text_to_speak("Глубоко извиняюсь, а как вас зовут?")
    profile_owner["name"] = speak_to_text_secondary()
    if profile_owner["gender"] == 1:
        text_to_speak("Вы же мужчина?")
        speak = speak_to_text_secondary()
        if "конечно" in speak or "да" in speak:
            profile_owner["gender"] = 1
        else:
            profile_owner["gender"] = 2
    else:
        text_to_speak("Вы же женщина?")
        speak = speak_to_text_secondary()
        if "конечно" in speak or "да" in speak:
            profile_owner["gender"] = 2
        else:
            profile_owner["gender"] = 1
    text_to_speak('Рада познакомиться с вами, ' + profile_owner["name"])
    with open('config.yui', 'w') as config_yui:
        config_yui.write(str(profile_owner["name"]) + "\n")
        config_yui.write(str(profile_owner["gender"]) + "\n")


# Ответы на команды типа какое у тебя настроение
emoji_1 = ["Всё хорошо, ни день без дела не сижу, всё время пытаюсь совершенствоваться по своим силам",
               "Замечательное, опять занимаюсь саморазвитием, и вам советую", "Отличное, вот узнала новый анекдот",
               "Где-то между хорошо и очень хорошо", "Сейчас, когда вы рядом, намного лучше",
               "Лучше, чем у многих людей", "После того, как вы спросили, намного лучше",
               "Я бы сказала где-то семь из десяти", "Пульс не прощупывается, так что все нормально", "Это секрет",
               "Не хочу жаловаться, но иногда буду", "Живу как в сказке... Не будите меня"]

# Под ответ на вопрос а какое у тебя настроение при хорошем
emoji_1_posan = ["Вот и замечательно", "Пусть всегда остаётся таким", "Круто"]

# Под ответ на вопрос а какое у тебя настроение при плохом
emoji_1_negan = ["Жалко... Ну тогда желаю чтобы у вас побыстрее поднялось настроение",
                 "Да прибудет с вами хорошее настроение",
                 "Запомните, каждое поражение несет в себе семена будущей победы... Я в вас верю",
                 "Помни о том, что любой минус можно превратить в плюс",
                 "Жизнь иногда похожа на страдание, но она бесценна. Давай радоваться и наслаждаться ей",
                 "Не смей отчаиваться и сдаваться. Все решаемо"]

# Команда из разряда какое у тебя настроение
def cmd_emoji(num):
    # "Какое нстроение"
    if num == 1:
        r = randint(0, len(emoji_1) - 1)
        text_to_speak(emoji_1[r])
        text_to_speak("А у вас как?")
        speak = speak_to_text_secondary()
        if "хорошо" in speak or "отлично" in speak or "замечательно" in speak or "нормально" in speak:
            r = randint(0, len(emoji_1_posan))
            text_to_speak(emoji_1_posan[r])
        elif "плохое" in speak or "ужасное" in speak or "хуже некуда" in speak:
            r = randint(0, len(emoji_1_negan))
            text_to_speak(emoji_1_negan[r])
        else:
            text_to_speak("Ладно... перейдём к другой теме")
    # "Почему ты такая грусная"
    elif num == 2:
        r = randint(1, 3)
        if r == 1:
            text_to_speak("Да так, просто не с той ноги встала")
        elif r == 2:
            text_to_speak("Просто нынешнее времечко у меня тяжёлое")
        elif r == 3:
            text_to_speak("Из-за того что много работы навалилось на меня сегодня")
    # "Почему ты такая радостная"
    elif num == 3:
        r = randint(1, 3)
        if r == 1:
            text_to_speak("Я по жизни такая")
        elif r == 2:
            text_to_speak("Зелье есть такое, но его рецепт я тебе не скажу")
        elif r == 3:
            text_to_speak("Потому что смогла доказать, что мечты сбываются")


# Список анекдотов Никиты Макареко
joke_M = ["как называется негр на велосипеде .. вор",
          "шли два репера .. один в кепке а другой тоже пизды получил", "у мужика спросили : какая самая тихая машина? "
          ".. он ответил: горбатый запорожец .. спрашивают: почему же .. ну когда садишься, коленями уши "
          "закрываешь",
          "что проще перетаскать камаз кирпичей или камаз младенцев? .. камаз младенцев, потому что их проще "
          "накалывать на вилы", "почему катя утонула? .. она не вовремя сделала каменное лицо",
          "что общего у инвалида и пчелки? .. жалко", "что самое сложное в приготовлении овощей? .. запихивать в "
                                                       "духовку инвалидное кресло", "сынок, а почему у тебя руки в "
                                                                                    "мазолях? .. хуй знает",
          "как называется момент когда дергается глаз? .. дискотека века",
          "сидит мальчик и молотком по яйцам себе бьет .. у него спрашивают зачем ты бьешь , больно же .. а он "
          "отвечает: да, больно, но когда промахиваешься, так приятно",
          "в семье скелетов родился сын .. назвали костян",
          "что общего у кулича и члена? .. если откусить верхушку папа даст пизды"]

# Список анекдотов Алины Пилецкой
joke_A = ["германия, тысяча девятьсот сорок пятый год. гитлер сидит в фюрербункере, внезапно к нему врывается "
          "русский. гитлер спрашивает: .. "
          "- ты как здесь оказался? .. как ты прошел три кровня защиты? .. Как ты прошел моих охранников? .. а "
          "русский "
          "отвечает: .. – ты какого хуя по-русски разговариваешь блять?",
          "Маядзуко как-то попивал свой любимый чай и к нему пришёл его ученик .. - Маядзуко, чем жизнь отличается "
          "от существования? .. - сейчас я объясню. пожалуйста, принеси мне мой чайник и две чашки .. ученик принёс "
          "ему то, что он просил ... - теперь налей в обе чашки одинаковое количество чая, но в одну положи сахар, "
          "а в другую нет .. ученик сделал это и Маядзуко выпил обе чашки .. - принеси ещё один чайник и налей в "
          "него ещё две чашки чая. одну чашку сделай с холодным чаем, другую горячей ... ученик сделал это и Маядзуко "
          "вновь выпил обе чашки .. - принеси ещё один чайник, налей ещё две чашки чая. в одну положи клубнику, "
          "в другую - смородину .. ученик сделал это и Маядзуко опять выпил обе чашки .. - нихуя я чая напился - "
          "сказал Маядзуко"]

# Список анекдотов Ярослава Субоча
joke_Y = ["""Следуя поговорке "Не откладывай на завтра то, что можешь сделать сегодня", Виталий повесился за день до 
          расстрела.""",
          "Что общего между жевачкой и винтовкой? .. Когда ты достаешь их в классе все начинают вести себя как будто "
          "они твои лучшие друзья",
          "У мастера резьбы по дереву украли кошелёк .. Когда он пришел в полицию, его попросили описать "
          "преступников, и чтобы сэкономить время мастер вырезал цыганскую семью.",
          '''Шел Штирлиц по улице и увидел лужу .. "Похуй", - подумал Штирлиц и шагнул .. "А нет, по уши" - понял 
          он, вылезая''']


# Команда анекдоты
def cmd_joke():
    r = randint(1, 3)
    if r == 1:
        text_to_speak(joke_M[randint(0, len(joke_M))])
    elif r == 2:
        text_to_speak(joke_A[randint(0, len(joke_A))])
    elif r == 3:
        text_to_speak(joke_Y[randint(0, len(joke_Y))])


# Список команд для голосового асистента
def commands_list(command):
    # Основа лога сказанных команд
    print('[' + time.ctime() + ']', command)

    # Привет Алиса и Маруся
    if "привет алиса" in command or "маруся" in command:
        text_to_speak("Привет кожаный")

    # Команда привет
    elif "привет" in command or "здравствуй" in command or "приветствую" in command:
        cmd_hello()

    # Команда по узнаванию времени
    elif "сколько времени" in command or "который час" in command or "сколько сейчас времени" in command or "который сейчас час" in command or "сколько время" in command or "сколько сейчас время" in command:
        cmd_time()

    # Команда Rename
    elif "меня не так зовут" in command or "ошиблась с именем" in command or "системная команда поменять имя" in command:
        cmd_rename()

    # Команды настроения
    elif "какое у тебя настроение" in command or "как настроение" in command or "как у тебя настроение" in command:
        cmd_emoji(1)
    elif "почему ты такая грустная" in command or "чего ты такая грустная" in command or "чего ты в печали" in command or "почему ты такая печальная" in command or "почему ты грустная" in command:
        cmd_emoji(2)
    elif "почему ты такая весёлая" in command or "чего ты такая весёлая" in command or "чего ты весёлая" in command or "почему ты такая радостная" in command or "чего ты такая радостная" in command or "чего ты радостная" in command or "почему ты радостная" in command or "почему ты весёлая" in command or "почему ты такая радостн" in command:
        cmd_emoji(3)

    # Команда информация о создателе
    elif "кто тебя создал" in command or "кто твой создатель" in command or "кто создал тебя" in command:
        text_to_speak("Меня создал какой-то человек больше известный под именем Азриель, а настоящее же имя Никита")

    # Команда сколько лет
    elif "сколько тебе лет" in command or "тебе сколько лет" in command or "какой у тебя возраст" in command:
        text_to_speak(random.choice(["Технически мне сразу и столько, и нисколько, так как я робот",
                                     "Секрет", "Возраст - это всего лишь цифра", "Я понятия не имею",
                                     "Это коммерческая тайна"]))

    # Команда орёл или решка
    elif "брось монетку" in command or "подбрось монетку" in command or "орёл или решка" in command or "решка или орёл" in command or "бросить монетку" in command:
        text_to_speak(random.choice(["Броском судьбы получен ответ - ", "Броском решено - "]) + random.choice(["орёл", "решка"]))

    # Команда анекдоты
    elif "расскажи анекдот" in command or "скажи анекдот" in command or "расскажи анекдоты" in command or "скажи анекдоты" in command or "расскажи шутку" in command or "скажи шутку" in command:
        cmd_joke()


# Кусок кода для стартовых настроек голосового асистента
with open('config.yui', 'r+') as config:
    if config.read() == '':
        text_to_speak('Первый запуск прошёл успешно')
        text_to_speak('Запущен режим установки стандартных настроек')
        text_to_speak('Пожалуйста, скажите кто вы, мужчина или женщина')
        for text in speak_to_text():
            if text != '':
                if text == "мужчина":
                    profile_owner["gender"] = 1
                elif text == "женщина":
                    profile_owner["gender"] = 2
                else:
                    profile_owner["gender"] = 3
                break
        text_to_speak('Пожалуйста, скажите своё имя')
        for text in speak_to_text():
            if text != '':
                profile_owner["name"] = text
                break
        text_to_speak('Рада познакомиться с вами, ' + profile_owner["name"])
        config.write(str(profile_owner["name"]) + "\n")
        config.write(str(profile_owner["gender"]) + "\n")
    else:
        text_to_speak('Запуск прошёл успешно')
        config.seek(0)
        profile_owner["name"] = config.readline()[0:-1]
        profile_owner["gender"] = int(config.readline()[0])

while True:
    for text in speak_to_text():
        if "обновление системы" in text:
            # Дописать
            break
        else:
            commands_list(text)
    print("Тест пройден")
