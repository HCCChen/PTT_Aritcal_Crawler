import re
import requests
from bs4 import BeautifulSoup

PTT_URL = 'https://www.ptt.cc'


# Get article link and relative information from article list
def get_article_link(oriText):
    if oriText.find('a') is None:
        return

    href = oriText.find('a')['href']
    url = PTT_URL + href

    title = oriText.find('a').string

    scoreLine = oriText.find('span')
    if scoreLine:
        score = scoreLine.string
    else:
        score = '0'

    mark = oriText.find(class_='mark').string

    date = oriText.find(class_='date').string
    author = oriText.find(class_='author').string

    result = {'url':url, 'title':title, 'score': score, 'mark':mark, 'date':date, 'author':author}
    return result;

# Get context from PTT website
def get_board_context(board, index):
    VERIFY = True
    timeout = 5
    resp = requests.get(
        url = PTT_URL + '/bbs/' + board + '/index' + str(index) + '.html',
        cookies={'over18': '1'}, verify=VERIFY, timeout=timeout
    )
    return resp


# To-do: get meta data from article
def get_article_meta_data(link):
    print(link)
    # Artical URL Example: https://www.ptt.cc/bbs/Baseball/M.1509090486.A.1EB.html
    #resp = requests.get(
    #    url = 'https://www.ptt.cc/bbs/Baseball/M.1509090486.A.1EB.html',
    #    cookies={'over18': '1'}, verify=True, timeout=10
    #)
    #print(resp.text)
    return

if __name__ == '__main__':
    #===================================
    board = 'ToS'
    index = '0'
    #===================================
    # Firstly, get first page of article list.
    resp = get_board_context(board, index)
#    print(resp.text)

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
#    print(max_index)

    # Get article url for each page
    for article_list_index in range (max_index - 10, max_index):
        print(article_list_index)
        resp = get_board_context(board, article_list_index)
        soupForEachContext = BeautifulSoup(resp.text, 'html.parser')

        # Get artical from list
        divs = soupForEachContext.find_all('div', 'r-ent')
        index = 0
        for boardContext in divs:
            index += 1
            article_link = get_article_link(boardContext)
            if not article_link is None:
                get_article_meta_data(article_link)


