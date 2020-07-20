import telegram
import sqlite3
import re
import time
from dateutil.parser import parse
from selenium import webdriver
from bs4 import BeautifulSoup
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

token='1278836862:AAGm-lHHhkDAlxjNN0L4y6SIAlpjeCAgZuM'
chat_unknown_id='-1001253133492'
bot = telegram.Bot(token=token)
driver = webdriver.Chrome('/Users/ui8yh/Downloads/chromedriver_win32/chromedriver')
conn=sqlite3.connect("notice.db",check_same_thread=False)
cur=conn.cursor()
sched = BlockingScheduler()

### database() stores the new announcement in the database.
def database(data_list):
    for data in data_list:
        cur.execute("insert into data values (?,?,?,?)", data)
    if (len(data_list) != 0):
        cur.execute('''UPDATE new_data SET title=?,date=? ,url=?  WHERE site=?''', (data[0], data[1], data[3], data[2]))
    conn.commit()

### telegram() communicate the new notice to the Telegram.
def telegram(data_list,stop_telegram):
    for data in data_list:
        if(stop_telegram==False):
            text=data[1]+"\n"+data[0]+"\n"+data[3]
            bot.sendMessage(chat_id=chat_unknown_id,text=text)

### is_new_site() determines if a site is newly entered.
def is_new_site(new_data_table_title):
    if(new_data_table_title=='random title'):
        return True
    else:
        return False

### find_site_num() returns how many sites are there.
def find_site_num():
    cur.execute("select * from list")
    list_table = cur.fetchall()
    index = len(list_table)
    return index

### find_list_table() returns database's list table variables
def find_list_table():
    cur.execute("select * from list")
    list_table = cur.fetchall()
    return list_table

### find_new_data_table() returns database's new_data table variables
def find_new_data_table():
    cur.execute("SELECT * FROM new_data")
    new_data_table = cur.fetchall()
    return new_data_table

### get_title(), get_date(), get_url(), get_site() are return notice's information
def get_title(tr,list_table_title):
    title = tr.select_one(list_table_title).text.strip()
    return title

def get_date(tr,list_table_date):
    try:
        date = parse(tr.select_one(list_table_date).text.strip()).date()
        date = date.strftime('%Y-%m-%d')
    except:
        print('no date')
        #date = datetime.today()
        #date = date.strftime('%Y-%m-%d')
        date='2000.00.00'
    return date

def get_url(tr,list_table_trs,list_table_url,list_table_notice_url,list_table_notice_url_append,list_table_url_mode):
    try:
        if (list_table_trs == list_table_notice_url):
            url = tr
        else:
            url = tr.select_one(list_table_notice_url)
        url = list_table_notice_url_append + re.findall("\d+", url[list_table_url_mode])[0]
    except:
        print('no url')
        url = list_table_url
    return url

def get_site(index):
    return index

### get_start(),get_end() limit the range of trs(notices) search
def get_start(new_data_table_title,list_table_start):
    if (is_new_site(new_data_table_title)):
        start = list_table_start
    else:
        start = 0
    return start

def get_end(trs,new_data_table_title,list_table_title):
    count=0
    for tr in trs:
        title = get_title(tr, list_table_title)
        if title == new_data_table_title:
            end = count
        count = count+1
    if (is_new_site(new_data_table_title)):
        end=len(trs)
    return end

### erase_repeat_data_list() removes the duplicate part of the list
def erase_repeat_data_list(data_list):
    new_list=[]
    for data in reversed(data_list):
        if data not in new_list:
            new_list.append(data)
    return new_list

### search() looks for new announcements on each site.
def search(index):
    data_list=[]
    new_data_table=find_new_data_table()
    new_data_table_title=new_data_table[index][0]
    new_data_table_date = new_data_table[index][1]
    list_table=find_list_table()
    list_table_url=list_table[index][0]
    list_table_trs=list_table[index][1]
    list_table_title=list_table[index][2]
    list_table_notice_url=list_table[index][3]
    list_table_notice_url_append=list_table[index][4]
    list_table_date=list_table[index][5]
    list_table_start=list_table[index][6]
    list_table_url_mode=list_table[index][7]
    driver.get(list_table_url)
    time.sleep(15)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    trs = soup.select(list_table_trs)
    for tr in trs[get_start(new_data_table_title,list_table_start):get_end(trs,new_data_table_title,list_table_title)]:
        title=get_title(tr,list_table_title)
        date=get_date(tr,list_table_date)
        url=get_url(tr,list_table_trs,list_table_url,list_table_notice_url,list_table_notice_url_append,list_table_url_mode)
        site=get_site(index)
        data=[]
        data.append(title), data.append(date), data.append(site), data.append(url)
        if (new_data_table_title != title):
            if (date >= new_data_table_date):
                print("NEW NOTICE!!!")
                print(data)
                data_list.append(data)
    data_list=erase_repeat_data_list(data_list)
    database(data_list)
    telegram(data_list,is_new_site(new_data_table_title))

### find_notice() looks for new announcements from sites in the existing database.
def find_notice():
    index=find_site_num()
    for i in range(index):
        print('now crawling index ', i)
        try :
            search(i)
        except :
            print(i,' site error')

### new_site() stores announcements from the new site in the database.
def new_site(index):
    url = input('Put new url : ')
    trs = input('Put new trs selector : ')
    title = input('Put new title selector : ')
    notice_url = input('Put new notice_url selector  : ')
    notice_url_append = input('Put new notice_url_append  : ')
    date = input('Put new date_selector : ')
    start_num = int(input('Put new start_num  : '))
    url_mode = input('Put new url_mode : ')
    lists = [url, trs, title, notice_url, notice_url_append, date, start_num, url_mode]
    cur.execute("insert into list values (?,?,?,?,?,?,?,?)", lists)
    new_data = ['random title', '2000-00-00', index, 'random url']
    cur.execute("insert into new_data values (?,?,?,?)", new_data)
    conn.commit()
    search(index)

if __name__=="__main__":
    find_notice()
    sched.add_job(find_notice, 'interval', minutes=30)
    sched.start()
    #new_site(find_site_num())

