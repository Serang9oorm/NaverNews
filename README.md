## 황영호(자연어처리 16회차) - 9oormthon

* GitHub : https://github.com/Serang9oorm/NaverNews


* Page : https://serang9oorm.github.io/NaverNews


* AWS 서버 (http://13.124.240.133/)

  nginx 웹서버 / Flask 설치 / MySQL 설치


* 서버 API 호출

  **1 Get News from DB (Action: GetNews)**
 
    서버의 MySQL DB에 저장된 Naver News 가져온다.

    로컬에서 날짜지정, 기사분류, 특정 언론사를 입력 실행하면 Flask 서버 API를 호출하여 서버DB(AWS MySQL)로부터 저장된 뉴스기사를 리턴한다.
  
  > 예) http://13.124.240.133/NaverNews/GetNews?startDate=2024-01-04&endDate=2024-01-05&category=105&press=&pageSize=10&maxPage=0


  **2 Start Server Crawler (Action: StartCrawler)**
  
    서버의 Naver News Crawler를 실행하고 서버 MySQL DB에 저장한다.

    로컬에서 날짜지정, 기사분류, 특정 언론사를 입력 실행하면 Flask 서버 API를 호출하여 네이버뉴스를 크롤링하여 서버DB(AWS MySQL)에 저장하고 로컬로 리턴한다.
 
  > 예) http://13.124.240.133//NaverNews/StartCrawler?startDate=2024-01-04&endDate=2024-01-05&category=105&press=&pageSize=10&maxPage=0


 <pre>
    API Server  : http://13.124.240.133/NaverNews/
    Action      : GetNews 또는 StartCrawler 
    startDate   : 시작날짜 (오늘~30일이전)
    endData     : 종료날짜 (오늘~30일이전)
    category    : 분류 (정치, 경제, 사회, 생활/문화, IT/과학, 세계)
    press       : 언론사 (입력 없으면 전체언론사)
    pageSize    : 결과 화면 한페이지당 줄 수
    maxPage     : 결과 화면 최대 페이지 / 0 제한없음
  </pre>

  
* 서버 API 호출:

 
