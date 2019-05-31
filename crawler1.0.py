# coding: utf-8
# Author: Jaime
# 爬取臉書賬戶

# import sys
import time
import socket
import pymysql
# import platform
import contextlib

from pymysql.err import DataError

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


# from bs4 import BeautifulSoup

# -------------------------------------------------------------
# -------------------------------------------------------------


# 定义数据库参数
dbhost = '192.168.20.207'
dbport = 3306
dbuser = 'fu'
dbpwd = '123456'
dbdb = 'fb_users'
dbcharset = 'utf8mb4'

# 瀏覽器配置
options = Options()
options.add_argument("--disable-notifications")
options.add_argument("--disable-infobars")
options.add_argument("--mute-audio")
socket.setdefaulttimeout(60)

driver_title = webdriver.Chrome(executable_path="./chromedriver.exe", options=options)
wait_title = WebDriverWait(driver_title, 20, 0.5)
driver_details = webdriver.Chrome(executable_path="./chromedriver.exe", options=options)
wait_details = WebDriverWait(driver_details, 10, 0.5)

# 爬取用戶信息的元素地址
name = '// *[ @ id = "fb-timeline-cover-name"] / a'
eduwork = "//*[@id='pagelet_eduwork']/div"
previous = '//*[@id="pagelet_hometown"]/div/div[2]/ul'
favorites = '//*[@id="favorites"]/div[2]/table'
contact = '//*[@id="pagelet_contact"]/div/div/ul'

# -------------------------------------------------------------
# -------------------------------------------------------------


def main():

    global id_num
    num = 0
    with open("page.txt") as contents:
        for page in contents:
            page = page.strip()
            num += 1

            # 加載網頁（爬取用戶列表的初始網頁）
            url = ["https://www.facebook.com/" + page]
            driver_title.get(url[0])
            print('------------------------------------ Scanning No.' + str(num) + ' '
                  + str(page) + '\'s users ------------------------------------\n')
            with mysql() as cursor:
                cursor.execute("SELECT identifier FROM pages_info WHERE page_id = %s LIMIT 1", page)
                id_num = cursor.fetchone()['identifier']

            # 爬取並解析用戶列表
            smart_crawler_2()

            # 爬取用戶信息
            get_users_info()

            driver_title.quit()
    contents.close()

# -------------------------------------------------------------
# -------------------------------------------------------------


# 数据库自动连接自动关闭
@contextlib.contextmanager
def mysql(host=dbhost, port=dbport, user=dbuser, passwd=dbpwd, db=dbdb, charset=dbcharset):
    conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db, charset=charset)
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    try:
        yield cursor
    finally:
        conn.commit()
        cursor.close()
        conn.close()

# -------------------------------------------------------------
# -------------------------------------------------------------


# 強制等待快捷方式
def get_rest():
    time.sleep(3)

# -------------------------------------------------------------
# -------------------------------------------------------------


# 網頁滾動相關工具
def check_height():
    new_height = driver_title.execute_script("return document.body.scrollHeight")
    return new_height != old_height

# -------------------------------------------------------------
# -------------------------------------------------------------


def input_pages():

    with mysql() as cursor:
        cursor.execute("SELECT 1 FROM pages_info WHERE page_id=%s LIMIT 1", page)
        if not cursor.rowcount > 0:
            cursor.execute("INSERT INTO pages_info (page_id, identifier) VALUES (%s, %s)", (page, num))
        try:
            wait_title.until(ec.presence_of_element_located((By.XPATH, '//*[@id="entity_sidebar"]/div[2]/div[1]')))
            page_name = driver_title.find_element_by_xpath('//*[@id="entity_sidebar"]/div[2]/div[1]')
        except TimeoutException:
            wait_title.until(ec.presence_of_element_located((By.XPATH, '//*[@id="seo_h1_tag"]/a')))
            page_name = driver_title.find_element_by_xpath('//*[@id="seo_h1_tag"]/a')
        get_rest()
        cursor.execute("SELECT MAX(identifier) FROM pages_info")
        identifier = cursor.fetchone()
        cursor.execute("UPDATE pages_info SET page_name = %s, identifier = %s WHERE page_id = %s LIMIT 1",
                       (page_name.text, identifier['MAX(identifier)'] + 1, page))

# -------------------------------------------------------------
# -------------------------------------------------------------


