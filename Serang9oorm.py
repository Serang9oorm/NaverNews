# -*- coding: utf-8 -*-

import os
import sys, json, requests, re
import datetime
import time
import random
import logging
import pandas as pd

from json import dumps as json_encode

from urllib.parse import urljoin

from bs4 import BeautifulSoup as BS

from tqdm.notebook import tqdm

import konlpy
#import nltk
from konlpy.tag import Okt
import joblib

from flask import Flask, request, jsonify, Response
from flask import render_template
from flask import make_response, redirect

from config import *
from db import *

app = Flask(__name__)

#model = joblib.load('/home/ubuntu/Serang9oorm/model/RandomForestClassifier_model_20240110.pkl')
#df_words = pd.read_csv( "/home/ubuntu/Serang9oorm/model/data_words.csv", index_col=0 )

# home ----------------------------------------------------------------------------------------------------------------
#@app.route("/", methods=['GET', 'POST'] )
@app.route('/')
@app.route('/index.html')
def home():
    return render_template( 'index.html' )


@app.route('/Classification', methods=['POST'])
def classification():

    article = request.form.get( 'article', '' )
    #print( 'article:', article )

    r = getClassfication( article )
    #r = "서버 지연으로 아직 제공되지 않습니다."

    return make_response( r.encode("utf-8"), 200 )


@app.route('/NaverNews/<act>', methods=['GET'])
def naverNews( act ):

    startDate = datetime.datetime.strptime( request.args.get( 'startDate' ), '%Y-%m-%d' )
    endDate = datetime.datetime.strptime( request.args.get( 'endDate' ), '%Y-%m-%d' )
    category = request.args.get( 'category' )
    press = request.args.get( 'press', '' )
    pageSize = int( request.args.get( 'pageSize', '20' ) )
    maxPage = int( request.args.get( 'maxPage', '0' ) )

    #print( type(startDate), type(endDate), type(pageSize), type(maxPage) )
    print( '/NaverNews/', act, 'StartDate:', startDate, ", EndDate:", endDate, ", Category:", category, "Press:", press, "PageSize:", pageSize, "MaxPage:", maxPage ) , "StartDate:", startDate, ", EndDate:", endDate, ", Category:", category, "Press:", press, "PageSize:", pageSize, "MaxPage:", maxPage 
  
    if ( act == 'GetNews' ):

        columns = [ "date", "category", "press", "title", "document", "link" ]

        # Mock Data
        # df = pd.DataFrame(
        #     [   [ "2023.11.30. 오전 10:46", "IT과학", "뉴시스", "'외국인 민원 OK' 보은군, 인공지능 통번역기 운영", "65개 언어 지원…언어장벽 해소보은군에서 외국인 민원인을 위해 운영 중인 인공지능 ...", "https://n.news.naver.com/mnews/article/003/001" ],
        #         [ "2023.11.29. 오후 5:11", "IT과학", "연합뉴스", "NIA, 인공지능 기업 CEO들과 AI 윤리 확산 간담회", "AI 윤리 확산 CEO 간담회[한국지능정보사회진흥원 제공] (서울=연합뉴스) ...", "https://n.news.naver.com/mnews/article/001/001" ],
        #         [ "2023.11.30. 오전 7:23", "IT과학", "헤럴드경제", "경콘진, '인공지능 활용 게임 제작 매뉴얼' 배포", "[경콘진 제공][헤럴드경제(수원)=박정규 기자]경기콘텐츠진흥원(원장 탁용석)은 20...", "https://n.news.naver.com/mnews/article/016/000" ],
        #         [ "2023.11.29. 오후 4:33", "IT과학", "노컷뉴스", "'원주시를 인공지능 실리콘 밸리로'", "핵심요약원주시, 국내 혁신 선도기업과 AI얼라이언스 공동연구센터 구축29일 원주시와...", "https://n.news.naver.com/mnews/article/079/000" ]
        #     ],
        #     columns=columns
        # )

        endDate = endDate + datetime.timedelta(days=1)

        seekTable = TABLE_News
        seekField = "DATE_FORMAT( newsDate, '%Y-%m-%d %H:%i:%s' ), category, press, title, documentHead, link"
        seekWhere = f"newsDate >= '{startDate}' and newsDate < '{endDate}' and " + f"category = '{category}'" + ( '' if press == '' else "and press LIKE '%" + f"{press}%'" )
        #print( seekTable, seekField, seekWhere )        

        newsList = getData( seekTable, seekField, seekWhere, many=MANY_ALL )
        #print( newsList )

        maxCount = pageSize * maxPage       

        if maxCount == 0 or maxCount >= len( newsList ):

            df = pd.DataFrame( newsList, columns=columns )
            
        else:

            df = pd.DataFrame( newsList[:maxCount], columns=columns )

    else:

        # Crawling - NaverNews
        df = crawler( startDate, endDate, category, press, pageSize, maxPage )


    df['category'] = df['category'].apply( getCategoryName )
    #print(df)

    r = df.to_json( orient="columns" )
    #print( "json:", r, r.encode("utf-8") )

    return make_response( r.encode("utf-8"), 200 )


