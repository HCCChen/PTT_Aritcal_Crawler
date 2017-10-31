import re
import requests
from bs4 import BeautifulSoup

PTT_URL = 'https://www.ptt.cc'


# Get article link and relative information from article list
def get_article_link(oriText):
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


if __name__ == '__main__':
    #===================================
    board = 'ToS'
    index = '0'
    PTT_URL = 'https://www.ptt.cc'
    #===================================
    resp = get_board_context(board, index)
    print(resp.text)


    # init BeautifulSoup
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Error handle for page error
    if soup.title.string == '500 - Internal Server Error':
        print('Server is too busy, skip it!')
        exit()
   
    # Get page info 
    pageInfo = soup.find_all(class_='btn')
    print(pageInfo[3]['href'])


    # Get artical from list
    divs = soup.find_all('div', 'r-ent')
    index = 0
    for link in divs:
        index += 1
        result = get_article_link(link)
        print(result)

    # Artical URL Example: https://www.ptt.cc/bbs/Baseball/M.1509090486.A.1EB.html
    resp = requests.get(
        url = 'https://www.ptt.cc/bbs/Baseball/M.1509090486.A.1EB.html',
        cookies={'over18': '1'}, verify=True, timeout=10
    )
    #print(resp.text)
