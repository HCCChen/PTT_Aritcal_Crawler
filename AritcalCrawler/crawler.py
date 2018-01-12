import os
import re
import requests
import time
import sys
import pickle
import json
from bs4 import BeautifulSoup

sys.setrecursionlimit(30000)
PTT_URL = 'https://www.ptt.cc'
WEB_REQUEST_TIMEOUT = 5


# Get article link and relative information from article list
def get_article_info(oriText):
    if oriText.find('a') is None:
        return

    href = oriText.find('a')['href']
    url = PTT_URL + href

    href = href.replace(".", "_")
    href = href.replace("/", "_")
    href = href.replace("_bbs_", "")
    index = href.replace("_html", "")

    title = oriText.find('a').string

    scoreLine = oriText.find('span')
    if scoreLine:
        score = scoreLine.string
    else:
        score = '0'

    mark = oriText.find(class_='mark').string

    date = oriText.find(class_='date').string
    author = oriText.find(class_='author').string

    articleInfo = {'index':index, 'url':url, 'title':title, 'score': score, 'mark':mark, 'date':date, 'author':author}
    return articleInfo;

# Get context from PTT website
def get_board_context(board, index):
    VERIFY = True
    resp = requests.get(
        url = PTT_URL + '/bbs/' + board + '/index' + str(index) + '.html',
        cookies={'over18': '1'}, verify=VERIFY, timeout=WEB_REQUEST_TIMEOUT
    )
    return resp


# Get meta data from article
def get_article_meta_data(link):
    resp = requests.get(
        url = link,
        cookies={'over18': '1'}, verify=True, timeout=WEB_REQUEST_TIMEOUT
    )

    soup = BeautifulSoup(resp.text, 'html.parser')
    if soup.title.string == '500 - Internal Server Error':
        print('Server is too busy, skip it!')
        exit()

    # Get meta data from artical
    articleMetaValue = soup.find_all(class_='article-meta-value')
    timeStamp = time.mktime(time.strptime(articleMetaValue[3].string, "%a %b %d %H:%M:%S %Y"))

    # Get all comment in this article
    pushList = soup.find_all(class_='push')
    pushMetaDataList = []
    for tagIndex in range (0, len(pushList)):
        pushTag = pushList[tagIndex].find(class_='push-tag').string
        pushUserId = pushList[tagIndex].find(class_='push-userid').string
        pushContent = pushList[tagIndex].find(class_='push-content').get_text()
        try:
            pushTimeStamp = pushList[tagIndex].find(class_='push-ipdatetime').string.split(' ', 1)[1]
        except IndexError:
            continue
        pushMetaData = {'tag':pushTag, 'userId':pushTag, 'content':pushContent, 'timeStamp':pushTimeStamp}
        pushMetaDataList.insert(tagIndex, pushMetaData)

    # Filter tag and get context only
    dropTag = soup.find_all(class_='push')
    for tagIndex in range (0, len(dropTag)):
        dropTag[tagIndex].decompose()

    dropTag = soup.find_all(class_='article-metaline')
    for tagIndex in range (0, len(dropTag)):
        dropTag[tagIndex].decompose()

    dropTag = soup.find_all(class_='article-metaline-right')
    for tagIndex in range (0, len(dropTag)):
        dropTag[tagIndex].decompose()

    contextHtml = soup.find(id='main-content')

    while (contextHtml.span != None):
        contextHtml.span.extract()

    while (contextHtml.div != None):
        contextHtml.div.extract()
    
    return {'timeStamp':timeStamp, 'context':contextHtml.get_text(), 'pushMetaData':pushMetaDataList}

# Save meta data to file
def save_article_meta_data(articleMetaData):
    if not os.path.exists("data"):
        os.makedirs("data")

    folderName = "data/" + articleMetaData['articleInfo']['index'].split('_', 1)[0]
    metaDataFilePath = folderName + "/" + articleMetaData['articleInfo']['index'] + ".txt"

    if not os.path.exists(folderName):
        os.makedirs(folderName)

    try:
        fp = open(metaDataFilePath, 'w')
        fp.write(json.dumps(articleMetaData, ensure_ascii=False))
    except FileNotFoundError:
        print('fp is none')
        return
    except TypeError:
        print("#### Have Type Error, dump context ####")
        print(articleMetaData) 
        print("#######################################")
        return
    return metaDataFilePath


# Load meta data from file
def load_article_meta_data(articleMetaData):
    with open(articleMetaData) as json_data:
        metaData = json.load(json_data)

    return metaData

# Save the article index file
def save_article_index(articleInfoList, boardName):
    if not os.path.exists("data"):
        os.makedirs("data")

    folderName = "data/" + boardName
    indexFilePath = folderName + "/" + "index.json"

    if not os.path.exists(folderName):
        os.makedirs(folderName)

    with open(indexFilePath, 'w') as outFile:
        json.dump(articleInfoList, outFile)


# Load the article index file
def load_article_index(boardName):
    indexFilePath = "data/" + boardName + "/index.json"
    with open(indexFilePath) as json_data:
        metaData = json.load(json_data)

    return metaData

# Main function for crawler
def ptt_crawler(boardName, page):
    articleInfoList = []

    # Firstly, get first page of article list.
    resp = get_board_context(board, '0')

    # init BeautifulSoup
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Error handle for page error
    if soup.title.string == '500 - Internal Server Error':
        print('Server is too busy, skip it!')
        exit()
   
    # Get article list index 
    pageInfo = soup.find_all(class_='btn')
    first_page_url = pageInfo[3]['href']
    buf_str = first_page_url.split('index', 1);
    buf_str = buf_str[1].split('.', 1)
    max_index = int(buf_str[0])

    # Get article url for each page
    for article_list_index in range (max_index - page, max_index):
        print(article_list_index)
        resp = get_board_context(board, article_list_index)
        soupForEachContext = BeautifulSoup(resp.text, 'html.parser')

        # Get artical from list
        divs = soupForEachContext.find_all('div', 'r-ent')
        index = 0
        for boardContext in divs:
            time.sleep(3)
            index += 1
            articleInfo = get_article_info(boardContext)
            if not articleInfo is None:
                articleMetaData = get_article_meta_data(articleInfo['url'])
                articleMetaData['articleInfo'] = articleInfo
                articleInfo['filePath'] = save_article_meta_data(articleMetaData)
                articleInfoList.append(articleInfo)
                print("Processing file: " + articleInfo['title'])

    save_article_index(articleInfoList, boardName)
    #print(json.dumps(load_article_index(boardName), indent=4, sort_keys=True))

# Main function
if __name__ == '__main__':
    #===================================
    board = 'ToS'
    page = 1
    #===================================
    ptt_crawler(board, page)
