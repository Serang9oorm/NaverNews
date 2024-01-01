# -*- coding: utf-8 -*-

import sys, json, requests
import datetime
import random
import logging
from json import dumps as json_encode

import pandas as pd

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


@app.route('/NaverNews', methods=['GET', 'POST'])
def naverNews():

    startDate = request.args.get( 'startDate', '' )
    endDate = request.args.get( 'endDate', '' )
    category = request.args.get( 'category', '' )
    press = request.args.get( 'press', '' )
    pageSize = request.args.get( 'pageSize', '' )
    maxPage = request.args.get( 'maxPage', '' )

    print( '/NaverNews ', "StartDate:", startDate, ", EndDate:", endDate, ", Category:", category, "Press:", press, "PageSize:", pageSize, "MaxPage:", maxPage )

    now = datetime.datetime.now()
    nowDate = now.strftime('%Y%m%d')
    startDate = startDate.replace("-","")
    endDate = endDate.replace("-","")

    maxPage = 10
    query = ''
    sort = '1' #관련도순=0  최신순=1  오래된순=2

    # Crawling - NaverNews
    #crawler( maxPage, query, sort, startDate, endDate )

    df = pd.DataFrame(
        [ [ "2023.11.30. 오전 10:46", "IT과학", "뉴시스", "'외국인 민원 OK' 보은군, 인공지능 통번역기 운영", "65개 언어 지원…언어장벽 해소보은군에서 외국인 민원인을 위해 운영 중인 인공지능 ...", "https://n.news.naver.com/mnews/article/003/001", "..." ],
          [ "2023.11.29. 오후 5:11", "IT과학", "연합뉴스", "NIA, 인공지능 기업 CEO들과 AI 윤리 확산 간담회", "AI 윤리 확산 CEO 간담회[한국지능정보사회진흥원 제공] (서울=연합뉴스) ...", "https://n.news.naver.com/mnews/article/001/001", "..." ],
          [ "2023.11.30. 오전 7:23", "IT과학", "헤럴드경제", "경콘진, '인공지능 활용 게임 제작 매뉴얼' 배포", "[경콘진 제공][헤럴드경제(수원)=박정규 기자]경기콘텐츠진흥원(원장 탁용석)은 20...", "https://n.news.naver.com/mnews/article/016/000", "..." ],
          [ "2023.11.29. 오후 4:33", "IT과학", "노컷뉴스", "'원주시를 인공지능 실리콘 밸리로'", "핵심요약원주시, 국내 혁신 선도기업과 AI얼라이언스 공동연구센터 구축29일 원주시와...", "https://n.news.naver.com/mnews/article/079/000", "..." ]
        ],
        columns=[ "date", "category", "press", "title", "document", "link", "summary" ]
    )
    #print(df)

    r = df.to_json( orient="columns" )
    #print( "json:", r, r.encode("utf-8") )

    #df2 = pd.read_json(js)
    #print( 'df2', df2)

    return make_response( r.encode("utf-8"), 200 )


def crawler( maxpage, query, sort, s_date, e_date):

    page = 1  
    maxpage_t =(int(maxpage)-1)*10+1   # 11= 2페이지 21=3페이지 31=4페이지  ...81=9페이지 , 91=10페이지, 101=11페이지
    
    titleList = []
    linkList = []
    pressList = []
    dateList = []
    documentList = []
    summaryList = []

    while page <= maxpage_t:

        #url = "https://search.naver.com/search.naver?where=news&query=" + query + "&sort="+sort+"&ds=" + s_date + "&de=" + e_date + "&nso=so%3Ar%2Cp%3Afrom" + s_from + "to" + e_to + "%2Ca%3A&start=" + str(page)
        url = "https://search.naver.com/search.naver?where=news&" + "&sort="+sort+"&ds=" + s_date + "&de=" + e_date + "start=" + str(page)
        
        response = requests.get(url)
        html = response.text

        #뷰티풀소프의 인자값 지정
        soup = BS(html, 'html.parser')
 
        #<a>태그에서 제목과 링크주소 추출
        atags = soup.select('._sp_each_title')
        print(atags)
        
        for atag in atags:
            print(atag.text)

            titleList.append(atag.text)     #제목
            linkList.append(atag['href'])   #링크주소
            
        #신문사 추출
        press_lists = soup.select('._sp_each_source')
        for press_list in press_lists:
            pressList.append(press_list.text)    #신문사
        
        #날짜 추출 
        date_lists = soup.select('.txt_inline')
        for date_list in date_lists:
            #test=date_list.text   
            #date_cleansing(test)  #날짜 정제 함수사용 
            dateList.append(date_list.text)
        
        #본문요약본
        summary_lists = soup.select('ul.type01 dl')
        for summary_list in summary_lists:
            #print('==='*40)
            #print(contents_list)
            #contents_cleansing(contents_list) #본문요약 정제화
            summaryList.append(summary_list.text)

        print(page)
        
        page += 10
    
    print('titleList:', titleList)
    print('linkList:', linkList) 
    print('pressList:', pressList)
    print('dateList:', dateList)
    print('documentList:', documentList)
    print('summaryList:', summaryList)

    #모든 리스트 딕셔너리형태로 저장
    result= {"date" :       dateList , 
                "press" :      pressList ,
                "title":       titleList ,  
                "summary":     summaryList ,
                "link":        linkList }
    
    df = pd.DataFrame(result)  #df로 변환

    df.to_csv( 'result.csv')
    
    return df


# ----------------------------------------------------------------------------------------------------------------------

if __name__=="__main__":

    createDB_Serang9oorm()

    app.run(host='0.0.0.0', debug=True)
 
    print("Hello Serang9oorm!")