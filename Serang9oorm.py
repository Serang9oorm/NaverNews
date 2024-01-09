﻿# -*- coding: utf-8 -*-

import sys, json, requests, re
import datetime
import time
import random
import logging
from json import dumps as json_encode

import pandas as pd

from urllib.parse import urljoin

from bs4 import BeautifulSoup as BS

from flask import Flask, request, jsonify, Response
from flask import render_template
from flask import make_response, redirect

from config import *
from db import *

app = Flask(__name__)

# home ----------------------------------------------------------------------------------------------------------------
#@app.route("/", methods=['GET', 'POST'] )
@app.route('/')
@app.route('/index.html')
def home():
    return render_template( 'index.html' )


@app.route('/NaverNews/<act>', methods=['GET', 'POST'])
def naverNews( act ):

    startDate = datetime.datetime.strptime( request.args.get( 'startDate' ), '%Y-%m-%d' )
    endDate = datetime.datetime.strptime( request.args.get( 'endDate' ), '%Y-%m-%d' ) + datetime.timedelta(days=1)
    category = request.args.get( 'category' )
    press = request.args.get( 'press', '' )
    pageSize = int( request.args.get( 'pageSize', '20' ) )
    maxPage = int( request.args.get( 'maxPage', '0' ) )

    #print( type(startDate), type(endDate), type(pageSize), type(maxPage) )
    print( '/NaverNews/', act, 'StartDate:', startDate, ", EndDate:", endDate, ", Category:", category, "Press:", press, "PageSize:", pageSize, "MaxPage:", maxPage ) , "StartDate:", startDate, ", EndDate:", endDate, ", Category:", category, "Press:", press, "PageSize:", pageSize, "MaxPage:", maxPage 
  
    if ( act == 'GetNews' ):

        columns = [ "date", "category", "press", "title", "document", "link" ]

        # df = pd.DataFrame(
        #         [   [ "2023.11.30. 오전 10:46", "IT과학", "뉴시스", "'외국인 민원 OK' 보은군, 인공지능 통번역기 운영", "65개 언어 지원…언어장벽 해소보은군에서 외국인 민원인을 위해 운영 중인 인공지능 ...", "https://n.news.naver.com/mnews/article/003/001" ],
        #             [ "2023.11.29. 오후 5:11", "IT과학", "연합뉴스", "NIA, 인공지능 기업 CEO들과 AI 윤리 확산 간담회", "AI 윤리 확산 CEO 간담회[한국지능정보사회진흥원 제공] (서울=연합뉴스) ...", "https://n.news.naver.com/mnews/article/001/001" ],
        #             [ "2023.11.30. 오전 7:23", "IT과학", "헤럴드경제", "경콘진, '인공지능 활용 게임 제작 매뉴얼' 배포", "[경콘진 제공][헤럴드경제(수원)=박정규 기자]경기콘텐츠진흥원(원장 탁용석)은 20...", "https://n.news.naver.com/mnews/article/016/000" ],
        #             [ "2023.11.29. 오후 4:33", "IT과학", "노컷뉴스", "'원주시를 인공지능 실리콘 밸리로'", "핵심요약원주시, 국내 혁신 선도기업과 AI얼라이언스 공동연구센터 구축29일 원주시와...", "https://n.news.naver.com/mnews/article/079/000" ]
        #         ],
        #         columns=columns
        # )

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

        df['category'] = df['category'].apply(getCategoryName)

    else:

        # Crawling - NaverNews
        df = crawler( startDate, endDate, category, press, pageSize, maxPage )

    #print(df)

    r = df.to_json( orient="columns" )
    #print( "json:", r, r.encode("utf-8") )

    return make_response( r.encode("utf-8"), 200 )