# helper function: used to scroll the page
def scroll():

    global old_height
    old_height = 0

    total_scrolls = 500
    scroll_time = 60
    current_scrolls = 0

    while True:
        try:
            if current_scrolls == total_scrolls:
                return
            old_height = driver_title.execute_script("return document.body.scrollHeight")
            get_rest()
            driver_title.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            get_rest()
            WebDriverWait(driver_title, scroll_time, 0.05).until(lambda driver: check_height())
            try:
                more = driver_title.find_elements_by_xpath("//a[@class='_4sxc _42ft']")
                for item in more:
                    get_rest()
                    item.send_keys("\n")
            except TimeoutException:
                print('No.' + str(current_scrolls) + '\'s scroll is clear!')
            current_scrolls += 1
            print('This is No.' + str(current_scrolls) + '\'s scrolling!')
        except TimeoutException:
            break
    return

# -------------------------------------------------------------
# -------------------------------------------------------------


# 開始爬取用戶列表
def smart_crawler_2():

    # 先滾兩下
    driver_title.execute_script("window.scrollBy(0, 800)")
    get_rest()
    driver_title.execute_script("window.scrollBy(0, 800)")

    # 去彈窗
    try:
        wait_title.until(ec.presence_of_element_located((By.XPATH, "//*[@id='expanding_cta_close_button']"))).click()
    except TimeoutException:
        print('Go!')

    # 繼續開滾
    scroll()

    # 集合
    result = []

    element = driver_title.find_elements_by_xpath("//a[@class='_6qw4']")
    for user in element:
        href = user.get_attribute('href')
        if href[-1] == '/':
            href = href[:-1]
        href = href.split("/")[-1]
        result.append(href)

    # 存儲超链接列表
    f = open(r'result.txt', 'w', encoding='utf-8')  # 文件路径、操作模式、编码  # r''
    for user in result:
        f.write(user + "\n")
    f.close()
    print("\r\n扫描结果已写入到result.txt文件中\r\n")

# -------------------------------------------------------------
# -------------------------------------------------------------


# 計算某元素下元素個數
def count_of_eles(where, ele):

    get_rest()
    parent_element = driver_details.find_element_by_xpath(where)
    number = len(parent_element.find_elements_by_xpath("./" + ele))
    return number

# -------------------------------------------------------------
# -------------------------------------------------------------


# 獲取工作經歷與學歷信息
def get_eduwork_info():

    get_rest()
    result = [0, '', '', '']
    results = '暫無'
    try:
        result[0] = count_of_eles(eduwork, "div")
        for i in range(1, result[0] + 1):
            get_rest()
            eduwork_header = driver_details.find_element_by_xpath(eduwork + "/div[%s]/div" % i)
            if count_of_eles(eduwork + "/div[%s]/ul" % i, "li") > 1:
                lis = count_of_eles(eduwork + "/div[%s]/ul" % i, "li")
                eduwork_content = ''
                for j in range(1, lis + 1):
                    get_rest()
                    sub_content = driver_details.find_element_by_xpath(eduwork + "/div[%s]/ul/li[%s]" % (i, j))
                    eduwork_content = eduwork_content + str('%s. ' % j) + sub_content.text.replace('\n', '，') + '；'
            else:
                get_rest()
                sub_content = driver_details.find_element_by_xpath(eduwork + "/div[%s]/ul" % i)
                eduwork_content = sub_content.text.replace('\n', '，') + '；'

            eduwork_info = '【' + eduwork_header.text + '】' + eduwork_content
            result[i] = eduwork_info
            if result[0] > 0:
                results = result[1] + result[2] + result[3]
    except NoSuchElementException:
        print('No eduwork info!')

    return results

# -------------------------------------------------------------
# -------------------------------------------------------------


