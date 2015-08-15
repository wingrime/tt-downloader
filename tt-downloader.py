#!/usr/bin/python3
#Tokyotoshokan autodownloader script

import os,re,fileinput
import transmissionrpc
import urllib
import argparse
import signal

from bs4 import BeautifulSoup, SoupStrainer

from peewee import *

db = SqliteDatabase('dlList.db')

class DLFile(Model):
    name = CharField()
    url = CharField()

    class Meta:
        database = db 
db.connect()

DLFile.create_table(True)

downloader = transmissionrpc.Client('127.0.0.1')



debug = 0
verbosity = 0;

def add_dl(url,name):

    print("New file for DL "+ name , "," + url)
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

    fileRecord = DLFile(name = name, url = url.encode('utf-8'))
    fileRecord.save()


    if  not debug:
        dir = downloader.session_stats().download_dir+'/'+name+'/'
        print(dir)
        d = os.path.dirname(dir)
        if not os.path.exists(d):
            os.makedirs(d)
        #try:
        #    print( url)
        downloader.add_uri(url,download_dir = dir)
        #except:
        #    print( "Bad torrent !  \n")
    else:
        print("[debug] name=" + name + " url=" + url )
    


def parse_site(terms):
    #first pass
    going_on = True
    page_number = 1;
    soup = BeautifulSoup(urllib.request.urlopen('http://www.tokyotosho.info/search.php?terms='+urllib.request.quote(terms)).read(),"lxml")
    while going_on:
        baselist = soup.body.div.findAll('table')[2].tr.nextSibling
        #print(baselist)
        for b in baselist:
            print(b)
            allRefs = b.findAll('a')
            if len(allRefs) > 1:
                reflist = b.findAll('a')[1]
                if (reflist):
                    if reflist.get('type') == 'application/x-bittorrent':
                        add_dl(reflist.get('href'),reflist.text)
                    
    #go next pages

        #get page number/ page count
        try: 
            stringa = soup.body.div.findAll('p')[1].findAll('a')[0].get('href')
        except:
            print( '(no next href)End! \n')
            break

        basepagenumber =  int(stringa[stringa.find('page=')+5:stringa.find('&terms')]) 
        if page_number == 1: basepagenumber = 1
        try:
            nextlink =  soup.body.div.findAll('p')[1].findAll('a')[page_number-basepagenumber].get('href')
        except :
            print( 'End! \n')
            break
        nextlink =  'http://www.tokyotosho.info/search.php' + nextlink 
        print( 'Going next page url= '+nextlink + '\n')
        page_number  = page_number + 1 
        soup = BeautifulSoup(urllib.request.urlopen(nextlink).read(),"lxml")
    
        
    


def dofile(seriesListFileName):
    for line in fileinput.input(seriesListFileName):
        print("parsing line="+ line)
        parse_site(line.rstrip('\n'))
    fileinput.close()




class TimeoutException(Exception): 
    pass 

def timeout_handler(signum, frame):
    raise TimeoutException()





signal.signal(signal.SIGALRM, timeout_handler) 
signal.alarm(600) # triger alarm in 5 minuts

argumentsParser = argparse.ArgumentParser()
argumentsParser.add_argument('f', type = str, help = "provide a series name for search and load")
argumentsParser.add_argument('-v', "--verbosity" , action = "count" , default = 0 ,help = "set verbosity level")
arguments = argumentsParser.parse_args()
verbosity  = arguments.verbosity
parse_site(arguments.f)



