# coding:utf-8
import requests,re,sys,datetime,urllib2
from bs4 import BeautifulSoup
from slacker import slacker

yoyakulist = {}
USERAGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36'
OUT_PATH = '/var/www/homeserver/pg/driving/'
CAR_TYPE = sys.argv[1]
login_headers = {'user-agent': USERAGENT}
s = requests.Session()
r = s.get('http://pic.ncors.com/ncors/login.asp', headers=login_headers)

soup = BeautifulSoup(r.text, "lxml")
if r.status_code == 200 and soup.find('title').string != 'Service is not ready.':
  cookie_soup = soup.find(attrs={'name':'COOKIE'}).get('value')
  payload = {
      'USERID': '637216A04046',
      'USERPASSWD': '578062078305',
      'COOKIE': cookie_soup
  }

  driving_login = s.post('http://pic.ncors.com/ncors/cartype.asp', data=payload, headers=login_headers)
  driving_login.encoding = 'Shift_JIS'
  #print isinstance(driving_login.text, unicode)
  #print isinstance(driving_login.text.encode('utf-8'), str)
  driving_text = BeautifulSoup(driving_login.text, "lxml")
  #driving_text = BeautifulSoup(driving_login.text.encode('utf-8'), "lxml")
  userinfo_cookie = driving_text.find(attrs={'name':'COOKIE'}).get('value')
  userinfo_username = driving_text.find(attrs={'name':'USERNAME'}).get('value')
  userinfo_step = driving_text.find(attrs={'name':'USERSTEP'}).get('value')
  userinfo_data = driving_text.find(attrs={'name':'USERDATA'}).get('value')
  #print userinfo_username+userinfo_step+userinfo_data.encode('utf-8')
  payload2 = {
      'CARTYPE':CAR_TYPE,
      'USERNAME':userinfo_username,
      'USERSTEP':userinfo_step,
      'USERDATA':userinfo_data,
      'COOKIE': userinfo_cookie
      }
  car_select = s.post('http://pic.ncors.com/ncors/ReserveList.asp', data=payload2, headers=login_headers)
  car_select.encoding = 'Shift_JIS'
  #print urllib2.quote("&".join(unicode(k)+'='+unicode(v)  for k, v in payload2.items()).encode('utf-8'))
  #print "&".join(unicode(k)+'='+unicode(v)  for k, v in payload2.items()).encode('utf-8')
  reserver = BeautifulSoup(car_select.text, "lxml")
  #reserver = BeautifulSoup(open('ReserverList01.asp','r'), "lxml")
  reserverlist = reserver.find(attrs={'class':'Reservation'}).findAll('td',id=re.compile('[A-Z][A-Z][0-9][0-9][0-9][0-9]'))
  reserverhead = reserver.find(attrs={'class':'Reservation'}).findAll('td', 'Head')
  timelist = reserver.find(attrs={'class':'Reservation'}).findAll('th')
  R_DATE = reserver.find(attrs={'name':'R_DATE'}).findAll('option')
  PERIOD = reserver.find(attrs={'name':'PERIOD'}).findAll('option')
  #print reserverlist[0].string
  del timelist[0]
  #print  reserverhead[int(reserverlist[0]['id'][3])].string + timelist[int(reserverlist[0]['id'][4-5])].string
  #print unicode(reserverhead[int('ID0510'[3])].string)[:5]
  for Reser in reserverlist:
    rser = datetime.datetime.strptime(str(datetime.date.today().year)+'-'+ str(unicode(reserverhead[int(Reser['id'][3])].string)[:5]), '%Y-%m/%d')
    #rser = str(datetime.datetime.today().year)+'-'+ str(unicode(reserverhead[int(Reser['id'][3])].string)[:5]) +'-'+timelist[int(Reser['id'][4-5])].string[:1]
    yoyakulist[Reser['id']] = datetime.date(rser.year, rser.month, rser.day)

  f = open(OUT_PATH+'slack_liston.txt','r+')
  slack_list = []
  for slack_lists in f:
    #tyouhuku = datetime.date.strftime(slack_lists.strip(), '%Y-%m-%d')
    tyouhuku = datetime.datetime.strptime(slack_lists.strip(), '%Y/%m/%d')
    slack_list.append(datetime.date(tyouhuku.year, tyouhuku.month, tyouhuku.day))

  freecheck = reserver.find(attrs={'class':'Reservation'}).findAll('td', class_='Free')
  #print car_select.text
  for freechecker in freecheck:
    yoyakubi = yoyakulist[freechecker['id']]
    if  not 2 < int(freechecker['id'][4-5]) < 7:
      print u'時間外です'
    elif  slack_list.count(yoyakubi) >= 2:
      print u'予約回数を超えています'
    elif yoyakubi.weekday() <= 3 :
      confirm_rdate = R_DATE[int(freechecker['id'][3])].get('value')
      confirm_period = PERIOD[int(freechecker['id'][4-5])].get('value')
      confirm_cancelflg = 0 #予約0,キャンセル1
      confirm_cartype = CAR_TYPE #01実車,02模擬,04無線,07AT,93応急
      confirm_cookie = reserver.find(attrs={'name':'COOKIE'}).get('value')
      confirm_username = reserver.find(attrs={'name':'USERNAME'}).get('value')
      confirm_step = reserver.find(attrs={'name':'USERSTEP'}).get('value')
      confirm_data = reserver.find(attrs={'name':'USERDATA'}).get('value')
      confirm_instructor = reserver.find(attrs={'name':'INSTRUCTOR'}).get('value')
      confirm_lastinfo = reserver.find(attrs={'name':'LASTINFO'}).get('value')
      yoyaku_url = u'http://pic.ncors.com/ncors/confirm.asp?'
      payload3 = {
        'R_DATE':confirm_rdate,
        'PERIOD':confirm_period,
        'CARTYPE':CAR_TYPE,
        'CANCELFLG':confirm_cancelflg,
        'USERNAME':confirm_username,
        'USERSTEP':confirm_step,
        'USERDATA':confirm_data,
        'INSTRUCTOR':confirm_data,
        'COOKIE':confirm_cookie,
        'LASTINFO':confirm_lastinfo
          }
      if datetime.date.today() == yoyakubi or (datetime.date.today() + datetime.timedelta(days=1) == yoyakubi) and (18 < datetime.datetime.now().hour < 24):
        print u'当日です'
        yoyaku_url += urllib2.quote("&".join(unicode(k)+'='+unicode(v)  for k, v in payload3.items()).encode('utf-8'))
        slacker(yoyakulist[str(freechecker['id'])].strftime('%Y/%m/%d')+' '+timelist[int(freechecker['id'][4-5])].string+u'に空あり <'+yoyaku_url+u'|■予約■>')
      else:
        #confirm = s.post('http://pic.ncors.com/ncors/confirm.asp', data=payload3, headers=login_headers)
        slacker(yoyakulist[str(freechecker['id'])].strftime('%Y/%m/%d')+' '+timelist[int(freechecker['id'][4-5])].string+u'に予約が出来ました ')
        slack_list.append(yoyakubi)
        print u'予約完了'
    else:
      print u'金〜日曜日です'


  f.seek(0)
  f.write("\n".join([x.strftime('%Y/%m/%d') for x in slack_list]))
  f.truncate()
  f.close()



  #confirm = s.post('http://pic.ncors.com/ncors/confirm.asp', data=payload3, headers=login_headers)

