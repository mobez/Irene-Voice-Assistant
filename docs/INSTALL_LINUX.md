# Настройка под Linux

### Некоторые проблемы при установке под Linux

Говорят, что требуется:
```apt install portaudio19-dev```

Также есть проблемы с запуском TTS движка. Варианта 2:

**1 вариант. Оставить pyttsx**

pyttsx идет по умолчанию.

Под него нужно ```apt install espeak-ng```

Далее в плагине plugins/plugin_tts_pyttsx.py поменять строку на
core.ttsEngine.setProperty("voice", "russian") либо найти нужный id языка
и установить его в options/plugin_tts_pyttsx.json sysId

Тогда звук будет идти через espeak-ng, и говорят, он не очень на русском.

**2 вариант. Поставить TTS rhvoice_rest и запустить Докер для rhvoice_rest**

Прстой вариант, чтобы не париться с зависимостями.
1. Установите в options/core.json "ttsEngineId": "rhvoice_rest"
2. Использует докер-сервер https://github.com/Aculeasis/rhvoice-rest для
   генерации голоса. Зайдите туда и запустите нужный вам докер.



**3 вариант. Поставить TTS rhvoice**

1. Скопируйте plugin_tts_rhvoice из plugins_active в plugins
2. Установите в options/core.json "ttsEngineId": "rhvoice"
3. Посмотрите в [PLUGINS.md](/docs/PLUGINS.md), что нужно для плагина rhvoice.

На Linux-системе говорят, что для установки rhvoice-wrapper-bin
требуется
```
apt install libspeechd-dev
pip3 install scons lxml
pip3 install rhvoice-wrapper
pip3 install rhvoice-wrapper-bin
```
 
Проблемы обсуждались в этой ветке комментариев: https://habr.com/ru/post/595855/#comment_24043171

**Важно:** если соберетесь использовать rhvoice, переключите настройку в core.json:
`"playWavEngineId": "sounddevice",`
потому что через audioplayer не проигрывает WAV по неизвестным причинам.
Либо `"playWavEngineId": "aplay"`.

Для добавления демона rc.local в ubuntu - https://linuxhint.com/use-rc-local-on-ubuntu/ и https://www.baeldung.com/linux/bash-daemon-script и https://microtechnics.ru/avtozapusk-skripta-na-raspberry-pi/
В ```rc.local прописать cd до папки с Ириной```, и ```sudo python3 runva_ulica.py &``` до "exit 0"
Команды:
```

sudo nano /etc/rc.local
sudo chmod +x /etc/rc.local
sudo nano /etc/systemd/system/rc-local.service
sudo chmod +x /etc/systemd/system/rc-local.service
sudo systemctl enable rc-local
sudo systemctl start rc-local.service
sudo systemctl stop rc-local.service
sudo systemctl restart rc-local.service
sudo systemctl reload rc-local.service
sudo systemctl status rc-local

```

Для убирания шумов с микрофона: https://askubuntu.ru/questions/451062/belyj-shum-v-mikrofone-s-ubuntu-20-04
```/etc/modprobe.d/alsa-base.conf :```
```
options snd-hda-intel position_fix=3
# https://help.ubuntu.com/community/HdaIntelSoundHowto
options snd-hda-intel model=laptop-amic

# https://bugzilla.kernel.org/show_bug.cgi?id=205959
options snd-intel-dspcfg dsp_driver=1
```

Проверка микрофона: https://losst.pro/zapis-s-mikrofona-v-linux
```sudo arecord output.wav``` -> ```sudo aplay output.wav```

Не забыть настроить звук и микрофон:
```
cat /proc/asound/card0/codec* | grep Codec
sudo arecord -l
sudo apt-get install alsa-utils
sudo alsamixer

```
