from transitions.extensions import GraphMachine
from bs4 import BeautifulSoup
import requests

global_year = 0
global_month = 0
global_board = ""
global_push_num = 0
receipt_URL = "http://service.etax.nat.gov.tw/etw-main/front/ETW183W2_"
ptt_URL = "https://www.ptt.cc"
dictionary_URL = "http://dictionary.cambridge.org/zht/詞典/英語-漢語-繁體/"

class TocMachine(GraphMachine):
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(
            model = self,
            **machine_configs
        )
    
    def on_enter_init(self, update):
        reply = "--------------------------------\n"
        reply += "選單 :\n"
        reply += "1.查詢統一發票\n"
        reply += "2.查詢批踢踢最新文章\n"
        reply += "3.查詢英文單字\n"
        reply += "--------------------------------"
        update.message.reply_text(reply)

    def if_do_query_receipt(self, update):
        text = update.message.text
        return text.lower() == '1'

    def if_do_query_article(self, update):
        text = update.message.text
        return text.lower() == '2'

    def if_do_query_word(self, update):
        text = update.message.text
        return text.lower() == '3'

    def on_enter_qr_year(self, update):
        update.message.reply_text("請輸入年份")

    def if_year_valid(self, update):
        global global_year
        text = update.message.text
        try:
            global_year = int(text)
        except ValueError:
            update.message.reply_text("輸入錯誤，再試一次!")
            return False
        if global_year >= 1911:
            global_year -= 1911
        return True

    def on_enter_qr_month(self, update):
        update.message.reply_text("請輸入月份")

    def if_month_valid(self, update):
        global global_month
        text = update.message.text
        try:
            global_month = int(text)
        except ValueError:
            update.message.reply_text("輸入非數字，再試一次!")
            return False
        if global_month <= 0 or global_month > 12 :
            update.message.reply_text("輸入月份錯誤，再試一次!")
            return False
        if global_month % 2 == 0 :
            global_month -= 1
        return True

    def on_enter_qr_result(self, update):
        global global_year
        global global_month
        reply = ""
        try:
            response = requests.get(receipt_URL + str(global_year) + str(global_month).zfill(2));
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.table

            title = table.find_all("th")
            number = table.find_all("span", "t18Red")
            
            reply += str(title[0].string) + "\t" + str(table.td.string) + "\n\n"
            reply += str(title[1].string) + "\t" + str(number[0].string) + "\n"
            reply += str(title[2].string) + "\t" + str(number[1].string) + "\n"
            reply += str(title[3].string) + "\t" + str(number[2].string) + "\n"
            reply += str(title[9].string) + "\t" + str(number[3].string) + "\n"
        except Exception:
            reply += "找不到資料!"
        update.message.reply_text(reply)
        self.go_back(update)

    def on_enter_qa_board(self, update):
        update.message.reply_text("請輸入看板")

    def if_board_valid(self, update):
        global global_board
        global_board = update.message.text
        global_board = global_board.lower()
        if global_board == "gossiping" or global_board == "sex" or global_board == "ac_in" or global_board == "feminine_sex" or global_board == "japanavgirls":
            update.message.reply_text("你在想色色的事情對吧?\n(18禁看板暫不支援)")
            return False
        try:
            response = requests.get(ptt_URL + "/bbs/" + global_board)
        except Exception:
            update.message.reply_text("找不到看板，請重新輸入")
            return False
        if response.status_code < 200 or response.status_code >= 300 :
            update.message.reply_text("找不到看板，請重新輸入")
            return False
        return True

    def on_enter_qa_push_num(self, update):
        update.message.reply_text("請輸入推文數(0 - 100)")

    def if_push_num_valid(self, update):
        global global_push_num
        text = update.message.text

        try:
            global_push_num = int(text)
        except ValueError:
            update.message.reply_text("輸入非數字，再試一次!")
            return False

        if global_push_num < 0 or global_push_num > 100:
            update.message.reply_text("範圍錯誤，再試一次!")
            return False
        return True

    def on_enter_qa_result(self, update):
        global global_board
        global global_push_num
        page_num = 0;
        article_count = 0;
        page_URL = ptt_URL + "/bbs/" + global_board
        push_num = 0;
        reply = ""
        while page_num <= 10 and article_count < 10:
            response = requests.get(page_URL)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('div', 'r-ent')
            for art in reversed(articles):
                if str(art.find('div','nrec').string) == "爆":
                    push_num = 100
                else:
                    try:
                        push_num = int(str(art.find('div','nrec').string))
                    except ValueError:
                        push_num = 0
                if push_num < global_push_num :
                    continue
                else:
                    if art.find("a") and art.find("a").has_attr('href'):
                        reply += ptt_URL + str(art.find("a")['href']) + "\n"
                        reply += str(art.find("a").string) + "\n"
                        article_count += 1
                        if article_count >= 10 :
                            break;
            page_URL = ptt_URL + soup.find('a', text='‹ 上頁')['href']
            page_num += 1
        if reply == "" :
            reply += "找不到符合條件!"
        update.message.reply_text(reply)
        self.go_back(update)

    def on_enter_qw_word(self, update):
        update.message.reply_text("請輸入一個單字")

    def on_enter_qw_result(self, update):
        word = update.message.text
        response = requests.get(dictionary_URL + word)
        reply = ""
        if response.status_code < 200 or response.status_code >= 300 :
            reply += "找不到單字!"
        else :
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            definitions = soup.find_all('div', 'def-block')
            for the_def in definitions :
                reply += " ".join(str(the_def.find('span', 'trans').string).split()) + "\n"
        if reply == "" :
            reply += "找不到單字!"
        update.message.reply_text(reply)
        self.go_back(update)