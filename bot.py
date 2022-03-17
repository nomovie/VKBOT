import vk_api, random
import sqlite3 as sql
import string
import numpy as np

from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType, VkBotMessageEvent

def make_pairs(massive):
    for i in range(len(massive)-1):
        yield (massive[i], massive[i+1])
        
def generate_chain(massive):
    pairs = make_pairs(massive)
    
    word_dict = {}
    for word_first, word_second in pairs:
        if word_first in word_dict.keys():
            word_dict[word_first].append(word_second)
        else:
            word_dict[word_first] = [word_second]
        
    first_word = np.random.choice(massive)
        
    #while first_word.islower():
        #first_word = np.random.choice(massive)
        
    chain = [first_word]
    words_count = random.randint(1, 7)
        
    for i in range(words_count):
        try:
            chain.append(np.random.choice(word_dict[chain[-1]]))    
        except KeyError as ke:
            if i == words_count:
                return ke
        
    return ' '.join(map(str, chain))

class Server:
    def __init__(self, token, group_id):
        
        print("[+] Запуск бота")
        print("[+] Бот запущен, версия 0.05")
        
        self.vk = vk_api.VkApi(token=token)
        self.longpoll = VkBotLongPoll(self.vk, group_id=group_id)
        self.api = self.vk.get_api()
        self.msg = 0
        self.next_msg = 1
        
    def connect(self):
        print('[+] Подключение к базе данных')
        self.db = sql.connect("chats.db")
        
    def create(self, chat_id):
        with self.db:
            cursor = self.db.cursor()
            cursor.execute(f"CREATE TABLE IF NOT EXISTS `chat_id{chat_id}` (`message` STRING)")
            print("[+] Создал новую базу данных")
            self.db.commit()
            cursor.close()
        
    def insert(self, chat_id, message):
        with self.db:
            cursor = self.db.cursor()
            cursor.execute(f"INSERT INTO `chat_id{chat_id}` VALUES (?)", (message,))
            self.db.commit()
            cursor.close()
    
    def valid(self, chat_id):
        with self.db:
            cursor = self.db.cursor()
            
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='chat_id{chat_id}'")
            
            if cursor.fetchone() == None:
                self.db.commit()
                cursor.close()
                print(f'[!] База данных для чата  chat_id{chat_id} не найдена')
                return False
            else:
                self.db.commit()
                cursor.close()
                return True
    
    def get_messages(self, chat_id):
        with self.db:
            cursor = self.db.cursor()
            cursor.execute(f"SELECT * FROM chat_id{chat_id}")
            
            list = [list[0] for list in cursor.fetchall()]
            cursor.close()
            return list;
    
    def generate_random_message(self, chat_id):
        msg_randomize = 0#random.randint(0, 1)
        
        if msg_randomize == 0:
            messages = self.get_messages(chat_id)
            
            return generate_chain(messages)#return messages[random.randint(1, len(messages) - 1)]
            
    def is_string_invalid(self, msg):
        return bool(not msg or msg == None or msg == "" or msg == " ")
    
    def cmd_clear(self, event, admin_id, chat_id):
        if event.message.from_id == admin_id:
            if event.message.text[0:6] == "/clear":
                
                with self.db:
                    cursor = self.db.cursor()
                    cursor.execute(f'DELETE FROM chat_id{chat_id};',)
                
                    self.db.commit()
                    cursor.close()
                    self.api.messages.send(chat_id=chat_id,message='База сообщений беседы очищена.', random_id=0)                
            else:
                self.api.messages.send(chat_id=chat_id,message='Ошибка. Вы не являетесь Администратором!', random_id=0)    
            
    def join(self):
        self.connect()
        
        for event in self.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                
                #if event.from_user:
                    #self.api.messages.send(user_id=event.peer_id, message='Привет, добавь меня в свою беседу, в личку я не отвечаю!', random_id=0)
                
                #self.cmd_clear(event, 362084469, event.chat_id)                
                if event.from_chat:
                    if self.valid(event.chat_id):
                        
                        if not self.is_string_invalid(event.message.text):
                            self.insert(event.chat_id, event.message.text)
                            print('[+] Записал сообщение')
                        
                        self.msg += 1
                        if self.msg == self.next_msg:
                            self.msg = 0
                            self.next_msg = random.randint(1, 10)
                            message = self.generate_random_message(event.chat_id)
                            
                            if self.is_string_invalid(message):
                                print('[-] Ошибка отправки, сообщение пустое')
                            else:
                                print(f"[+] Отправил сообщение в чат 'chat_id{event.chat_id}'")
                                self.api.messages.send(chat_id=event.chat_id,message=message, random_id=0)
                    else:
                        self.create(event.chat_id)
                        if not self.is_string_invalid(event.message.text):
                            self.insert(event.chat_id, event.message.text)
                            print('[+] Записал сообщение')
                  

server = Server('токен группы', ид группы)
server.join()
