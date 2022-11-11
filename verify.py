import httpx
import re
import requests
import logging
from concurrent.futures import ThreadPoolExecutor
import time
import datetime
import threading
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import xlwt
import xlrd
from xlutils.copy import copy
logging.captureWarnings(True)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

start = datetime.datetime.now()
lock = threading.Lock()
savefilename = time.strftime("%Y-%m-%d %H.%M.%S")
myxls = xlwt.Workbook()
sheet1 = myxls.add_sheet(u'title',cell_overwrite_ok=True)
sheet1.write(0,0,"源地址")
sheet1.write(0,1,"跳转地址")
sheet1.write(0,2,"状态码")
sheet1.write(0,3,"标题")
myxls.save(savefilename+'.xls')

headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36",
        }

def get_title(url):
    """
    获取网站的title
    """
    try:
        location_res = httpx.get(url, headers=headers)
        title = re.findall(u'<title>(.*?)</title>', location_res.content.decode("utf-8"), re.S)[0].strip()
    except Exception as e:
        title = "多次跳转"
    return title


def Verify(url):
    """
    验证子域名的存活
    """
    try:
        res = httpx.get(url, headers=headers, timeout=(3, 6))
        status_code = res.status_code    # 状态
        if status_code == 302 or status_code == 301:
            location = res.headers["location"]
            title = get_title(location)
        elif status_code == 200:
            title = get_title(url)
            location = ""
        else:
            location = ""
            title = ""
    except Exception as e:
        status_code = ""
        location = ""
        title = "无法访问"
    return url, location, status_code, title


def write(url):
    codetitle = Verify(url)
    url = str(codetitle[0])
    resurl = str(codetitle[1])
    code = str(codetitle[2])
    title = str(codetitle[3])
    print(f"{url} || {resurl} || {code} || {title}")
    with lock:
        word_book = xlrd.open_workbook(savefilename+'.xls')
        sheets = word_book.sheet_names()
        work_sheet = word_book.sheet_by_name(sheets[0])
        old_rows = work_sheet.nrows
        heads = work_sheet.row_values(0)
        new_work_book = copy(word_book)
        new_sheet = new_work_book.get_sheet(0)
        i = old_rows
        new_sheet.write(i, 0, url)
        new_sheet.write(i, 1, resurl)
        new_sheet.write(i, 2, code)
        new_sheet.write(i, 3, title)
        new_work_book.save(savefilename + '.xls')


# 读取文件
filename = "url.txt"
with open(filename, 'r', encoding='utf-8') as f:
    urls_data = ["http://" + data.replace("\n", "") for data in f]

# 线程池
with ThreadPoolExecutor(max_workers=500) as executor:
    for urls in urls_data:
        executor.submit(
            write, url=urls
        )
end = datetime.datetime.now()
seconds = (end - start).seconds
print(f"共耗时{seconds}秒")
