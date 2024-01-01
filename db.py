# -*- coding: utf-8 -*-

import os
import sys

import timeit
import datetime
import json

import mysql.connector as mdb

from config import *

# Table of Content
TABLE_News = 'NaverNews'

FIELD_News_ID = 'news_id'            # News
FIELD_NewsDate = 'newsDate'          # 날짜
FIELD_Category = 'category'          # 분류
FIELD_Press = 'press'                # 신문사
FIELD_Title = 'title'                # 제목
FIELD_Document = 'document'          # 내용
FIELD_Link = 'link'                  # Link
FIELD_Summary = 'summary'            # 요약


def createDB_Serang9oorm():

    print( "* DB", DB_Name, Host_Name, Port_No, User_Name, Pass_Word, DB_Name, Char_Set )

    result = False

    # Open database connection
    db = mdb.connect(
        host = Host_Name,           # MySQL 서버 호스트
        user = User_Name,           # MySQL 사용자 이름
        password = Pass_Word,       # MySQL 암호
        database = DB_Name          # 연결할 데이터베이스
    )

    print( 'db:', db )

    try:

        cursor = db.cursor()

        # execute SQL query using execute() method.
        cursor.execute( "SELECT VERSION()" )
        print( "Database version : %s " % cursor.fetchone() )

        # User Table - news
        sql = """
            (
            newsDate datetime,
            category varchar(30) default '',
            press varchar(50) default '',
            title varchar(100) default '',
            document text,
            link varchar(100) default '',
            summary text,
            primary key( newsDate, press )
            )
            """
        createTable( TABLE_News, DB_Name, sql, cursor )

        # 연결 및 커서 닫기
        cursor.close()
        db.close()

        result = True

    except mdb.Error as e:
        #except mysql.connector.errors.ProgrammingError as err:
        db.rollback()
        print( "Error: %d, %s" % ( e.args[0], e.args[1] ) )
        #sys.exit(1)

    except FileNotFoundError as e:
        print( 'Error occured: ', e )

    finally:
        print('finally close')
        if db:
            db.close()

    return result


def createTable( tableName, dbName, sql, cursor ):
# Table Shmema를 확인하고 없으면 테이블을 새로 생성한다.

    schemaSql = "Select 1 From Information_Schema.tables Where Table_Name='" + tableName + "' and Table_Schema='" + dbName + "'"

    cursor.execute( schemaSql )

    if ( cursor.fetchone() == None ):

        # SQL 쿼리 실행
        cursor.execute( 'CREATE TABLE ' + tableName + ' ' + sql )
        print( 'Create Table:', tableName, 'on DB:', dbName )

        # 결과 가져오기
        results = cursor.fetchall()


def insertData( table, tableValue, dbName=DB_Name, InsertMode="INSERT" ):
# Table에 새로운 데이타{ 'field': value }를 추가한다.
    #print( '[insertData] table:', table, '/tableValue:', tableValue )

    result = False

    try:
        # Open database connection
        db = mdb.connect(
            host = Host_Name,           # MySQL 서버 호스트
            user = User_Name,           # MySQL 사용자 이름
            password = Pass_Word,       # MySQL 암호
            database = DB_Name          # 연결할 데이터베이스
        )

        #cursor = db.cursor( mdb.cursors.DictCursor )
        cursor = db.cursor()

        fields = ''
        values = ''
        count = 0

        for key, value in tableValue.items():

            fields += key
            quotation = getQuotation( value )
            values += quotation + str( value ) + quotation

            count += 1
            if count < len( tableValue ):
                fields += ','
                values += ','

        #print( 'fields:', fields, '/values:', values )

        sql = InsertMode + " INTO " + table + " ( " + fields + " ) VALUES ( " + values + " )"
        #print( '[insert/ReplaceData] sql:', sql )

        #print( 'sql.encode():', sql.encode() )
        cursor.execute( sql.encode() )
        db.commit()

        result = True

    except mdb.Error as e:
        # except mysql.connector.errors.ProgrammingError as err:
        print( 'Insert/Replace Error: %d, %s' % ( e.args[0], e.args[1] ) )
        db.rollback()


    except FileNotFoundError as e:
        print( 'Error occured in insert: ', e )
        db.rollback()


    finally:
        # print('finally close')
        if db:
            db.close()

    return result


