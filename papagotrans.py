from selenium import webdriver
import chromedriver_autoinstaller
import urllib.parse
import time

class Translator(object):
    def __init__(self,sleep_time=0.01):
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
        self.alive_drive = False
        
    def translate(self, text, source='auto', target='ko'):
        if source not in self.LANGUAGES:
            raise Exception('This source languages is not supported')
        if target not in self.LANGUAGES or target == 'auto':
            raise Exception('This target languages is not supported')
            
        if len(text) > 5000:
            raise Exception('Input must be less than 5000 characters.')
        if type(text) != str:
            raise Exception('The type of input must be str.')    
            
        self.start()
        out = self.loading(text,source,target)
        sl,tl = self.get_language()
        return {'source':sl, 
                'target':tl, 
                'origin':text, 
                'text':out}
    
    def detect(self,text):
        if len(text) > 5000:
            raise Exception('Input must be less than 5000 characters.')
        if type(text) != str:
            raise Exception('The type of input must be str.')        

        self.start()
        _ = self.loading(text,'auto','ko')
        sl,_ = self.get_language()
        return {'source':sl}
            
    def loading(self,text,source,target):
        papago_url = f'https://papago.naver.com/?sk={source}&tk={target}&st={urllib.parse.quote(text)}' 
        self.driver.get(papago_url)
        while True:                   
            try:
                out = self.driver.find_element_by_css_selector('div#txtTarget').text
                if out == '' or out == '...':
                    time.sleep(self.sleep_time)
                    continue
                break
            except:
                try:
                    self.driver.find_element_by_css_selector('.err_area___3BqJr')
                    find_err_area = True
                except:
                    find_err_area = False
                if '&st=' not in self.driver.current_url or find_err_area:
                    return text
                time.sleep(self.sleep_time)
                continue
        return out
    
    def get_language(self):
        sl = self.driver.find_element_by_css_selector('button#ddSourceLanguageButton').text
        tl = self.driver.find_element_by_css_selector('button#ddTargetLanguageButton').text
        if ' 감지' in sl:
            sl = sl[:-3]
        return self.REVERSE_LANGUAGES[sl],self.REVERSE_LANGUAGES[tl]
    
    def start(self):
        if not(self.alive_drive):
            chrome_ver = chromedriver_autoinstaller.get_chrome_version().split('.')[0]  #크롬드라이버 버전 확인
            opt = webdriver.ChromeOptions()
            opt.add_argument("headless")
            try:
                self.driver = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe',options=opt)   
            except:
                chromedriver_autoinstaller.install(True)
                self.driver = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe',options=opt)
            self.alive_drive = True
    def quit(self):
        if self.alive_drive:
            self.driver.quit()
            self.alive_drive = False
            
def test():
    translator = Translator()
    print(translator.translate('Hello, world!'))
    print(translator.detect('Hello, world!'))
    translator.quit()
      

test()