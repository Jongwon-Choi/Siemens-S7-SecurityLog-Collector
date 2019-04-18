from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import socket
import re
import time

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def sender():             # 
    sender_ip = input("Logstash`s ip address(default = 145.0.100.10) = ")
    if sender_ip == "":
        sender_ip = '145.0.100.10'
    sender_port = input("Logstash`s port(default = 5044) = ")
    if sender_port == "":
        sender_port = 5044

    return sender_ip, sender_port


def auto_url():
    plc_ip = input("plc`s ip address(default = 192.168.0.1) = ")
    if plc_ip == "":
        plc_ip = '192.168.0.1'

    return 'http://' + plc_ip + '/Portal/Portal.mwsl?intro_enter_button=ENTER&PriNav=Start&coming_from_intro=true', plc_ip


def auto_login():
    login_id = input("input ID : ")
    pd = input("input Password : ")
    return login_id, pd


url, plc_ip_main = auto_url()
driver = webdriver.Chrome('chromedriver')
driver.get(url)

logId, passwd = auto_login()
driver.find_element_by_name('Login').send_keys(logId)
driver.find_element_by_name('Password').send_keys(passwd)
driver.find_element_by_id('Login_Area_SubmitButton').click()

driver.get('http://' + plc_ip_main + '/Portal/Portal.mwsl?PriNav=Diag')
driver.find_element_by_xpath("//option[@value='en']").click()
soup = BeautifulSoup(driver.page_source, 'lxml')
selected_id = soup.select('option')
DiagCount = len(selected_id) - 11


sender_ip, sender_port = sender()
s.connect((sender_ip, sender_port))

while DiagCount > 0:
    driver.get('http://' + plc_ip_main + '/Portal/Portal.mwsl?PriNav=Diag&ThrNav=DiagTable' + str(DiagCount))
    DiagCount -= 1
    driver.find_element_by_id('MWSL_1050').click()
    driver.switch_to_window(driver.window_handles[1])
    # soup = BeautifulSoup(driver.page_source, 'lxml')
    tables = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//td[@class='contentItem']//td")))
    tables.reverse()
    tables.pop()
    cnt = 0
    line = []
    for table in tables:
        print(table.text)
        if cnt < 3:
            cnt += 1
            if cnt != 1:
                if cnt == 2:
                    str1 = table.text
                    list2 = str1.split('\n')
                    if 'pm' in list2[-1]:
                        list2[-1][0] = str(int(list2[-1][0]) + 12)
                    list100 = re.findall(r'\d+', list2[-1])
                    print(list100)
                    list100[0] = "hh " + list100[0]
                    list100[1] = "mm " + list100[1]
                    list100[2] = "ss " + list100[2]
                    list100[4] = "MM " + list100[4]
                    list100[5] = "dd " + list100[5]
                    list100[6] = "yyyy " + list100[6]
                    str100 = '\n'.join(list100)
                    list2[-1] = str100
                    str2 = "Timestamp " + list2[-1]
                    str3 = "InorOut " + list2[-2]
                    list2[-2] = str3
                    list2[-1] = str2
                    print(list2)
                    str1 = '\n'.join(list2)
                    str1 = "Message " + str1
                    print(str1)
                    line.append(str1)
                else:
                    line.append(table.text)
        else:
            temp = table.text
            print(temp)
            line.reverse()
            print(line)
            cnt = 0
            test = "'".join(line)
            print(test)
            p = re.compile('(\n)')
            test = p.sub("'", test)
            test = bytes(test, 'utf-8')
            print(test)
            s.send(test)
            line = []
    driver.close()
    driver.switch_to_window(driver.window_handles[0])

s.close()

while True:
    time_start = time.time()
    driver.get('http://' + plc_ip_main + '/Portal/Portal.mwsl?PriNav=Diag&ThrNav=DiagTable1')
    driver.find_element_by_id('MWSL_1050').click()
    driver.switch_to_window(driver.window_handles[1])
    # soup = BeautifulSoup(driver.page_source, 'lxml')
    tables = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//td[@class='contentItem']//td")))
    print(tables[1].text)
    latest = tables[1].text

    if before != latest:
        print("no")
        beforeList = re.findall(r'\d+', before)
        latestList = re.findall(r'\d+', latest)
        beforeNum = beforeList[1]
        latestNum = latestList[1]
        latestNum = int(latestNum)
        beforeNum = int(beforeNum)
        finalNum = latestNum - beforeNum
        print(finalNum)
        cnt = 0
        line = []
        for table in tables:
            cnt = cnt + 1
            print(table.text)
            if cnt == finalNum:
                break
    else:
        print("yes")
    driver.close()
    driver.switch_to_window(driver.window_handles[0])
    time_end = time.time()
    print('measured time per one page:', time_end - time_start)
    time.sleep(10)