# 獲取家鄉與現居地信息
def get_hometown_info():

    get_rest()
    result = ['', '', '']
    results = '暫無'

    try:
        current_content = driver_details.find_element_by_xpath(
            '//*[@id="current_city"]/div/div/div/div/div/div[2]/span')
        get_rest()
        result[1] = '【現居城市】' + current_content.text
    except NoSuchElementException:
        print('No current_city info!')

    try:
        hometown_content = driver_details.find_element_by_xpath('//*[@id="hometown"]/div/div/div[2]/span/a')
        get_rest()
        result[0] = '【家鄉】' + hometown_content.text
    except NoSuchElementException:
        print('No hometown info!')

    try:
        wait_details.until(ec.presence_of_element_located((By.XPATH, "//*[@id='pagelet_hometown']/div/div[2]")))
        lis = count_of_eles(previous, "li")
        previous_info = '【住所】'
        if lis > 1:
            for j in range(1, lis + 1):
                get_rest()
                sub_content = driver_details.find_element_by_xpath(previous + '/li[%s]' % j)
                previous_info = previous_info + str('%s.' % j) + sub_content.text.replace('\n', '，') + '；'
        else:
            get_rest()
            sub_content = driver_details.find_element_by_xpath(previous + '/li')
            previous_info += sub_content.text.replace('\n', '，')
        result[2] = previous_info
    except TimeoutException:
        print('No previous_cities info!')

    if not (result[0] == '' and result[1] == '' and result[2] == ''):
        results = result[0] + result[1] + result[2]

    return results

# -------------------------------------------------------------
# -------------------------------------------------------------


# 獲取其他信息
def get_bio_info():

    get_rest()
    result = ['', '', '', '', '']
    results = ['暫無', '暫無']

    try:
        bio_content = driver_details.find_element_by_xpath('//*[@id="pagelet_bio"]/div/ul')
        get_rest()
        result[0] = bio_content.text
    except NoSuchElementException:
        print('No bio info!')

    try:
        pronounce_content = driver_details.find_element_by_xpath('//*[@id="pagelet_pronounce"]/div/ul')
        get_rest()
        result[1] = pronounce_content.text
    except NoSuchElementException:
        print('No pronounce info!')

    try:
        nicknames_content = driver_details.find_element_by_xpath('//*[@id="pagelet_nicknames"]/div/ul')
        get_rest()
        result[2] = nicknames_content.text
    except NoSuchElementException:
        print('No nicknames info!')

    try:
        quotes_content = driver_details.find_element_by_xpath('//*[@id="pagelet_quotes"]/div/ul')
        get_rest()
        result[3] = '【喜愛的名言佳句】' + quotes_content.text
    except NoSuchElementException:
        print('No quotes info!')

    try:
        blood_donations_content = driver_details.find_element_by_xpath('//*[@id="pagelet_blood_donations"]/div/ul')
        get_rest()
        result[4] = blood_donations_content.text
    except NoSuchElementException:
        print('No blood_donations info!')

    if not (result[1] == '' and result[2] == '' and result[3] == '' and result[4] == ''):
        results[1] = result[4] + result[1] + result[2] + result[3]

    return results

# -------------------------------------------------------------
# -------------------------------------------------------------


# 獲取關注列表信息
def get_favorites_info():

    get_rest()
    try:
        wait_details.until(ec.presence_of_element_located((By.XPATH, "// *[ @ id = 'u_0_e'] / a"))).click()
    except TimeoutException:
        print("已全部顯示")

    result = [0, '', '', '', '', '', '', '', '', '', '', '', '']
    results = '暫無'
    try:
        for i in range(1, count_of_eles(favorites, "tbody") + 1):
            result[0] = count_of_eles(favorites, "tbody")
            favorites_header = driver_details.find_element_by_xpath(favorites + "/tbody[%s]/tr[1]/th" % i)
            get_rest()
            favorites_content = driver_details.find_element_by_xpath(favorites + "/tbody[%s]/tr[1]/td" % i)
            get_rest()
            favorites_info = '【' + favorites_header.text + '】' + favorites_content.text
            result[i] = favorites_info
        if result[0] > 0:
            results = result[1] + result[2] + result[3] + result[4] + result[5] + result[6] \
                      + result[7] + result[8] + result[9] + result[10] + result[11] + result[12]
    except NoSuchElementException:
        print('No favorites info!')

    return results

# -------------------------------------------------------------
# -------------------------------------------------------------


# 獲取聯絡資料
def get_contact_info():

    get_rest()
    result = [0, '', '', '']
    results = '暫無'
    try:
        result[0] = count_of_eles(contact, "li")
        for i in range(1, result[0] + 1):
            contact_header = driver_details.find_element_by_xpath(contact + '/li[%s]/div/div[1]' % i)
            get_rest()
            contact_content = driver_details.find_element_by_xpath(contact + '/li[%s]/div/div[2]' % i)
            get_rest()
            contact_info = '【' + contact_header.text + '】' + contact_content.text
            result[i] = contact_info
        if result[0] > 0:
            results = result[1] + result[2] + result[3]
    except NoSuchElementException:
        print('No contact info!')

    return results

