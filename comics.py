import os
import sys
import json

import requests
import urllib2
from bs4 import BeautifulSoup

def cmdline():
    if len(sys.argv) != 4:
        print "Insufficient params !!"
        return
    pages = int(sys.argv[1])
    link = sys.argv[2]
    hname = sys.argv[3]

    build(pages, link, hname)

def fileImport():
    file_to_look = sys.argv[1]
    with open(file_to_look, "r") as f:
      for line in f:
        opts = line.split(",")
        pgs = int(opts[0])
        lnk = opts[1]
        hname = opts[2].rstrip()

        print ("A: %s, B: %s, C: %s" % (pgs, lnk, hname))
        build(pgs, lnk, hname)

def build(pages, link, hname):
    # Create dir to dump
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
    f_st = fjpg.split(pre[match_pos])[0]
    ls = ls + f_st

    for x in range(0, pages):
        file_dump = hname + "/" + "%0.3d.jpg" % (x + 1)
        link_sp = ls + pre[match_pos + x] + '.jpg'

        print ("Trying url: %s -> saving as: %s" % (link_sp, file_dump))

        f = open(file_dump, 'wb')
        f.write(requests.get(link_sp).content)
        f.close()


def getPagesCurChapter(soup):
    print "Get Pages"
    jData = soup.find_all("script")
    plen = 0
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

    return plen

def getCdnUrl(soup):
    cdn = soup.find_all("img", id="arf-reader")

    print (" CDN URL found : %s " %cdn[0]["src"])
    return cdn[0]["src"]

def getTitle(soup):
    tag = soup.find_all("img", id="arf-reader")

    return tag[0]["alt"]

def getChapter(soup):
    chapters = soup.find_all('a', class_='js-rdrChapter')
    ch_len = []

    # Finds non-unique chapter
    for ch in chapters:
        if ch["data-cslug"] not in ch_len:
            ch_len.append(ch["data-cslug"])

    return ch_len

def startDownload():
    if len(sys.argv) != 2:
        print "Insufficient Paramters. Provide url."
        return

    url = sys.argv[1]

    if url.endswith("/"):
        url = url[:-1]

    opts = url.split("/")

    # Allow chapters append
    opts.pop()
    opts.append("")

    page = urllib2.urlopen(url)

    soup = BeautifulSoup(page, "html.parser")

    # Get Title
    title = getTitle(soup)

    # Get chapters
    chapters = getChapter(soup)

    for i in chapters:
        i = int(i)
        ch_url = "/".join(opts) + str(i)

        # Fetch url to get page and cdn url
        page = urllib2.urlopen(ch_url)
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

# if len(sys.argv) == 2:
#     fileImport()
# else:
#     cmdline()

startDownload()
