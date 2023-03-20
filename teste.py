"noDZy9bG2RkUAqPOWcQLwtFYh0nkaYSIG4NnA6KTl0cQVfVSu0oK66MNuMS3kqaU"
['SOLUSDTPERP', 'BTCUSDTPERP', 'ETHUSDTPERP', 'ADAUSDTPERP', 'FTMUSDTPERP', 'APTUSDTPERP', 'ATOMUSDTPERP', 'APEUSDTPERP', 'ENSUSDTPERP', 'XRPUSDTPERP', 'SNXUSDTPERP', 'BCHUSDTPERP', 'BNBUSDTPERP', 'DOTUSDTPERP', 'MASKUSDTPERP']
['5m', '15m', '30m', '1h', '4h']

# from binance.client import Client
# from apibinance import api_key, api_secret
# client = Client(api_key, api_secret)
# import time
# import win32api
# gt = client.get_server_time()
# tt=time.gmtime(int((gt["serverTime"])/1000))
# win32api.SetSystemTime(tt[0],tt[1],0,tt[2],tt[3],tt[4],tt[5],0)

sla = [5 , 2, 10]
# sla.sort()

print(sorted(sla))