def crawler( startDate, endDate, category, press, pageSize, maxPage ):

    categoryName = getCategoryName( category )

    # Get Crawling Date Range
    dateRange_list = []
    for date in pd.date_range( start=startDate, end=endDate, freq='D' ):
        dateRange_list.append( date.strftime( "%Y%m%d" ) )
    print( 'dateRange:', dateRange_list )

    #NaverNews = "https://news.naver.com/main/main.naver?mode=LSD&mid=shm&sid1={sid}#&date=%2000:00:00&page={page}"
    NaverNews = "https://news.naver.com/main/list.naver"
    #NaverNewsPage = "?mode=LS2D&mid=shm&sid1={sid1}&sid2={sid2}&date={date}&page={page}"
    NaverNewsPage = "?mode=LS2D&sid2={sid2}&sid1={sid1}&mid=shm&date={date}&page={page}"

    req_header_dict = {
        'user-agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'
    }
  
    sid2List = { '100':  [ '264', '265', '266', '267', '268', '269' ],
                 '101':  [ '258', '270', '271', '272', '273', '274', '275' ],
                 '102':  [ '249', '250', '251', '252', '254', '255', '256', '257', '276', '59b' ],
                 '103':  [ '237', '238', '239', '240', '241', '242', '243', '244', '245', '248', '376' ],
                 '104':  [ '231', '232', '233', '234', '322' ],
                 '105':  [ '226', '227', '228', '229', '230', '283', '731', '732' ]
    }
                 
    sid1 = category
    sid2_list = sid2List[ sid1 ]
    #sid2_list = [ '732' ]
    print( 'sid1:', sid1, 'sid2:', sid2_list )

    # Get PageLinks --------------------------------------------------------------------------------------------------
    pageLink_list = []

    for sid2 in sid2_list:

        #print( "Sid:", sid1, sid2 )
        
        for date in dateRange_list:

            print( "Sid:", sid1, sid2, "Date:", date )

            nPage = 1
            nOldPage = 0
            
            while nPage > nOldPage:

                nOldPage = nPage
                
                url = NaverNewsPage.format( sid1=sid1, sid2=sid2, date=date, page=nPage )
                #print( 'url:', url )
                
                res = requests.get( NaverNews + url, headers=req_header_dict )
                
                if res.ok:
        
                    pageLink_list.append( url )
        
                    html = res.text
                    soup = BS( html, 'html.parser' ) 
                    page_list = soup.select( "div.paging > a" ) 
                        
                    #print( "page_list:", len(page_list) )
                    for page in page_list:
                        
                        link = page['href']
                        #print( 'page #', page.get_text(), link )

                        if ( page.get_text() == '이전' ):
                            continue
                            
                        elif ( page.get_text() == '다음' ):
                            nPage = nPage + 10

                        else:
                            pageLink_list.append( link )
        
                    #print('\n')
        

    for pl in pageLink_list:
        print(pl)
    print( "Total Pages:", len( pageLink_list ) )  

    # Get Articles -------------------------------------------------------------------------------------------------------
    
    # Initialize Rerurn Data
    date_list = []
    category_list = []
    press_list = []
    title_list = []
    document_list = []
    documentHead_list = []
    link_list = []

    articleCount = 0
    duplicationCount = 0
    errorCount = 0
    
    for url in pageLink_list:

        res = requests.get( NaverNews + url, headers=req_header_dict )
        
        if res.ok:

            html = res.text
            soup = BS( html, 'html.parser' ) 

            for body in [ "ul.type06_headline", "ul.type06" ]:

                try:

                    item_list = soup.select( body + " > li > dl" ) 
                    
                    #print( "item_list:", body, len(item_list) )
                    for item in item_list:

                        #print( '-' * 60 )
                        link = item.a['href']
                        article_link = link if link.find('?') < 0 else link[0:link.find('?')]
                        #print( "Link:", link, article_link )
                        #print( "Link:", link )

                        article_documentHead = removeMark( item.select_one( "span.lede" ).get_text() )
                        #print( "DocumentHead:", article_documentHead )

                        article_press = item.select_one( "span.writing" ).get_text()
                        pressCheck = ( press in article_press ) if press != '' else True    # 언론사 포함 검사
                        #print( "Press: ( ", press, ")", article_press, pressCheck )

                        # 중복 검사
                        if article_link not in link_list:
                    
                            #print( '-' * 60 )
                            #print( 'Request:', article_link )
                            #time.sleep( random.uniform(2,4) )
                            time.sleep(0.5)
                        
                            article_res = requests.get( link, headers=req_header_dict )
                            #print( article_res.status_code, article_res.ok )
                            #print( article_res.headers, article_res.request.headers )
                            #print( article_res.text )

                            if article_res.ok:

                                #print( '=' * 60 )            
                                article_html = article_res.text
                                article_soup = BS( article_html, 'html.parser' )
                                
                                article_title = removeMark( article_soup.select_one( "h2#title_area > span" ).get_text() )
                                #print( "Title:", article_title )

                                article_datetime = article_soup.select( "span._ARTICLE_DATE_TIME" )[0]['data-date-time']
                                article_date = datetime.datetime.strptime( article_datetime, "%Y-%m-%d %H:%M:%S" )
                                #print( "DateTime:", article_date )

                                #article_document = article_soup.select( "article#dic_area" )[0]
                                #document = removeMark( article_document.get_text() )
                                article_document = removeMark( article_soup.select( "article#dic_area" )[0].get_text() )
                                #print( "Document:", article_document )

                                if pressCheck:
                                    
                                    articleCount += 1
                                    print( '[추가] Count:', articleCount, article_link )

                                    # Append DataFrame 
                                    date_list.append( article_datetime )
                                    category_list.append( category )
                                    press_list.append( article_press )
                                    title_list.append( article_title )
                                    document_list.append( article_document )
                                    documentHead_list.append( article_documentHead )
                                    link_list.append( article_link )

                                    # Save to DB
                                    save2DB( article_datetime, 
                                             category, 
                                             article_press, 
                                             article_title, 
                                             article_document, 
                                             article_documentHead, 
                                             article_link
                                    )

                        else:
                            duplicationCount += 1
                            print( '[중복] Count: (', duplicationCount, ')', articleCount, article_link )

                except:
                    errorCount += 1
                    print( '[오류] Count:', errorCount, article_link )
      
    print( 'Total Articles:', articleCount, len( link_list ), 'Duplicated Counts:', duplicationCount, 'Error Count:', errorCount )

    result = {  'date'          : date_list,
                'category'      : category_list,
                'press'         : press_list,
                'title'         : title_list,
                'document'      : document_list,
                'documentHead'  : documentHead_list,
                'link'          : link_list
    }

    # Make DataFrame
    df = pd.DataFrame( result )

    # 리턴할 데이터프레임 변경
    df = df.drop('document', axis=1)
    df.rename( columns={ 'documentHead' : 'document' }, inplace=True )

    maxCount = pageSize * maxPage
    if ( maxCount > 0 and df['date'].count() > maxCount ):
        df = df.head( maxCount )   #maxCount는 Return 자료에만 적용

    # df.to_csv( 'result.csv', index=False, encoding="utf-8-sig" )

    print( "Complete!", '-' * 60 )

    return df


