## 황영호(자연어처리 16회차) - 9oormthon

### 현재(2024.01.06)까지의 작업 내용

* GitHub : https://github.com/Serang9oorm/NaverNews

* Page : https://serang9oorm.github.io/NaverNews 또는 http://3.37.66.31


* AWS 서버 세팅(http://3.37.66.31)

  nginx 웹서버 / Flask 설치 / MySQL 설치

* 내용

  로컬에서 최근날짜와 분류 카테고리를 입력하면 Flask 서버 API를 호출하여 네이버뉴스를 크롤링하여 서버DB(AWS MySQL)에 저장하고 로컬로 리턴한다.

  날짜지정(시작일-종료일)<br>
  분류 선택<br>
  언론사 선택<br>
  Page Size(화면 페이지당 줄수)<br>
  Max Page(크롤링시 최대페이지)
  
* 서버 API 호출:

  > 예) http://3.37.66.31/NaverNews?startDate=2024-01-02&endDate=2024-01-05&category=105&press=&pageSize=20&maxPage=0

  <pre>
    서버        : http://3.37.66.31/NaverNews
    startDate   : 시작날짜 (오늘~30일이전)
    endData     : 종료날짜 (오늘~30일이전)
    category    : 분류
    press       : 언론사
    pageSize    : 결과 화면 한페이지당 줄 수
    maxPage     : 크롤링시 최대 페이지 / 0 제한없음
</pre>