# -------------------------------------------------------------
# -------------------------------------------------------------


# 獲取用戶信息
def get_users_info():
    count = 0
    with open("result.txt") as file:
        for line in file:
            line = line.strip()
            count += 1
            with mysql() as cursor:
                cursor.execute("SELECT 1 FROM users_info WHERE user_id = %s LIMIT 1", line)
                if cursor.rowcount > 0:
                    print('\n------------------------------------ User No.' + str(count) + ' '
                          + str(line) + ' has already been recorded! ------------------------------------')
                    cursor.execute(
                        ("SELECT page_" + str(id_num) + " FROM users_pages WHERE user_id = %s LIMIT 1"), line)
                    vez = cursor.fetchone()[("page_" + str(id_num))] + 1
                    cursor.execute(
                        ("UPDATE users_pages SET page_" + str(id_num) + " = %s WHERE user_id = %s LIMIT 1"),
                        (vez, line))
                else:
                    try:
                        ids = ["https://www.facebook.com/" + line]
                        driver_details.get(ids[0])
                        # driver_details.maximize_window()
                        print('\n------------------------------------ [New User ALERT] Crawling No.' + str(count) + ' '
                              + str(line) + '\'s info ------------------------------------')
                        try:
                            wait_details.until(ec.presence_of_element_located((By.XPATH, name)))
                            ni = driver_details.find_element_by_xpath(name)
                            cursor.execute("INSERT INTO users_info (user_id) VALUES (%s)", line)
                            cursor.execute("INSERT INTO users_pages (user_id) VALUES (%s)", line)

                            ei = get_eduwork_info()
                            hi = get_hometown_info()
                            fi = get_favorites_info()
                            bi = get_bio_info()
                            ci = get_contact_info()

                            get_rest()
                            try:
                                cursor.execute("UPDATE users_info SET "
                                               "user_name = %s, "
                                               "eduwork = %s, "
                                               "city = %s, "
                                               "bio = %s, "
                                               "quotes = %s, "
                                               "favorite = %s, "
                                               "contact = %s "
                                               "WHERE user_id = %s LIMIT 1",
                                               (ni.text, ei, hi, bi[0], bi[1], fi, ci, line))
                                cursor.execute(
                                    ("UPDATE users_pages SET page_" + str(id_num) + " = %s WHERE user_id = %s LIMIT 1"),
                                    (str(1), line))
                            except StaleElementReferenceException:
                                print('Wrong User!')
                                cursor.execute("INSERT INTO wrong_users_info (id) VALUES (%s)", line)
                            # break
                        except TimeoutException:
                            print('This is either a page or a WRONG user!')
                            cursor.execute("INSERT INTO wrong_users_info (id) VALUES (%s)", line)
                    except DataError:
                        cursor.execute("INSERT INTO wrong_users_info (id) VALUES (%s)", line)
                        print("This user_id is too long!")
    file.close()

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------


if __name__ == '__main__':
    # get things rolling
    main()

# -------------------------------------------------------------
# -------------------------------------------------------------


# # 網頁源碼解析
# def smart_crawler():
#
#     # 導入源碼
#     fbf = open(r'C:\Users\pc\Desktop\J\Ultimate-Facebook-Scraper-master\Code\fb.html', encoding="utf-8")
#     fb = fbf.read()
#     soup = BeautifulSoup(fb, 'html.parser')
#
#     # 集合
#     result = set()
#
#     # 查找所有帶用戶ID鏈接的a元素
#     for k in soup.find_all("a", {"class": {"_6qw4"}}):
#         # 獲取href标签
#         link = k.get('href')
#         # 过滤没找到的
#         if link is not None:
#             if link[-1] == '/':
#                 link = link[:-1]
#             user = link.split("/")[-1]
#             result.add(user)
#
#     # 存儲超链接列表
#     f = open(r'result.txt', 'w', encoding='utf-8')  # 文件路径、操作模式、编码  # r''
#     for a in result:
#         f.write(a + "\n")
#     f.close()
#     print("\r\n扫描结果已写入到result.txt文件中\r\n")
