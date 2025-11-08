A2='createdAt'
A1='valueUsd'
A0='total_value'
z='totalValue'
y='username'
x='symbol'
w='coinSymbol'
v='0.01'
u='cookie.txt'
t='utf-8'
s='.env'
r=format
g='timestamp'
e='Z'
d=max
c=dict
b=abs
a=float
U='='
R=list
T=False
P='.'
S='N/A'
N=True
M='sell'
K='0'
J=int
L='buy'
I=print
G=isinstance
E=''
C=Exception
B=str
A=None
import os as F,time as V,json as W,requests as h,datetime as X
from typing import Any,Dict,List,Optional,Tuple
from decimal import Decimal as H,getcontext as A3,ROUND_DOWN as i
A3().prec=40
def A4(path=s):
	if not F.path.exists(path):return
	with open(path,'r',encoding=t)as D:
		for A in D:
			A=A.strip()
			if not A or A.startswith('#')or U not in A:continue
			B,C=A.split(U,1);B=B.strip();C=C.strip().strip('"').strip("'")
			if B not in F.environ:F.environ[B]=C
A4(s)
j=F.getenv('DISCORD_WEBHOOK',E).strip()
k=a(F.getenv('POLL_INTERVAL','8'))
l=J(F.getenv('LIMIT','100'))
m=F.getenv('COIN_FILTER',E).strip().upper()
n=H(F.getenv('MIN_USD',K)or K)
Q=F.getenv('RUGPLAY_COOKIE',E).strip()
if not Q and F.path.exists(u):
	with open(u,'r',encoding=t)as A5:Q=A5.read().strip()
A6='https://rugplay.com/api/trades/recent'
f='https://rugplay.com'
Y=h.Session()
Y.headers.update({'accept':'*/*','accept-language':'pt-BR','referer':'https://rugplay.com/live','sec-ch-ua':'"Chromium";v="127", "Not)A;Brand";v="99", "Microsoft Edge Simulate";v="127", "Lemur";v="127"','sec-ch-ua-mobile':'?0','sec-ch-ua-platform':'"Android"','sec-fetch-dest':'empty','sec-fetch-mode':'cors','sec-fetch-site':'same-origin','user-agent':'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'})
if Q:
	for o in[A.strip()for A in Q.split(';')if A.strip()]:
		if U in o:A7,A8=o.split(U,1);Y.cookies.set(A7.strip(),A8.strip())
def O(x):
	if x is A:return
	try:return H(B(x))
	except C:
		try:return H(x)
		except C:return
def Z(d,max_places=12):
	I='1e-6';F=max_places
	if d is A:return S
	try:
		d=+d
		if d==0:return K
		G=b(d)
		if G>=H(v):E=H(I)
		elif G>=H(I):E=H('1e-9')
		else:E=H(1).scaleb(-F)
		J=d.quantize(E,rounding=i);D=r(J.normalize(),'f')
		if D in('-0','+0'):return K
		if P in D:D=D.rstrip(K).rstrip(P)
		return D
	except C:
		try:D=f"{a(d):.{F}f}";D=D.rstrip(K).rstrip(P);return D or K
		except C:return B(d)
def AD(raw_price):A=O(raw_price);return Z(A,max_places=12)
def AE(raw_amount):
	B=O(raw_amount)
	if B is A:return S
	if b(B)>=H('1'):return Z(B,max_places=6)
	return Z(B,max_places=12)
def AF(dec):
	G=dec
	if G is A:return S
	try:
		D=G.quantize(H(v),rounding=i);M='-'if D<0 else E;D=b(D);I=r(D,'f')
		if P in I:K,F=I.split(P,1)
		else:K,F=I,'00'
		try:L='{:,}'.format(J(K))
		except C:L=K
		F=(F+'00')[:2];return f"{M}${L}.{F}"
	except C:return f"${B(G)}"
