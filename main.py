import os
import time
import json
import threading
import requests
import datetime
from typing import Any,Dict,List,Optional,Tuple
from decimal import Decimal,getcontext,ROUND_DOWN
getcontext().prec=40
def load_dotenv(path='.env'):
	if not os.path.exists(path):return
	with open(path,'r',encoding='utf-8')as f:
		for ln in f:
			ln=ln.strip()
			if not ln or ln.startswith('#')or'='not in ln:continue
			k,v=ln.split('=',1);k=k.strip();v=v.strip().strip('"').strip("'")
			if k not in os.environ:os.environ[k]=v
load_dotenv('.env')
DISCORD_WEBHOOK=os.getenv('DISCORD_WEBHOOK','').strip()
POLL_INTERVAL=float(os.getenv('POLL_INTERVAL','8'))
LIMIT=int(os.getenv('LIMIT','100'))
COIN_FILTER=os.getenv('COIN_FILTER','').strip().upper()
MIN_USD=Decimal(os.getenv('MIN_USD','0')or'0')
COOKIE_STR=os.getenv('RUGPLAY_COOKIE','').strip()
if not COOKIE_STR and os.path.exists('cookie.txt'):
	with open('cookie.txt','r',encoding='utf-8')as f:COOKIE_STR=f.read().strip()
API_URL=os.getenv('API_URL','https://rugplay.com/api/trades/recent')
RUGPLAY_BASE=os.getenv('RUGPLAY_BASE','https://rugplay.com')
WEBSOCKET_URL=os.getenv('WEBSOCKET_URL','wss://ws.rugplay.com/')
WEBSOCKET_USERID=os.getenv('WEBSOCKET_USERID','8351')
WEBSOCKET_COIN=os.getenv('WEBSOCKET_COIN','@global')
AUTO_SUBSCRIBE=os.getenv('AUTO_SUBSCRIBE','true').lower()in('1','true','yes')
session=requests.Session()
session.headers.update({'accept':'*/*','accept-language':'pt-BR','referer':f"{RUGPLAY_BASE.rstrip("/")}/live",'user-agent':'RugPlayMonitor/1.0'})
if COOKIE_STR:
	for item in[c.strip()for c in COOKIE_STR.split(';')if c.strip()]:
		if'='in item:k,v=item.split('=',1);session.cookies.set(k.strip(),v.strip())
def to_decimal_safe(x):
	if x is None:return None
	try:return Decimal(str(x))
	except Exception:
		try:return Decimal(x)
		except Exception:return None
def format_decimal(d,max_places=12):
	if d is None:return'N/A'
	try:
		d=+d
		if d==0:return'0'
		ab=abs(d)
		if ab>=Decimal('0.01'):q=Decimal('1e-6')
		elif ab>=Decimal('1e-6'):q=Decimal('1e-9')
		else:q=Decimal(1).scaleb(-max_places)
		quant=d.quantize(q,rounding=ROUND_DOWN);s=format(quant.normalize(),'f')
		if s in('-0','+0'):return'0'
		if'.'in s:s=s.rstrip('0').rstrip('.')
		return s
	except Exception:
		try:s=f"{float(d):.{max_places}f}";s=s.rstrip('0').rstrip('.');return s or'0'
		except Exception:return str(d)
def format_price_for_display(raw_price):dec=to_decimal_safe(raw_price);return format_decimal(dec,max_places=12)
def format_amount_for_display(raw_amount):
	dec=to_decimal_safe(raw_amount)
	if dec is None:return'N/A'
	if abs(dec)>=Decimal('1'):return format_decimal(dec,max_places=6)
	return format_decimal(dec,max_places=12)
def format_usd_currency(dec):
	if dec is None:return'N/A'
	try:
		q=dec.quantize(Decimal('0.01'),rounding=ROUND_DOWN);sign='-'if q<0 else'';q=abs(q);s=format(q,'f')
		if'.'in s:int_part,frac=s.split('.',1)
		else:int_part,frac=s,'00'
		try:int_with_commas='{:,}'.format(int(int_part))
		except Exception:int_with_commas=int_part
		frac=(frac+'00')[:2];return f"{sign}${int_with_commas}.{frac}"
	except Exception:return f"${str(dec)}"
