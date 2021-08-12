import urllib.parse
import time
import math
import threading
import chromedriver_autoinstaller
from selenium import webdriver

class Translated:
    def __init__(self,source,target,origin,text,pronunciation):
        self.source = source
        self.target = target
        self.origin = origin
        self.text = text
        self.pronunciation = pronunciation
        
    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return (
            u'Translated(source={source}, target={target}, text={text}, pronunciation={pronunciation})'.format(
                source=self.source, target=self.target, text=self.text,
                pronunciation=self.pronunciation))
        
class Detected:
    def __init__(self,source):
        self.source = source
        
    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return (u'Detected(source={source})'.format(source=self.source))
            
class Translator(object):
    def __init__(self,num_worker = 1,sleep_time=0.01,wait_time = 0.1,timeout=10):
        self.LANGUAGES = {'auto': '언어감지',
                          'ko': '한국어',
                          'en': '영어',
                          'ja': '일본어',
                          'zh-CN': '중국어(간체)',
                          'zh-TW': '중국어(번체)',
                          'es': '스페인어',
                          'fr': '프랑스어',
                          'de': '독일어',
                          'ru': '러시아어',
                          'pk': '포루투칼어',
                          'it': '이탈리아어',
                          'vi': '베트남어',
                          'th': '태국어',
                          'id': '인도네시아어',
                          'hi': '힌디어'}
        
        self.REVERSE_LANGUAGES = {'언어감지': 'auto',
                                  '한국어': 'ko',
                                  '영어': 'en',
                                  '일본어': 'ja',
                                  '중국어(간체)': 'zh-CN',
                                  '중국어(번체)': 'zh-TW',
                                  '스페인어': 'es',
                                  '프랑스어': 'fr',
                                  '독일어': 'de',
                                  '러시아어': 'ru',
                                  '포루투칼어': 'pk',
                                  '이탈리아어': 'it',
                                  '베트남어': 'vi',
                                  '태국어': 'th',
                                  '인도네시아어': 'id',
                                  '힌디어': 'hi'}
        self.sleep_time = sleep_time
        self.wait_time = wait_time
        self.timeout = timeout
        self.drivers = []
        
        self.chrome_ver = chromedriver_autoinstaller.get_chrome_version().split('.')[0]
        self.opt = webdriver.ChromeOptions()
        self.opt.add_argument("headless")
        self.set_drivers(max(1,num_worker))
        
    def translate(self, texts, source='auto', target='ko',honour = False,num_worker = None):
        if source not in self.LANGUAGES:
            raise Exception('This source languages is not supported')
        if target not in self.LANGUAGES or target == 'auto':
            raise Exception('This target languages is not supported')
        
        num_worker = num_worker if num_worker != None else len(self.drivers)
        
        self.set_drivers(max(1,num_worker))
        if type(texts) == str:
            texts = [texts]
        self.result = [None] * len(texts)
        for i in range(math.ceil(len(texts)/num_worker)):
            threads = []
            for j in range(0,len(texts[i*num_worker:(i+1)*num_worker])):
                idx = (num_worker*i)+j
                t = threading.Thread(target=self._translate,args=(texts[idx],source,target,honour,j,idx,))
                t.start()
                threads.append(t)
                for thread in threads:
                    thread.join() 
                    
        if len(self.result) > 1 or len(self.result) == 0:
            out = self.result
        else:
            out = self.result[0]
            
        del self.result
        return out
    
    def detect(self,texts,num_worker = None):
        num_worker = num_worker if num_worker != None else len(self.drivers)
        self.set_drivers(max(1,num_worker))
        if type(texts) == str:
            texts = [texts]
        self.result = [None] * len(texts)
        for i in range(math.ceil(len(texts)/num_worker)):
            threads = []
            for j in range(0,len(texts[i*num_worker:(i+1)*num_worker])):
                idx = (num_worker*i)+j
                t = threading.Thread(target=self._detect,args=(texts[idx],j,idx,))
                t.start()
                threads.append(t)
                for thread in threads:
                    thread.join() 
                    
        if len(self.result) > 1 or len(self.result) == 0:
            out = self.result
        else:
            out = self.result[0]
            
        del self.result
        return out    
    
    def _translate(self,text, source, target,honour,driver_idx,result_idx):
        out = self.loading(text,source,target,honour,driver_idx,result_idx)
        sl,tl = self.get_language(driver_idx,result_idx)
        pronunciation = self.get_pronunciation(driver_idx,result_idx)
        self.result[result_idx] =  Translated(sl, tl,text, out,pronunciation)
    
    def _detect(self,text,driver_idx,result_idx):
        _ = self.loading(text,'auto','ko',True,driver_idx,result_idx)
        sl,_ = self.get_language(driver_idx,result_idx)
        self.result[result_idx] = Detected(sl)
            
    def loading(self,text,source,target,honour,idx,result_idx):
        if len(text) > 5000:
            raise Exception(f'texts[{result_idx}]:Input must be less than 5000 characters.')
        if type(text) != str:
            raise Exception(f'texts[{result_idx}]:The type of input must be str.')
        
        honour = 1 if honour else 0
        papago_url = f'https://papago.naver.com/?sk={source}&tk={target}&hn={honour}&st={urllib.parse.quote(text)}' 
        self.drivers[idx].get(papago_url)
        while True:
            self.wait(idx,result_idx)
            if '&st=' not in self.drivers[idx].current_url:
                return text
            try:
                self.drivers[idx].find_element_by_css_selector('.err_area___3BqJr')
                return text
            except: 
                out = self.drivers[idx].find_element_by_css_selector('div#txtTarget').text
            if out != '' and (out!='...' or text == '...'):
                return out
        
    def wait(self,idx,result_idx):
        past_time = time.time()
        now_time = past_time
        past_num = len(self.drivers[idx].execute_script("return window.performance.getEntries();"))
        while True:
            time.sleep(self.sleep_time)
            if (time.time() -  past_time) > self.timeout:
                raise Exception(f'texts[{result_idx}]:Time Out')
            if len(self.drivers[idx].execute_script("return window.performance.getEntries();")) != past_num:
                past_num = len(self.drivers[idx].execute_script("return window.performance.getEntries();"))
                now_time = time.time()
            if (time.time() - now_time) > self.wait_time:
                break
    
    def get_language(self,idx,result_idx):
        sl = self.drivers[idx].find_element_by_css_selector('button#ddSourceLanguageButton').text
        tl = self.drivers[idx].find_element_by_css_selector('button#ddTargetLanguageButton').text
        if ' 감지' in sl:
            sl = sl[:-3]
        return self.REVERSE_LANGUAGES[sl],self.REVERSE_LANGUAGES[tl]
    
    def get_pronunciation(self,idx,result_idx):
        try:
            try:
                self.drivers[idx].find_element_by_id('sourceEditArea').find_element_by_css_selector('.diction_text___1alha').find_element_by_css_selector('em').click()
                self.wait(idx,result_idx)
            except:
                pass
            sp = self.drivers[idx].find_element_by_id('sourceEditArea').find_element_by_css_selector('.diction_text___1alha').text
        except:
            sp = None
        
        try:
            try:
                self.drivers[idx].find_element_by_id('targetEditArea').find_element_by_css_selector('.diction_text___1alha').find_element_by_css_selector('em').click()
                self.wait(idx,result_idx)
            except:
                pass
            tp = self.drivers[idx].find_element_by_id('targetEditArea').find_element_by_css_selector('.diction_text___1alha').text
        except:
            tp = None
        return {'source pronunciation':sp,'target pronunciation':tp}
    
    def set_drivers(self,num_worker):
        num_worker = max(0,num_worker)
        len_driver = len(self.drivers)
        thread_num = abs(len(self.drivers) - num_worker)
        threads = []
        if len_driver < num_worker:
            self.drivers = self.drivers + ([None] * thread_num)
            for i in range(0,thread_num):
                t = threading.Thread(target=self._start,args=(len_driver + i,))
                t.start()
                threads.append(t)

            for thread in threads:
                thread.join()
            
        if len_driver > num_worker:
            for i in range(1,thread_num+1):
                t = threading.Thread(target=self._quit,args=(len_driver - i,))
                t.start()
                threads.append(t)

            for thread in threads:
                thread.join()
            del self.drivers[-thread_num:]
            
    def all_quit(self):
        self.set_drivers(0)
            
    def _start(self,idx):
        try:
            self.drivers[idx] = webdriver.Chrome(f'./{self.chrome_ver}/chromedriver.exe',options=self.opt)   
        except:
            chromedriver_autoinstaller.install(True)
            self.drivers[idx] = webdriver.Chrome(f'./{self.chrome_ver}/chromedriver.exe',options=self.opt)
    
    def _quit(self,idx):
        self.drivers[idx].quit()
            
def test():
    translator = Translator()
    print(translator.translate(['Hello, world!']))
    print(translator.detect(['Hello, world!']))
    print(translator.translate(['Hello','world!']))
    print(translator.detect(['Hello','world!']))
    translator.all_quit()

test()
