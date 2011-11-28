#!/usr/bin/python2


import os,re,fileinput

import transmissionrpc

import urllib

import  fsdbm

from BeautifulSoup import BeautifulSoup, SoupStrainer

downloader = transmissionrpc.Client('127.0.0.1')

down_db =  fsdbm.FSDBM("feed-dl.db")

debug = 0


def add_dl(url,name):
    global downloader;
    global debug
    global down_db
    #try decode name
    #get name
    filename = name
    #cut relise group
    name = name.replace(name[name.find('['):name.find(']')+1],'')
    #get only name
    name = name[1:name.find("-")-1]
    #remove spaces
    while name.startswith(' '):
        name = name[1:len(name)]
    print(name)
    #find collisions
    try:
        if (down_db[url.encode('utf-8')] == 1 ):
            print( "Already in db")
            return
    except Exception, err:
        print("Adding to db")
        down_db[url.encode('utf-8')] = 1;

    if  not debug:
        dir = downloader.session_stats().fields['download_dir']+name+'/'
        print(dir)
        d = os.path.dirname(dir)
        if not os.path.exists(d):
            os.makedirs(d)
        try:
            print( url)
            downloader.add_uri(url,download_dir = dir)
        except Exception, err:
            print( "Bad torrent !  \n")
    else:
        print("[debug] name=" + name + " url=" + url )
    


def parse_site(terms):
    #first pass
    going_on = True
    page_number = 1;
    soup = BeautifulSoup(urllib.urlopen('http://www.tokyotosho.info/search.php?terms='+urllib.quote_plus(terms)).read())
    while going_on:
        baselist = soup.body.div.findAll('table')[2].tr.nextSibling
        
        while not not baselist:
            reflist = baselist.findAll('td')[1].a
            if (reflist):
                if reflist.get('type') == 'application/x-bittorrent':
                #print reflist.text
                    print (reflist.text)
                    add_dl(reflist.get('href'),reflist.text)
                    baselist  = baselist.nextSibling.nextSibling
        
    #go next pages

        #get page number/ page count
        try: 
            stringa = soup.body.div.findAll('p')[1].findAll('a')[0].get('href')
        except Exception,err:
            print( '(no next href)End! \n')
            break

        basepagenumber =  int(stringa[stringa.find('page=')+5:stringa.find('&terms')]) 
        if page_number == 1: basepagenumber = 1
        try:
            nextlink =  soup.body.div.findAll('p')[1].findAll('a')[page_number-basepagenumber].get('href')
        except  Exception,err:
            print( 'End! \n')
            break
        nextlink =  'http://www.tokyotosho.info/search.php' + nextlink 
        print( 'Going next page url= '+nextlink + '\n')
        page_number  = page_number + 1 
        soup = BeautifulSoup(urllib.urlopen(nextlink).read())
    
        
    


def dofile():
    for line in fileinput.input("file-dl.txt"):
        print("parsing line="+ line)
        parse_site(line.rstrip('\n'))
    fileinput.close()




class TimeoutException(Exception): 
    pass 

def timeout_handler(signum, frame):
    raise TimeoutException()



import signal

signal.signal(signal.SIGALRM, timeout_handler) 
signal.alarm(600) # triger alarm in 5 minuts

try:
    dofile()
except:
    print("Time out parsing");