def safe_get(item,keys,default=None):
	for k in keys:
		if k in item and item[k]is not None:return item[k]
	return default
def normalize_ts(ts):
	if ts is None:return 0
	try:
		if isinstance(ts,(int,float)):t=int(ts)
		else:
			s=str(ts).strip()
			if s.isdigit():t=int(s)
			else:
				try:dt=datetime.datetime.fromisoformat(s.replace('Z','+00:00'));return int(dt.timestamp()*1000)
				except Exception:return 0
		if t>10**12:return t
		if t>10**9:return t*1000
		return t
	except Exception:return 0
def parse_response_json(r_text):
	try:data=json.loads(r_text)
	except Exception:return[]
	if isinstance(data,dict):
		if'trades'in data and isinstance(data['trades'],list):return data['trades']
		if'data'in data and isinstance(data['data'],list):return data['data']
		for v in data.values():
			if isinstance(v,list):return v
		return[]
	elif isinstance(data,list):return data
	return[]
def detect_side(item):
	side_raw=safe_get(item,['type','side','action'],'')
	if isinstance(side_raw,str):
		s=side_raw.strip().upper()
		if'BUY'in s:return'buy'
		if'SELL'in s:return'sell'
		if s in('B','S'):return'buy'if s=='B'else'sell'
	if'is_buy'in item:
		try:return'buy'if bool(item.get('is_buy'))else'sell'
		except Exception:pass
	if'isSell'in item:
		try:return'sell'if bool(item.get('isSell'))else'buy'
		except Exception:pass
	return'unknown'