def crawler( startDate, endDate, category, press, pageSize, maxPage ):

    categoryName = getCategoryName( category )

    NaverNews = "https://news.naver.com/main/main.naver?mode=LSD&mid=shm&sid1={sid}#&date=%2000:00:00&page={page}"

    req_header_dict = {
        # 요청헤더 : 브라우저 정보
        'user-agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'
    }
  
    #[ [ "2023.11.30. 오전 10:46", "IT과학", "뉴시스", "'외국인 민원 OK' 보은군, 인공지능 통번역기 운영", "65개 언어 지원…언어장벽 해소보은군에서 외국인 민원인을 위해 운영 중인 인공지능 ...", "https://n.news.naver.com/mnews/article/003/001", "..." ],
    date_list = []
    category_list = []
    press_list = []
    title_list = []
    documentHead_list = []
    link_list = []

    dateUnderCheck = False
    dateOverCheck = False

    articleCount = 0
    duplicationCount = 0
    maxCount = pageSize * maxPage

    nPage = 1

    while not dateOverCheck and ( maxCount == 0 or articleCount < maxCount ):
        
        print( 'nPage:', nPage )
        url = NaverNews.format( sid=category, page=nPage )

        res = requests.get( url, headers=req_header_dict ) 
        print( res.status_code, res.ok )
        #print( type(res) ) 
        #print( '응답헤더', res.headers )
        #print( '요청헤더', res.request.headers )
        #print( res.text )
        
        if res.ok:
            
            html = res.text
            soup = BS( html, 'html.parser' )
            #sh_list = soup.select("div._persist > div.section_headline > ul > li > div.sh_text")
            sh_list= soup.select("div.sh_text")
                
            print( 'Headline Count:', len(sh_list) )
            for item in sh_list:

                #print(item)
                print( '-' * 60 )
                article_title = removeMark( item.a.get_text() )
                print( "Title:", article_title )
                link = item.a['href']
                print( "Link0:", item.a['href'] )
                link = link if link.find('?') < 0 else link[0:link.find('?')]
                print( "Link:", link )
                documentHead = removeMark( item.select_one("div.sh_text_lede").get_text() )
                print( "DocumentHead:", documentHead )
                article_press = removeMark( item.select_one("div.sh_text_press").get_text() )
                pressCheck = ( press in article_press ) if press != '' else True
                print( "Press: ( ", press, ")", article_press, pressCheck )
                #print( '=' * 60 )            

                # 중복 검사
                if link not in link_list:
            
                    print( 'Request:', link )
                    time.sleep(0.5)
                    #time.sleep( random.uniform(2,4) )

                    article_res = requests.get( link, headers=req_header_dict )
                    print( article_res.status_code, article_res.ok )
                    #print( '응답헤더', article_res.headers )
                    #print( '요청헤더', article_res.request.headers )
                    #print( article_res.text )

                    if article_res.ok:

                        print( '=' * 60 )            
                        article_html = article_res.text
                        article_soup = BS( article_html, 'html.parser' )
                        #sh_list = soup.select("div._persist > div.section_headline > ul > li > div.sh_text")
                        
                        #datetime = article_soup.select("span._ARTICLE_DATE_TIME").find['data-date-time']
                        article_datetime = article_soup.select("span._ARTICLE_DATE_TIME")[0]['data-date-time']
                        #datetime = datetime['data-date-time']
                        print( "DateTime:", article_datetime )
                        article_date = datetime.datetime.strptime( article_datetime, "%Y-%m-%d %H:%M:%S" )
                        #print( "DateTime:", type(article_date), article_date )

                        #dateCheck = ( article_date >= startDate ) and ( article_date < endDate )
                        dateUnderCheck = ( article_date < startDate )
                        dateOverCheck = ( article_date >= endDate )
                        print( "DateCheck:", dateUnderCheck, dateOverCheck )

                        article_document = article_soup.select("article#dic_area")[0]
                        document = removeMark( article_document.get_text() )
                        
                        #print( "Document:", document )

                        if dateOverCheck:
                            print( 'Date Over:', startDate, endDate, article_date )
                            break
                            
                        elif dateUnderCheck:
                            continue

                        elif pressCheck:
                            
                            articleCount += 1
                            print( '[추가] Page:', nPage, ', Count:', articleCount )

                            date_list.append( article_datetime )
                            category_list.append( categoryName )
                            press_list.append( article_press )
                            title_list.append( article_title )
                            documentHead_list.append( documentHead )
                            link_list.append( link )

                            news_data = { 'newsDate'        : article_datetime,
                                          'category'        : category,
                                          'press'           : article_press,
                                          'title'           : article_title,
                                          'document'        : document,
                                          'documentHead'    : documentHead,
                                          'link'            : link,
                                          'summary'         : ''
                                         }
                            
                            insertData( TABLE_News, news_data )
                            #db.insertData( TABLE_News, { 'date': article_date, 'category': categoryName, 'press': article_press, 'title': item.a.get_text(), 'document': document, 'link': link, 'summary': documentHead } )
                
                else:
                    duplicationCount += 1
                    print( '[중복] Page:', nPage, ', Count: (', duplicationCount, ')', articleCount, link )

            nPage += 1

        else:
            dateCheck = False

    print( '총갯수:', articleCount, '총중복갯수:', duplicationCount, '총페이지수:', nPage - 1 )

    result = {  'date'      : date_list,
                'category'  : category_list,
                'press'     : press_list,
                'title'     : title_list,
                'document'  : documentHead_list,
                'link'      : link_list
            }
    
    df = pd.DataFrame( result )
    df.to_csv( 'result.csv')

    return df


def getCategoryName( category ):

    categoryName = { '100': '정치', '101' : '경제', '102' : '사회', '103' : '생활/문화', '105' : 'IT/과학', '104' : '세계' }[category]
    #print( categoryName )

    return categoryName
    
# ----------------------------------------------------------------------------------------------------------------------

if __name__=="__main__":

    createDB_Serang9oorm()

    app.run(host='0.0.0.0', debug=True)
 
    print("Hello Serang9oorm!")