def D(item,keys,default=A):
	B=item
	for C in keys:
		if C in B and B[C]is not A:return B[C]
	return default
def p(ts):
	if ts is A:return 0
	try:
		if G(ts,(J,a)):D=J(ts)
		else:
			E=B(ts).strip()
			if E.isdigit():D=J(E)
			else:
				try:F=X.datetime.fromisoformat(E.replace(e,'+00:00'));return J(F.timestamp()*1000)
				except C:return 0
		if D>10**12:return D
		if D>10**9:return D*1000
		return D
	except C:return 0
def A9(r):
	D='data';B='trades'
	try:A=r.json()
	except C:
		try:A=W.loads(r.text)
		except C:return[]
	if G(A,c):
		if B in A and G(A[B],R):return A[B]
		if D in A and G(A[D],R):return A[D]
		for E in A.values():
			if G(E,R):return E
		return[]
	elif G(A,R):return A
	return[]
def AA(limit=l):
	F={'limit':limit}
	try:A=Y.get(A6,params=F,timeout=15)
	except C as H:I('Request error:',H);return[]
	if A.status_code!=200:I(f"Bad status {A.status_code} from trades endpoint. Preview: {A.text[:300]}");return[]
	J=A9(A);E=[]
	for D in J:
		if G(D,c):E.append(D)
		elif G(D,B):
			try:E.append(W.loads(D))
			except C:continue
	return E
def AG(ms_ts):
	try:return X.datetime.utcfromtimestamp(ms_ts/1e3).isoformat()+e
	except C:return X.datetime.utcnow().isoformat()+e
def q(item):
	J='isSell';I='is_buy';A=item;H=D(A,['type','side','action'],E)
	if G(H,B):
		F=H.strip().upper()
		if'BUY'in F:return L
		if'SELL'in F:return M
		if F in('B','S'):return L if F=='B'else M
	if I in A:
		try:return L if bool(A.get(I))else M
		except C:pass
	if J in A:
		try:return M if bool(A.get(J))else L
		except C:pass
	return'unknown'