def build_embed_from_item(item,buy_count,sell_count):
	side=detect_side(item);symbol=safe_get(item,['coinSymbol','symbol','coin','pair'],'UNKNOWN');coin_name=safe_get(item,['coinName','name'],'');username=safe_get(item,['username','user','userName'],'');user_id=safe_get(item,['userId','user_id','id'],'');raw_amount=safe_get(item,['amount','qty','quantity'],None);raw_price=safe_get(item,['price','priceUsd','price_usd'],None);raw_usd=safe_get(item,['totalValue','total_value','valueUsd','usd','total'],None);ts_raw=safe_get(item,['timestamp','time','createdAt'],None);ts_ms=normalize_ts(ts_raw);amount_display=format_amount_for_display(raw_amount);price_display=format_price_for_display(raw_price);usd_dec=to_decimal_safe(raw_usd)
	if usd_dec is None:
		dec_price=to_decimal_safe(raw_price);dec_amount=to_decimal_safe(raw_amount)
		if dec_price is not None and dec_amount is not None:
			try:usd_dec=dec_price*dec_amount
			except Exception:usd_dec=None
	usd_text=format_usd_currency(usd_dec);coin_icon=safe_get(item,['coinIcon'],'');thumbnail_url=None
	if coin_icon:
		if isinstance(coin_icon,str)and(coin_icon.startswith('http://')or coin_icon.startswith('https://')):thumbnail_url=coin_icon
		else:thumbnail_url=f"{RUGPLAY_BASE.rstrip("/")}/{str(coin_icon).lstrip("/")}"
	user_image=safe_get(item,['userImage','avatar','userImg'],'');author_icon=None
	if user_image:
		if isinstance(user_image,str)and(user_image.startswith('http://')or user_image.startswith('https://')):author_icon=user_image
		else:author_icon=f"{RUGPLAY_BASE.rstrip("/")}/{str(user_image).lstrip("/")}"
	COLOR_BUY=65416;COLOR_SELL=16729156;COLOR_UNKNOWN=10181046;color=COLOR_BUY if side=='buy'else COLOR_SELL if side=='sell'else COLOR_UNKNOWN
	if side=='buy':emoji='🚀';action_text='BOUGHT';bar='━━━━━━━━━━━━━━━━';indicator='📈'
	elif side=='sell':emoji='💎';action_text='SOLD';bar='━━━━━━━━━━━━━━━━';indicator='📉'
	else:emoji='🔔';action_text='TRADED';bar='━━━━━━━━━━━━━━━━';indicator='📊'
	title=f"{emoji} **{symbol}** {action_text} {emoji}";description=f"```ansi\n[1;37m{bar}[0m\n```\n";description+=f"{indicator} **Transaction Value:** {usd_text}\n";fields=[]
	if amount_display!='N/A':fields.append({'name':'💰 Amount','value':f"```fix\n{amount_display}\n```",'inline':True})
	if price_display!='N/A':fields.append({'name':'💵 Price (USD)','value':f"```fix\n{price_display}\n```",'inline':True})
	fields.append({'name':'💸 Total Value','value':f"```diff\n+ {usd_text}\n```",'inline':True});fields.append({'name':'\u200b','value':'```\n▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n```','inline':False})
	if coin_name:fields.append({'name':'🪙 Token Name','value':f"`{coin_name}`",'inline':False})
	if username or user_id:usr=username if username else'Anonymous';uid_text=f"\n*ID: `{user_id}`*"if user_id else'';fields.append({'name':'👤 Trader','value':f"**{usr}**{uid_text}",'inline':True})
	tx=safe_get(item,['txHash','hash','transaction'],None);wallet=safe_get(item,['address','wallet','from','to'],None)
	if wallet:wallet_short=f"{str(wallet)[:6]}...{str(wallet)[-4:]}"if len(str(wallet))>12 else str(wallet);fields.append({'name':'🔑 Wallet','value':f"`{wallet_short}`",'inline':True})
	if tx:tx_short=f"{str(tx)[:6]}...{str(tx)[-4:]}"if len(str(tx))>12 else str(tx);fields.append({'name':'🔗 Transaction','value':f"`{tx_short}`",'inline':True})
	fields.append({'name':'\u200b','value':'```\n▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n```','inline':False});total_trades=buy_count+sell_count;buy_percentage=buy_count/total_trades*100 if total_trades>0 else 0;sell_percentage=sell_count/total_trades*100 if total_trades>0 else 0;stats_value=f"```ml\n";stats_value+=f"🚀 Buys:  {buy_count:>4} ({buy_percentage:.1f}%)\n";stats_value+=f"💎 Sells: {sell_count:>4} ({sell_percentage:.1f}%)\n";stats_value+=f"━━━━━━━━━━━━━━━━━━━\n";stats_value+=f"📊 Total: {total_trades:>4} trades\n";stats_value+=f"```";fields.append({'name':'📈 Session Statistics','value':stats_value,'inline':False});embed={'title':title,'description':description,'color':color,'fields':fields,'timestamp':ts_to_iso(ts_ms)}
	if thumbnail_url:embed['thumbnail']={'url':thumbnail_url}
	if author_icon or username:author_name=f"💼 {username or"Trader"}";embed['author']={'name':author_name,'icon_url':author_icon if author_icon else None}
	embed['footer']={'text':f"RugPlay Live • {symbol}",'icon_url':f"{RUGPLAY_BASE.rstrip("/")}/favicon.ico"};return embed,ts_ms
def send_discord_embed(embed):
	if not DISCORD_WEBHOOK:print('DISCORD_WEBHOOK not set - preview embed:');print(json.dumps(embed,indent=2,ensure_ascii=False)[:1000]);return
	payload={'username':'🎯 RugPlay Monitor','avatar_url':f"{RUGPLAY_BASE.rstrip("/")}/favicon.ico",'embeds':[embed]}
	try:
		r=requests.post(DISCORD_WEBHOOK,json=payload,timeout=10)
		if r.status_code not in(200,204):print('Discord webhook failed:',r.status_code,r.text[:300])
	except Exception as e:print('Error sending webhook:',e)
lock=threading.Lock()
buy_count=0
sell_count=0
last_seen=int(time.time()*1000)
def process_trade(item):
	global buy_count,sell_count,last_seen;ts=normalize_ts(safe_get(item,['timestamp','time','createdAt'],None))
	with lock:
		if ts<=last_seen:return
		symbol=(safe_get(item,['coinSymbol','symbol'],'')or'').upper();usd_dec=to_decimal_safe(safe_get(item,['totalValue','total_value','valueUsd','usd','total'],None))
		if COIN_FILTER and symbol and COIN_FILTER!=symbol:last_seen=max(last_seen,ts);return
		if MIN_USD and(usd_dec is None or usd_dec<MIN_USD):last_seen=max(last_seen,ts);return
		side=detect_side(item)
		if side=='buy':buy_count+=1
		elif side=='sell':sell_count+=1
		embed,ts_ms=build_embed_from_item(item,buy_count,sell_count);send_discord_embed(embed);action_emoji='🚀'if side=='buy'else'💎'if side=='sell'else'🔔';print(f"{action_emoji} Notified: {symbol or"UNKNOWN"} @ {ts_ms}  (B:{buy_count}, S:{sell_count})");last_seen=max(last_seen,ts_ms)
