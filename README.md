# PTT_Aritcal_Crawler
Aritcal Crawler for PTT-Web, save context and meta data to json

### Run Environment
* Python 3
* BeautifulSoup

### Command

```sh
usage: crawler.py [-h] [-b BOARD] [-p PAGE]

optional arguments:
  -h, --help            show this help message and exit
  -b BOARD, --board BOARD
                        Give the board name which want to crawler
  -p PAGE, --page PAGE  Give the page which want to crawler
```
### Output result
All data will saved at folder "data/BOARD_NAME", it saved as json formate and one file record one article.
File name is base on board name and article id, EX: Gossiping_M_1515772101_A_B7B.json

There have one index file named "index.json" at the same folder.
It record all article index in previous work.