def AB(item,buy_count,sell_count):
	AC='icon_url';AB='```\n▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n```';AA='\u200b';A9='https://';A8='http://';n='━━━━━━━━━━━━━━━━';i=sell_count;h=buy_count;Z='/';K='inline';J='value';H='name';F=item;a=q(F);o=D(F,[w,x,'coin','pair'],'UNKNOWN');r=D(F,['coinName',H],E);U=D(F,[y,'user','userName'],E);j=D(F,['userId','user_id','id'],E);s=D(F,['amount','qty','quantity'],A);t=D(F,['price','priceUsd','price_usd'],A);AH=D(F,[z,A0,A1,'usd','total'],A);AI=D(F,[g,'time',A2],A);u=p(AI);v=AE(s);A3=AD(t);b=O(AH)
	if b is A:
		A4=O(t);A5=O(s)
		if A4 is not A and A5 is not A:
			try:b=A4*A5
			except C:b=A
	A6=AF(b);P=D(F,['coinIcon'],E);c=A
	if P:
		if G(P,B)and(P.startswith(A8)or P.startswith(A9)):c=P
		else:c=f"{f.rstrip(Z)}/{B(P).lstrip(Z)}"
	Q=D(F,['userImage','avatar','userImg'],E);V=A
	if Q:
		if G(Q,B)and(Q.startswith(A8)or Q.startswith(A9)):V=Q
		else:V=f"{f.rstrip(Z)}/{B(Q).lstrip(Z)}"
	AJ=65416;AK=16729156;AL=10181046;AM=AJ if a==L else AK if a==M else AL
	if a==L:d='🚀';k='BOUGHT';l=n;m='📈'
	elif a==M:d='💎';k='SOLD';l=n;m='📉'
	else:d='🔔';k='TRADED';l=n;m='📊'
	AN=f"{d} **{o}** {k} {d}";A7=f"```ansi\n[1;37m{l}[0m\n```\n";A7+=f"{m} **Transaction Value:** {A6}\n";I=[]
	if v!=S:I.append({H:'💰 Amount',J:f"```fix\n{v}\n```",K:N})
	if A3!=S:I.append({H:'💵 Price (USD)',J:f"```fix\n{A3}\n```",K:N})
	I.append({H:'💸 Total Value',J:f"```diff\n+ {A6}\n```",K:N});I.append({H:AA,J:AB,K:T})
	if r:I.append({H:'🪙 Token Name',J:f"`{r}`",K:T})
	if U or j:AO=U if U else'Anonymous';AP=f"\n*ID: `{j}`*"if j else E;I.append({H:'👤 Trader',J:f"**{AO}**{AP}",K:N})
	W=D(F,['txHash','hash','transaction'],A);X=D(F,['address','wallet','from','to'],A)
	if X:AQ=f"{B(X)[:6]}...{B(X)[-4:]}"if len(B(X))>12 else B(X);I.append({H:'🔑 Wallet',J:f"`{AQ}`",K:N})
	if W:AR=f"{B(W)[:6]}...{B(W)[-4:]}"if len(B(W))>12 else B(W);I.append({H:'🔗 Transaction',J:f"`{AR}`",K:N})
	I.append({H:AA,J:AB,K:T});Y=h+i;AS=h/Y*100 if Y>0 else 0;AT=i/Y*100 if Y>0 else 0;R=f"```ml\n";R+=f"🚀 Buys:  {h:>4} ({AS:.1f}%)\n";R+=f"💎 Sells: {i:>4} ({AT:.1f}%)\n";R+=f"━━━━━━━━━━━━━━━━━━━\n";R+=f"📊 Total: {Y:>4} trades\n";R+=f"```";I.append({H:'📈 Session Statistics',J:R,K:T});e={'title':AN,'description':A7,'color':AM,'fields':I,g:AG(u)}
	if c:e['thumbnail']={'url':c}
	if V or U:AU=f"💼 {U or"Trader"}";e['author']={H:AU,AC:V if V else A}
	e['footer']={'text':f"RugPlay Live • {o}",AC:f"{f.rstrip(Z)}/favicon.ico"};return e,u
def AC(embed):
	B=embed
	if not j:I('DISCORD_WEBHOOK not set - preview embed:');I(W.dumps(B,indent=2,ensure_ascii=T)[:1000]);return
	D={y:'🎯 RugPlay Monitor','avatar_url':'https://rugplay.com/favicon.ico','embeds':[B]}
	try:
		A=h.post(j,json=D,timeout=10)
		if A.status_code not in(200,204):I('Discord webhook failed:',A.status_code,A.text[:300])
	except C as E:I('Error sending webhook:',E)
def AH():
	T=J(V.time()*1000);B=T;I(f"🚀 Notifier started at {T} ms. Ignoring prior trades.");K=0;P=0
	while N:
		U=AA(l)
		if not U:I('⏳ No trades returned from endpoint.');V.sleep(k);continue
		F=[]
		for Q in U:
			if not G(Q,c):continue
			C=p(D(Q,[g,'time',A2],A))
			if C>B:F.append((C,Q))
		if F:
			F.sort(key=lambda x:x[0])
			for(C,H)in F:
				R=(D(H,[w,x],E)or E).upper();W=O(D(H,[z,A0,A1,'usd','total'],A))
				if m and R and m!=R:B=d(B,C);continue
				if n and(W is A or W<n):B=d(B,C);continue
				S=q(H)
				if S==L:K+=1
				elif S==M:P+=1
				Y,X=AB(H,K,P);AC(Y);Z='🚀'if S==L else'💎';I(f"{Z} Notified: {R} @ {X}  (B:{K}, S:{P})");B=d(B,X)
		else:I('💤 No new trades.')
		V.sleep(k)
if __name__=='__main__':AH()
