import requests
import sys
import os

def build():
    pages = int(sys.argv[1])
    link = sys.argv[2]
    hname = sys.argv[3]

    if len(sys.argv) != 4:
        print "Insufficient params !!"
        return

    # Create dir to dump
    if not os.path.exists(hname):
        print "Creating dir %s" %hname
        os.mkdir(hname)

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
        if nos == 3:
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

build()
