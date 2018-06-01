import os
import sys
import json

import requests
import urllib2
from bs4 import BeautifulSoup

# Change default encoding to add support
reload(sys)
sys.setdefaultencoding('utf8')
# H2R - 1
# Mangabb - 2
comic_source = None
hdr = {}

def fileImport(file_to_look):
    with open(file_to_look, "r") as f:
      for line in f:
        link = line.strip()

        print ("Downloading for %s" % (link))
        startDownload(link)

def build(pages, link, hname):
    # Create dir to dump
    # sanitize hname folder
    print hname
    # hname = hname.encode('utf-8').strip()
    if not os.path.exists(hname):
        print "Creating dir %s" %hname
        os.makedirs(hname)

    ls = link.split("/")
    # Get img link like ccdn0001.jpg
    fjpg = ls.pop()

    # Rebuild link without img
    ls.append('')
    ls = '/'.join(ls)

    # Create pre determined array
    nos = sum(c.isdigit() for c in fjpg)
    pre = []
    for i in range(0, 1000):
        if nos == 1:
            t = str("%0.1d" % i)
        elif nos == 2:
            t = str("%0.2d" % i)
        elif nos == 3:
            t = str("%0.3d" % i)
        else:
            t = str("%0.4d" % i)
        pre.append(t)

    # Find occu in pre
    match_pos = -1
    for i in range(0, 1000):
        if pre[i] in fjpg:
            match_pos = i
            break

    if match_pos == -1:
        print "NO Matching found"
        exit()

    # Rebuild url again
    s_arr = fjpg.split(pre[match_pos])

    # Consider extra chars after page number
    # like: vcdn001_copy.
    f_st = s_arr[0]
    f_end = '.jpg'
    if len(s_arr) == 2:
        f_end = s_arr[1]

    ls = ls + f_st

    for x in range(0, pages):
        file_dump = hname + "/" + "%0.3d.jpg" % (x + 1)
        link_sp = ls + pre[match_pos + x] + f_end

        print ("Trying url: %s -> saving as: %s" % (link_sp, file_dump))

        f = open(file_dump, 'wb')
        f.write(requests.get(link_sp).content)
        f.close()


def getPagesCurChapter(soup):
    print "Get Pages"
    plen = 0
    if comic_source == 1:
        jData = soup.find_all("script")
        for j in jData:
            if j.string is not None:
                txt = j.string
                txt = "".join(txt.split(None))
                idx = txt.find("gData=")
                if idx > 0:
                    data = txt[txt.find("vargData=") + 9:-1]

                    data = data.replace("\'", "\"")
                    jss = json.loads(data)

                    plen = len(jss["images"])
                    break
    elif comic_source == 2:
        pages_lst = []
        for pgs in soup.find_all('option'):
            try:
                chps = pgs.string.strip()

                if chps.isdigit():
                    to_add = int(chps)
                    if to_add not in pages_lst:
                        pages_lst.append(to_add)
            except KeyError:
                pass
        plen = len(pages_lst)
    return plen

def setPreRequest(url):
    global comic_source
    global hdr
    if "hentai2read" in url :
        comic_source = 1
        hdr = {}
    elif "goodmanga" in url or "mangabb" in url:
        hdr = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }
        comic_source = 2

def getCdnUrl(soup):
    cdn = ""
    if comic_source == 1:
        cdn = soup.find_all("img", id="arf-reader")

        cdn = cdn[0]["src"]
    elif comic_source == 2:
        tags = soup.find_all("img")

        for tag in tags:
            try:
                wdt = tag["width"]
                cdn = tag["src"]
            except KeyError:
                pass

    print (" CDN URL found : %s " %cdn)
    return cdn

def getTitle(soup):
    if comic_source == 1:
        tag = soup.find_all("img", id="arf-reader")

        return tag[0]["alt"]
    elif comic_source == 2:
        for tag in soup.find_all('a'):
            if tag.parent.name == 'h3':
                return tag.string


def getChapter(soup):
    ch_len = []
    if comic_source == 1:
        chapters = soup.find_all('a', class_='js-reader_chapters')

        # Finds non-unique chapter
        for ch in chapters:
            tmp = int(ch["data-cslug"])
            if tmp not in ch_len:
                ch_len.append(tmp)

    elif comic_source == 2:
        for ch in soup.find_all('option'):
            try:
                # Double pop
                tmp = ch["value"].split("/")

                pg = tmp.pop()
                ch = tmp.pop()

                if not ch.isdigit():
                    try:
                        to_add = int(pg)
                    except ValueError:
                        to_add = float(pg)
                    if to_add not in ch_len:
                        ch_len.append(to_add)
            except KeyError:
                pass

    ch_len.sort()
    return ch_len


def startDownload(url):
    setPreRequest(url)

    if url.endswith("/"):
        url = url[:-1]

    opts = url.split("/")

    # Allow chapters append
    ch_start = int(opts.pop())

    # Check if popped item is not page
    tmp = opts.pop()
    if tmp.isdigit():
        ch_start = int(tmp)
    else:
        opts.append(tmp)

    opts.append("")

    req = urllib2.Request(url, headers=hdr)
    page = urllib2.urlopen(req)

    soup = BeautifulSoup(page, "html.parser")

    # Get Title
    title = getTitle(soup)

    # Get chapters
    chapters = getChapter(soup)

    # Pick chapters more than current passed
    chapters = [a for a in chapters if a >= ch_start]

    for i in chapters:
        ch_url = "/".join(opts) + str(i)

        print ch_url
        # Fetch url to get page and cdn url
        req_ch = urllib2.Request(ch_url, headers=hdr)
        page = urllib2.urlopen(req_ch)
        soup = BeautifulSoup(page, "html.parser")

        pgs = int(getPagesCurChapter(soup))
        cdn_url = getCdnUrl(soup)

        # Don't create additional folders for 1 chapter
        if len(chapters) == 1:
            ch_title = title
        else:
            ch_title = title + "/" + str(i)

        print(" Chapter: %d , pages: %d, url: %s  " % (i, pgs, ch_url))
        print "Fetching Data"
        build(pgs, cdn_url, ch_title)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        param = sys.argv[1]
        if os.path.exists(param):
            fileImport(param)
        else:
            startDownload(param)
    else:
        print "Insufficient Parameter!!"