def save2DB( date, category, press, title, document, documentHead, link ):
    
    result = False

    saveData = { 'date'          : [ date ],
                 'category'      : [ category ],
                 'press'         : [ press ],
                 'title'         : [ title ],
                 'document'      : [ document ],
                 'documentHead'  : [ documentHead ],
                 'link'          : [ link ]
    }

    # Make DataFrame
    df = pd.DataFrame( saveData )

    # 특수문자 제거
    df["title"] = df["title"].str.replace( pat=r'[^\w]', repl=r' ', regex=True )
    df["document"] = df["document"].str.replace( pat=r'[^\w]', repl=r' ', regex=True )
    df["documentHead"] = df["documentHead"].str.replace( pat=r'[^\w]', repl=r' ', regex=True )

    # DB 저장
    for idx, row in df.iterrows():

        #print( "DB:", idx, row['link'] )

        news_data = {   'newsDate'        : row['date'],
                        'category'        : row['category'],
                        'press'           : row['press'],
                        'title'           : row['title'],
                        'document'        : row['document'],
                        'documentHead'    : row['documentHead'],
                        'link'            : row['link'],
                        'summary'         : ''
        }
        
        result = insertData( TABLE_News, news_data )
        #db.insertData( TABLE_News, { 'date': article_date, 'category': categoryName, 'press': article_press, 'title': item.a.get_text(), 'document': document, 'link': link, 'summary': documentHead } )

    return result