def replaceData( table, tableValue, dbName=DB_Name ):
# Table에 새로운 데이타{ 'field': value }를 대치한다.
    #print( '[replaceData] table:', table, '/tableValue:', tableValue )

    return insertData( table, tableValue, dbName=DB_Name, InsertMode="REPLACE" )


def updateData( table, where, tableValue, dbName=DB_Name ):
# Table로부터 조건(where)에 맞는 데이타를 업데이트한다.
    #print( '[updateData] table:', table, '/where:', where, '/tableValue:', tableValue )

    result = False

    try:
        # Open database connection
        db = mdb.connect(
            host = Host_Name,           # MySQL 서버 호스트
            user = User_Name,           # MySQL 사용자 이름
            password = Pass_Word,       # MySQL 암호
            database = DB_Name          # 연결할 데이터베이스
        )

        #cursor = db.cursor( mdb.cursors.DictCursor )
        cursor = db.cursor()

        setValue = ''
        count = 0

        for field, value in tableValue.items():
            count += 1
            setValue += field + "= '" + str(value) + "'" + ( ',' if count < len(tableValue) else '' )

        #print( '[updateData] setValue:', setValue )

        sql = 'UPDATE ' + table + ' SET ' + setValue + ' WHERE ' + where
        print( '[updateData] sql:', sql )

        #print( 'sql.encode():', sql.encode() )
        cursor.execute( sql.encode() )
        db.commit()

        result = True

    except mdb.Error as e:
        # except mysql.connector.errors.ProgrammingError as err:
        db.rollback()
        print( 'Update Error: %d, %s' % ( e.args[0], e.args[1] ) )
        #sys.exit(1)

    except FileNotFoundError as e:
        print( 'Error occured in update: ', e )

    finally:
        #print('finally close')
        if db:
            db.close()

    return result


def deleteData( table, where, dbName=DB_Name ):
# Table로부터 조건(where)에 맞는 데이타를 삭제한다.
    #print('[deleteData] table:', table, '/where:', where )

    result = False

    try:
        # Open database connection
        db = mdb.connect(
            host = Host_Name,           # MySQL 서버 호스트
            user = User_Name,           # MySQL 사용자 이름
            password = Pass_Word,       # MySQL 암호
            database = DB_Name          # 연결할 데이터베이스
        )

        #cursor = db.cursor( mdb.cursors.DictCursor )
        cursor = db.cursor()

        sql = 'DELETE FROM ' + table + ' WHERE ' + where
        #print( '[deleteData] sql:', sql )

        # print( 'sql.encode():', sql.encode() )
        cursor.execute(sql.encode())
        db.commit()

        result = True

    except mdb.Error as e:
        # except mysql.connector.errors.ProgrammingError as err:
        db.rollback()
        print( 'Delete Error: %d, %s' % ( e.args[0], e.args[1] ) )
        #sys.exit(1)

    except FileNotFoundError as e:
        print( 'Error occured in delete: ', e )

    finally:
        # print('finally close')
        if db:
            db.close()

    return result


def getQuotation( value ):
# value가 숫자인 경우에만 따옴표를 붙이지 않는다.
    return( "" if ( type(value) is int ) else "'" )

def getStr2Int( str ):
# str이 문자형인 경우 숫자로 되돌려 준다, 빈공백은 0으로
    return int(str) if ( str.isdigit() ) else 0

def afterPost( str ):
# post한 str내에서 ampersand(/@)를 &로 바꾼다.
    return str.replace( SIGN_AMPERSAND, '&' ).replace( SIGN_SHARP, '#' )
