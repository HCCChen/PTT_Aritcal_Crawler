# -*- coding: utf-8 -*-
import os
import re
import requests
import time
import datetime
import sys
import json
import argparse
from bs4 import BeautifulSoup

PTT_URL = 'https://www.ptt.cc'
WEB_REQUEST_TIMEOUT = 5
MAX_RETRY_COUNT = 5


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
    resp = None
    retryCount = 0

    while resp is None:
        retryCount += 1
        if retryCount == MAX_RETRY_COUNT:
            print('Had retry ', MAX_RETRY_COUNT, ' times, skip to get board context')
            return None
        try:
            resp = requests.get(
                url = PTT_URL + '/bbs/' + board + '/index' + str(index) + '.html',
                cookies={'over18': '1'}, verify=True, timeout=WEB_REQUEST_TIMEOUT
            )
        except Exception as e:
            print('[Exception] ', e)
            print('Have exception during get board context, try again')

    return resp


# Get meta data from article
def get_article_meta_data(link):
    resp = None
    retryCount = 0

    while resp is None:
        retryCount += 1
        if retryCount == MAX_RETRY_COUNT:
            print('Had retry ', MAX_RETRY_COUNT, ' times, skip to get board context')
            return None
        try:
            resp = requests.get(
               url = link,
                cookies={'over18': '1'}, verify=True, timeout=WEB_REQUEST_TIMEOUT
            )
        except Exception as e:
            print('[Exception] ', e)
            print("Get article fail from: ", link)
            return None

    soup = BeautifulSoup(resp.text, 'html.parser')
    if soup.title.string == '500 - Internal Server Error':
        print('Server is too busy, skip it!')
        exit()

    # Get meta data from artical
    articleMetaValue = soup.find_all(class_='article-meta-value')
    try:
        timeStamp = time.mktime(time.strptime(articleMetaValue[3].string, "%a %b %d %H:%M:%S %Y"))
    except Exception as e:
        print('[Exception] ', e)
        print("Get timestamp fail, dump all and skip it")
        print("Link: ", link)
        print("Context: ", soup)
        return None
    st = time.localtime(timeStamp)
    year = time.strftime('%Y', st)

    # Get all comment in this article
    likeCount = 0
    dislikeCount = 0
    neutralCount = 0
    pushList = soup.find_all(class_='push')
    pushMetaDataList = []
    for tagIndex in range (0, len(pushList)):
        try:
            pushTag = pushList[tagIndex].find(class_='push-tag').get_text().rsplit()[0]
            if pushTag == u"推":
                likeCount += 1
                pushTag = '+'
            elif pushTag == u"噓":
                dislikeCount += 1
                pushTag = '-'
            elif pushTag == u"→":
                neutralCount += 1
                pushTag = '.'

            pushUserId = pushList[tagIndex].find(class_='push-userid').string
            pushContent = pushList[tagIndex].find(class_='push-content').get_text()
            pushTime = year + ' ' + pushList[tagIndex].find(class_='push-ipdatetime').get_text().strip()
            st = time.strptime(pushTime, '%Y %m/%d %H:%M')
            pushTimeStamp = time.mktime(st)
        except Exception as e:
            print('[Exception] ', e)
            print("Have exception during get push info, Skip it and dump original context")
            print(pushList[tagIndex])
            continue
        pushMetaData = {'tag':pushTag, 'userId':pushUserId, 'content':pushContent, 'timeStamp':pushTimeStamp}
        pushMetaDataList.insert(tagIndex, pushMetaData)


    # Get Ip Address
    ipAddr = 0
    f2List = soup.find_all(class_='f2')
    for tagIndex in range(0, len(f2List)):
        try:
            if '(ptt.cc)' in f2List[tagIndex].get_text():
                ipAddr = f2List[tagIndex].get_text().split(": ", 2)[2].rstrip()
                break;
        except Exception as e:
            print('[Exception] ', e)
            print("Get Ip address fail, skip to get IP address and dump context")
            print("Link: ", link)
            print("Context: ", soup)
            break

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
    
    return {'timeStamp':timeStamp, 'context':contextHtml.get_text(), 'pushMetaData':pushMetaDataList, 'ipAddr':ipAddr, 'countLike':likeCount, 'countDislike':dislikeCount, 'countNeutral':neutralCount}

# Save meta data to file
def save_article_meta_data(articleMetaData, boardName):
    articleDate = datetime.datetime.fromtimestamp(articleMetaData['timeStamp']).strftime("%Y_%m_%d")
    if not os.path.exists("data"):
        os.makedirs("data")
    
    folderName = "data/" + boardName + "/" + articleDate
    metaDataFilePath = folderName + "/" + articleMetaData['index'] + ".json"

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
def load_article_meta_data(filePath):
    with open(filePath) as json_data:
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
        json.dump(articleInfoList, outFile, ensure_ascii=False)


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
    resp = get_board_context(boardName, '0')
    if resp is None:
        return

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
        resp = get_board_context(boardName, article_list_index)
        if resp is None:
            continue;
        soupForEachContext = BeautifulSoup(resp.text, 'html.parser')

        # Get artical from list
        divs = soupForEachContext.find_all('div', 'r-ent')
        index = 0
        for boardContext in divs:
            #time.sleep(1)
            index += 1
            articleInfo = get_article_info(boardContext)
            if not articleInfo is None:
                print("Processing article: ", articleInfo['title'])
                articleMetaData = get_article_meta_data(articleInfo['url'])
                if articleMetaData is None:
                    print("Have problem during dump article, slow down and skip it")
                    time.sleep(1)
                    continue;
                articleMetaData.update(articleInfo)
                articleInfo['filePath'] = save_article_meta_data(articleMetaData, boardName)
                articleInfoList.append(articleInfo)
                print("Process done.")

    save_article_index(articleInfoList, boardName)

# Main function
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--board", help="Give the board name which want to crawler", type=str)
    parser.add_argument("-p", "--page", help="Give the page which want to crawler", type=int)
    args = parser.parse_args()
    if args.board is None:
        print("Leak argument: board name, STOP it.")
    elif args.page is None:
        print("Leak argument: page, STOP it.")
    else:
        ptt_crawler(args.board, args.page)
        #get_article_meta_data("https://www.ptt.cc/bbs/ToS/M.1515507630.A.8D3.html")
        #print(json.dumps(load_article_index(board), indent=4, sort_keys=True, ensure_ascii=False))
        #print(json.dumps(load_article_meta_data("data/ToS/ToS_M_1515844001_A_D50.txt"), indent=4, sort_keys=True, ensure_ascii=False))