def start_websocket_client():
	try:from websocket import WebSocketApp
	except Exception:print('websocket-client is required for WebSocket mode. Install with: pip install websocket-client');return
	headers=[];headers.append(f"Origin: {RUGPLAY_BASE.rstrip("/")}");headers.append(f"User-Agent: {session.headers.get("user-agent")}")
	if COOKIE_STR:headers.append(f"Cookie: {COOKIE_STR}")
	def on_message(ws,message):
		try:payload=json.loads(message)
		except Exception:return
		if isinstance(payload,dict)and payload.get('type')=='ping':
			try:ws.send(json.dumps({'type':'pong'}))
			except Exception:pass
			return
		if isinstance(payload,dict)and payload.get('type')in('all-trades','trade','trade:update'):data=payload.get('data')if isinstance(payload.get('data'),dict)else payload;process_trade(data);return
		trades=[]
		if isinstance(payload,dict):
			if'trades'in payload and isinstance(payload['trades'],list):trades=payload['trades']
			elif'data'in payload and isinstance(payload['data'],list):trades=payload['data']
			elif'data'in payload and isinstance(payload['data'],dict)and payload.get('type')in('all-trades','trade'):process_trade(payload['data']);return
		elif isinstance(payload,list):trades=payload
		for t in trades:
			if isinstance(t,dict):process_trade(t)
	def on_open(ws):
		print('WebSocket connected; sending init messages...')
		try:
			ws.send(json.dumps({'type':'set_user','userId':WEBSOCKET_USERID}));ws.send(json.dumps({'type':'set_coin','coinSymbol':WEBSOCKET_COIN}))
			if AUTO_SUBSCRIBE:ws.send(json.dumps({'type':'subscribe','channel':'trades:all'}))
		except Exception as e:print('Error sending init messages:',e)
	def on_close(ws,close_status_code,close_msg):print('WebSocket closed.',close_status_code,close_msg)
	def on_error(ws,error):print('WebSocket error:',error)
	backoff=1
	while True:
		try:print(f"Connecting to WebSocket: {WEBSOCKET_URL}");ws=WebSocketApp(WEBSOCKET_URL,on_message=on_message,on_open=on_open,on_close=on_close,on_error=on_error,header=headers if headers else None);ws.run_forever(ping_interval=20,ping_timeout=10)
		except Exception as e:print('WebSocket client exception:',e)
		print(f"Reconnecting in {backoff}s...");time.sleep(backoff);backoff=min(backoff*2,60)
def fetch_trades_http(limit=LIMIT):
	params={'limit':limit}
	try:r=session.get(API_URL,params=params,timeout=15)
	except Exception as e:print('Request error:',e);return[]
	if r.status_code!=200:print(f"Bad status {r.status_code} from trades endpoint. Preview: {r.text[:300]}");return[]
	return parse_response_json(r.text)
def start_http_poller():
	global last_seen;print('Starting HTTP poller.')
	while True:
		trades=fetch_trades_http(LIMIT)
		if not trades:print('⏳ No trades returned from endpoint.');time.sleep(POLL_INTERVAL);continue
		new_items=[]
		for t in trades:
			if not isinstance(t,dict):continue
			ts=normalize_ts(safe_get(t,['timestamp','time','createdAt'],None))
			if ts>last_seen:new_items.append((ts,t))
		if new_items:
			new_items.sort(key=lambda x:x[0])
			for(ts,item)in new_items:process_trade(item)
		else:print('💤 No new trades.')
		time.sleep(POLL_INTERVAL)
def main():
	print('RugPlay real-time monitor starting.');global last_seen;last_seen=int(time.time()*1000)
	if WEBSOCKET_URL:start_websocket_client()
	else:print('Starting HTTP poller.');start_http_poller()
if __name__=='__main__':main()
