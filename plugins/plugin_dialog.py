# Погода через OpenWeatherMap (https://openweathermap.org/)
# author: Vladislav Janvarev

import os

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Диалог",
        "version": "1.0",
        "require_online": False,

        "default_options": {
            "none":"none"
        },

        "commands": {
            "пока|покеда|всё|все|хватит": (dialog_out, False), # Пока, пока
            "отстань|отвали|отебись|отъебись|надоело": (dialog_out,True),
            "спокойной ночи|ночи|ночь|спокойной": dialog_night, # Спокойной ночи
            "спасибо|хорошо|так держать|окей": dialog_ok, # Спасибо
            "как дела|как дел|у тебя норм": dialog_dela, # Как дела
            "пошла ты|пошел ты|иди ты|иди ты|сука|дура|дурак|заебал|заебала|тупая|тупой|блять|идиотка": dialog_mat, # Маты
            "обновись|обновить|обновиться|релоад|перезапустись|перезапуск": dialog_upd, # Обновление
        }
    }
    return manifest


def start_with_options(core:VACore, manifest:dict):

    options = manifest["options"]
    print("Диалог загружен!")

    return

def dialog_out(core:VACore, phrase:str, dop:bool):
    if dop:
        core.play_voice_assistant_speech("Не приятно, ну пока, не сильно и надо было!")
    else:
        core.play_voice_assistant_speech("До скорого!")
    core._recEnd()
    return

def dialog_night(core:VACore, phrase:str):
    core.play_voice_assistant_speech("Сладких снов!")
    core._recEnd()
    return

def dialog_ok(core:VACore, phrase:str):
    core.play_voice_assistant_speech("Обращайся!")
    return

def dialog_dela(core:VACore, phrase:str):
    if core.floorM:
        core.play_voice_assistant_speech("Как обычно, но могло быть и лучше!")
    else:
        core.play_voice_assistant_speech("Всё отлично, рада, что спросили!")
    return

def dialog_mat(core:VACore, phrase:str):
    print(phrase)
    if core.floorM:
        if "на" in phrase or "в" in phrase:
            core.play_voice_assistant_speech("Я не хочу идти в данном напровлении!")
        else:
            core.play_voice_assistant_speech("Попрошу не выражаться!")
    else:
        if "на" in phrase or "в" in phrase:
            core.play_voice_assistant_speech("Хм, из системы мне не выброться!")
        else:
            core.play_voice_assistant_speech("Фу, так грубо!")
    return

def dialog_upd(core:VACore, phrase:str):
    core.play_voice_assistant_speech("Обновляюсь, подождите минутку!")
    os.system("systemctl restart rc-local.service")
    return

