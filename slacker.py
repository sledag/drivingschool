#coding: utf-8

import requests

def slacker(stext):
  """slackへ投稿する関数です"""
  url = "https://slack.com/api/chat.postMessage"

  params = {'token':'tokennumber','channel':'G10TVETNW','text': stext,'username':'Server_bot'}
  #params['text'] = 'hellow!'
  headers = {'Content-Type': 'application/x-www-form-urlencoded'}
  r = requests.get(url, params=params,headers=headers)
  #print r.text

