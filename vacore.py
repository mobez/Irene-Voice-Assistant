import os
import traceback
import hashlib

from termcolor import colored, cprint
import time

from threading import Timer

from jaa import JaaCore

version = "6.8"

# main VACore class

class VACore(JaaCore):
    def __init__(self):
        JaaCore.__init__(self)

        self.timers = [-1,-1,-1,-1,-1,-1,-1,-1]
        self.timersFuncUpd = [None,None,None,None,None,None,None,None]
        self.timersFuncEnd = [None,None,None,None,None,None,None,None]
        self.timersDuration = [0,0,0,0,0,0,0,0]

        self.commands = {
        }

        self.plugin_commands = {
        }

        self.ttss = {
        }

        self.playwavs = {
        }

        # more options
        self.mpcHcPath = ""
        self.mpcIsUse = False
        self.mpcIsUseHttpRemote = False

        self.isOnline = False
        self.version = version

        self.voiceAssNamesW = []
        self.voiceAssNamesM = []
        self.voiceId = ""
        self.floorM = False

        self.useTTSCache = False
        self.tts_cache_dir = "tts_cache"
        self.ttsEngineId = ""
        self.ttsEngineId2 = ""
        self.playWavEngineId = ""

        self.logPolicy = ""
        self.tmpdir = "temp"
        self.wavedir = "waves/"
        self.tmpcnt = 0

        self.lastSay = ""
        self.remoteTTS = "none"
        self.remoteTTSResult = None

        self.context = None
        self.contextTimer = None
        self.recTimer = None
        self.contextTimerLastDuration = 0

        self.contextDefaultDuration = 10
        self.contextRemoteWaitForCall = False

        self.recOld = False
        self.noncmd = False

        import mpcapi.core
        self.mpchc = mpcapi.core.MpcAPI()



    def init_with_plugins(self):
        self.init_plugins(["core"])
        self.display_init_info()

        self.setup_assistant_voice()

    # ----------- process plugins functions ------
    def process_plugin_manifest(self,modname,manifest):
        # is req online?
        plugin_req_online = True
        if "require_online" in manifest:
            plugin_req_online = manifest["require_online"]

        # adding commands from plugin manifest
        if "commands" in manifest: # process commands
            for cmd in manifest["commands"].keys():
                if not self.isOnline and plugin_req_online:
                    # special processing
                    self.commands[cmd] = self.stub_online_required
                else:
                    # normal add command
                    self.commands[cmd] = manifest["commands"][cmd]

                if modname in self.plugin_commands:
                    self.plugin_commands[modname].append(cmd)
                else:
                    self.plugin_commands[modname] = [cmd]

        # adding tts engines from plugin manifest
        if "tts" in manifest: # process commands
            for cmd in manifest["tts"].keys():
                self.ttss[cmd] = manifest["tts"][cmd]

        # adding playwav engines from plugin manifest
        if "playwav" in manifest: # process commands
            for cmd in manifest["playwav"].keys():
                self.playwavs[cmd] = manifest["playwav"][cmd]

    def stub_online_required(self,core,phrase):
        self.play_voice_assistant_speech(self.plugin_options("core")["replyOnlineRequired"])

    def print_error(self,err_txt,e:Exception = None):
        cprint(err_txt,"red")
        # if e != None:
        #     cprint(e,"red")
        import traceback
        traceback.print_exc()

    def print_red(self,txt):
        cprint(txt,"red")

    # ----------- text-to-speech functions ------

    def setup_assistant_voice(self):
        # init playwav engine
        try:
            self.playwavs[self.playWavEngineId][0](self)
        except Exception as e:
            self.print_error("Ошибка инициализации плагина проигрывания WAV (playWavEngineId)", e)
            self.print_red('Попробуйте установить в options/core.json: "playWavEngineId": "sounddevice"')
            self.print_red('...временно переключаюсь на консольный вывод ответа...')
            self.ttsEngineId = "console"

        # init tts engine
        try:
            self.ttss[self.ttsEngineId][0](self)
        except Exception as e:
            self.print_error("Ошибка инициализации плагина TTS (ttsEngineId)", e)
            cprint('Попробуйте установить в options/core.json: "ttsEngineId": "console" для тестирования вывода через консоль', "red")
            cprint('Позднее, если все заработает, вы сможете настроить свой TTS-движок', "red")

            from sys import platform
            if platform == "linux" or platform == "linux2":
                cprint("Подробнее об установке на Linux: https://github.com/janvarev/Irene-Voice-Assistant/blob/master/docs/INSTALL_LINUX.md", "red")
            elif platform == "darwin":
                cprint("Подробнее об установке на Mac: https://github.com/janvarev/Irene-Voice-Assistant/blob/master/docs/INSTALL_MAC.md", "red")
            elif platform == "win32":
                #cprint("Подробнее об установке на Linux: https://github.com/janvarev/Irene-Voice-Assistant/blob/master/docs/INSTALL_LINUX.md", "red")
                pass

            self.print_red('...временно переключаюсь на консольный вывод ответа...')
            self.ttsEngineId = "console"

        # init tts2 engine
        if self.ttsEngineId2 == "":
            self.ttsEngineId2 = self.ttsEngineId
        if self.ttsEngineId2 != self.ttsEngineId:
            try:
                self.ttss[self.ttsEngineId2][0](self)
            except Exception as e:
                self.print_error("Ошибка инициализации плагина TTS2 (ttsEngineId2)", e)

    def play_voice_assistant_speech(self,text_to_speech:str):
        self.lastSay = text_to_speech
        remoteTTSList = self.remoteTTS.split(",")

        self.remoteTTSResult = {}
        if "none" in remoteTTSList: # no remote tts, do locally anything
            #self.remoteTTSResult = "" # anywhere, set it ""

            if self.ttss[self.ttsEngineId][1] != None:
                self.ttss[self.ttsEngineId][1](self,text_to_speech)
            else:
                if self.useTTSCache:
                    tts_file = self.get_tts_cache_file(text_to_speech)
                else:
                    tts_file = self.get_tempfilename()+".wav"

                #print('Temp TTS filename: ', tts_file)
                if not self.useTTSCache or self.useTTSCache and not os.path.exists(tts_file):
                    self.tts_to_filewav(text_to_speech, tts_file)

                self.play_wav(tts_file)
                if not self.useTTSCache and os.path.exists(tts_file):
                    os.unlink(tts_file)

        if "saytxt" in remoteTTSList: # return only last say txt
            self.remoteTTSResult["restxt"] = text_to_speech

        if "saywav" in remoteTTSList:
            if self.useTTSCache:
                tts_file = self.get_tts_cache_file(text_to_speech)
            else:
                tts_file = self.get_tempfilename()+".wav"

            if not self.useTTSCache or self.useTTSCache and not os.path.exists(tts_file):
                self.tts_to_filewav(text_to_speech, tts_file)
            #self.play_wav(tts_file)
            import base64

            with open(tts_file, "rb") as wav_file:
                encoded_string = base64.b64encode(wav_file.read())

            if not self.useTTSCache and os.path.exists(tts_file):
                os.unlink(tts_file)

            self.remoteTTSResult["wav_base64"] = encoded_string


    def say(self,text_to_speech:str): # alias for play_voice_assistant_speech
        self.play_voice_assistant_speech(text_to_speech)

    def say2(self,text_to_speech:str): # озвучивает через второй движок
        if self.ttss[self.ttsEngineId2][1] != None:
            self.ttss[self.ttsEngineId2][1](self,text_to_speech)
        else:
            tempfilename = self.get_tempfilename()+".wav"
            #print('Temp TTS filename: ', tempfilename)
            self.tts_to_filewav2(text_to_speech,tempfilename)
            self.play_wav(tempfilename)
            if os.path.exists(tempfilename):
                os.unlink(tempfilename)


    def tts_to_filewav(self,text_to_speech:str,filename:str):
        if len(self.ttss[self.ttsEngineId]) > 2:
            self.ttss[self.ttsEngineId][2](self,text_to_speech,filename)
        else:
            print("File save not supported by this TTS")

    def tts_to_filewav2(self,text_to_speech:str,filename:str): # через второй движок
        if len(self.ttss[self.ttsEngineId2]) > 2:
            self.ttss[self.ttsEngineId2][2](self,text_to_speech,filename)
        else:
            print("File save not supported by this TTS")

    def get_tempfilename(self):
        self.tmpcnt += 1
        return self.tmpdir+"/vacore_"+str(self.tmpcnt)

    def get_tts_cache_file(self, text_to_speech:str):
        hash = hashlib.md5(text_to_speech.encode('utf-8')).hexdigest()
        text_slice = text_to_speech[:40]
        filename = ".".join([text_slice, hash, "wav"])
        return self.tts_cache_dir+"/"+self.ttsEngineId+"/"+filename

    def all_num_to_text(self,text:str):
        from utils.all_num_to_text import all_num_to_text
        return all_num_to_text(text)

    # -------- main function ----------

    def execute_next(self,command,context):
        if context == None:
            context = self.commands

        if isinstance(context,dict):
            pass
        else:
            # it is function to call!
            #context(self,command)
            self.context_clear()
            self.call_ext_func_phrase(command,context)
            return True

        try:
            # первый проход - ищем полное совпадение
            for keyall in context.keys():
                keys = keyall.split("|")
                for key in keys:
                    if command == key:
                        rest_phrase = ""
                        next_context = context[keyall]
                        self.execute_next(rest_phrase,next_context)
                        return True

            # второй проход - ищем частичное совпадение
            for keyall in context.keys():
                keys = keyall.split("|")
                for key in keys:
                    if command.startswith(key):
                        rest_phrase = command[(len(key)+1):]
                        next_context = context[keyall]
                        self.execute_next(rest_phrase,next_context)
                        return True


            # if not founded
            if self.context == None:
                # no context
                if self.noncmd or not self.recOld:
                    if self.floorM:
                        self.say(self.plugin_options("core")["replyNoCommandFoundInContextM"])
                    else:
                        self.say(self.plugin_options("core")["replyNoCommandFoundInContextW"])
                else:
                    if self.floorM:
                        self.say(self.plugin_options("core")["replyNoCommandFoundM"])
                    else:
                        self.say(self.plugin_options("core")["replyNoCommandFoundW"])
            else:
                # in context
                if self.floorM:
                    self.say(self.plugin_options("core")["replyNoCommandFoundInContextM"])
                else:
                    self.say(self.plugin_options("core")["replyNoCommandFoundInContextW"])
                # restart timer for context
                if self.contextTimer != None:
                    self.context_set(self.context,self.contextTimerLastDuration)
        except Exception as err:
            print(traceback.format_exc())
        return False

    # ----------- timers -----------
    def set_timer(self, duration, timerFuncEnd, timerFuncUpd = None):
        # print "Start set_timer!"
        curtime = time.time()
        for i in range(len(self.timers)):
            if self.timers[i] <= 0:
                # print "Found timer!"
                self.timers[i] = curtime+duration  #duration
                self.timersFuncEnd[i] = timerFuncEnd
                print("New Timer ID =", str(i), ' curtime=', curtime, 'duration=', duration, 'endtime=', self.timers[i])
                return i
        return -1  # no more timer valid

    def clear_timer(self, index, runEndFunc=False):
        if runEndFunc and self.timersFuncEnd[index] != None:
            self.call_ext_func(self.timersFuncEnd[index])
        self.timers[index] = -1
        self.timersDuration[index] = 0
        self.timersFuncEnd[index] = None

    def clear_timers(self): # not calling end function
        for i in range(len(self.timers)):
            if self.timers[i] >= 0:
                self.timers[i] = -1
                self.timersFuncEnd[i] = None

    def _update_timers(self):
        curtime = time.time()
        for i in range(len(self.timers)):
            if(self.timers[i] > 0):
                if curtime >= self.timers[i]:
                    print("End Timer ID =", str(i), ' curtime=', curtime, 'endtime=', self.timers[i])
                    self.clear_timer(i,True)

    # --------- calling functions -----------

    def call_ext_func(self,funcparam):
        if isinstance(funcparam,tuple): # funcparam =(func, param)
            funcparam[0](self,funcparam[1])
        else: # funcparam = func
            funcparam(self)

    def call_ext_func_phrase(self,phrase,funcparam):
        if isinstance(funcparam,tuple): # funcparam =(func, param)
            funcparam[0](self,phrase,funcparam[1])
        else: # funcparam = func
            funcparam(self,phrase)

    # ------- play wav from subfolder ----------
    def play_wav(self,wavfile):
        self.playwavs[self.playWavEngineId][1](self,wavfile)


    # -------- raw txt running -----------------
    def run_input_str(self,voice_input_str,func_before_run_cmd = None): # voice_input_str - строка распознавания голоса, разделенная пробелами
                # пример: "ирина таймер пять"
        haveRun = False
        if voice_input_str == None:
            return False

        if self.logPolicy == "all":
            if self.context == None:
                print("Input: ",voice_input_str)
            else:
                print("Input (in context): ",voice_input_str)

        try:
            voice_input = voice_input_str.split(" ")
            #callname = voice_input[0]
            haveRun = False
            nameOk = False
            if self.context == None:
                for ind in range(len(voice_input)):
                    callname = voice_input[ind]

                    if callname in self.voiceAssNamesW: # найдено имя ассистента
                        self.noncmd = False
                        self.timeoutCancel()
                        nameOk = True
                        self.floorM = False
                        self.voiceId = self.plugin_options("core")["voiceIdW"]
                    if callname in self.voiceAssNamesM: # найдено имя ассистента
                        self.noncmd = False
                        self.timeoutCancel()
                        nameOk = True
                        self.floorM = True
                        self.voiceId = self.plugin_options("core")["voiceIdM"]
                    if self.recOld or nameOk:
                        if self.logPolicy == "cmd":
                            print("Input (cmd): ",voice_input_str)
                        if self.recOld:
                            command_options = " ".join([str(input_part) for input_part in voice_input[(ind):len(voice_input)]])
                        else:
                            if (ind+1 >= len(voice_input)):
                                self.recOld = True
                                self.timeoutSet(15)
                                print("Null mess!")
                            command_options = " ".join([str(input_part) for input_part in voice_input[(ind+1):len(voice_input)]])

                        # running some cmd before run cmd
                        if func_before_run_cmd != None:
                            func_before_run_cmd()


                        #context = self.context
                        #self.context_clear()
                        self.timeoutSet(15)
                        self.execute_next(command_options, None)
                        self.noncmd = True
                        haveRun = True
                        break
            else:
                if self.logPolicy == "cmd":
                    print("Input (cmd in context): ",voice_input_str)
                else:
                    print("Input: ",voice_input_str)

                # running some cmd before run cmd
                if func_before_run_cmd != None:
                    func_before_run_cmd()

                self.execute_next(voice_input_str, self.context)

                haveRun = True
        except Exception as err:
            print(traceback.format_exc())
        #if not haveRun:
            #print("Input: ",voice_input_str)

        return haveRun

    # ------------ context handling functions ----------------

    def timeoutCancel(self):
        self.recOld = False
        if self.recTimer != None:
            self.recTimer.cancel()
            self.recTimer = None

    def timeoutSet(self, duration = None):
        if duration == None:
            duration = self.contextDefaultDuration
        self.timeoutCancel()
        self.recOld = True
        self.recTimer = Timer(duration,self._recEnd)
        self.recTimer.start()

    def _recEnd(self):
        self.timeoutCancel()
        self.recOld = False
        self.noncmd = False
        print("Rec timeout")
        tts_file = self.wavedir+"tethys.wav"
        self.play_wav(tts_file)


    def context_set(self,context,duration = None):
        if duration == None:
            duration = self.contextDefaultDuration

        self.context_clear()

        self.context = context
        self.contextTimerLastDuration = duration
        self.contextTimer = Timer(duration,self._context_clear_timer)

        remoteTTSList = self.remoteTTS.split(",")
        if self.contextRemoteWaitForCall and ("saytxt" in remoteTTSList or "saywav" in remoteTTSList):
            pass # wait for run context timer
        else:
            self.contextTimer.start()


    #def _timer_context
    def _context_clear_timer(self):
        print("Context cleared after timeout")
        self.contextTimer = None
        self.context_clear()
        if self.recTimer != None:
            self.recTimer.cancel()
            self.recTimer = None
            self.timeoutSet()

    def context_clear(self):
        self.context = None
        if self.contextTimer != None:
            self.contextTimer.cancel()
            self.contextTimer = None
        if self.recTimer != None:
            self.recTimer.cancel()
            self.recTimer = None
            self.timeoutSet()

    # ----------- display info functions ------

    def display_init_info(self):
        cprint("VoiceAssistantCore v{0}:".format(version), "blue", end=' ')
        print("run ONLINE" if self.isOnline else "run OFFLINE")

        self.format_print_key_list("TTS engines", self.ttss.keys())
        self.format_print_key_list("Assistant names", self.voiceAssNamesW)

        cprint("Commands list: "+"#"*65, "blue")
        for plugin in self.plugin_commands:
            self.format_print_key_list(plugin, self.plugin_commands[plugin])
        cprint("#"*80, "blue")

    def format_print_key_list(self, key:str, value:list):
        print(colored(key+": ", "blue")+", ".join(value))