def getClassfication( article ):

    print( "Article:", article )

    #print( "Location:", os.getcwd() )

    okt = Okt()

    #raw = okt.pos( article, norm=True, stem=True )
    raw = okt.pos( article )
    print( "Pos:", raw )
    
    words = []
    for word, pos in raw:
        if pos in ["Noun", "Verb", "Adjective", "Adverb"]:
            words.append(word)
    print( "Words:", words )

    vc = pd.Series(words).value_counts()
    print( "Vc:", vc )

    df_words = pd.read_csv( "/home/ubuntu/Serang9oorm/model/data_words.csv", index_col=0 )
    print( "DataWords:", df_words )

    temp = pd.DataFrame( columns=df_words.columns )

    for word in vc.index:
        count = vc.loc[word]
        if word in df_words.columns:
            temp.loc[0, word] = count

    temp.fillna( 0, inplace=True )
    print( "Temp:", temp )

    # section = { 0: "정치", 1: "경제", 2: "사회", 3: "생활/문화", 4: "세계", 5: "IT/과학" }

    # model = joblib.load('/home/ubuntu/Serang9oorm/model/RandomForestClassifier_model_20240110.pkl')
    # print( "Model loaded!" )

    # predict = model.predict( temp )

    # predictResult = "이 기사는 '" + section[ predict[0] ] + "' 뉴스입니다!"
    # print( predictResult )
    predictResult = "predict test..."

    return predictResult


def getCategoryName( category ):

    categoryName = { '100': '정치', '101' : '경제', '102' : '사회', '103' : '생활/문화', '105' : 'IT/과학', '104' : '세계' }[category]
    #print( categoryName )

    return categoryName
    
# ----------------------------------------------------------------------------------------------------------------------

if __name__=="__main__":

    createDB_Serang9oorm()

    app.run(host='0.0.0.0', debug=True)
 
    print("Hello Serang9oorm!")