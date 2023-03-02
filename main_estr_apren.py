from binance.client import Client
from apibinance import api_key, api_secret
import numpy as np
import pandas as pd
import time
import os

#login client
client = Client(api_key, api_secret, testnet=True)

#sincronizing ao server time
gt = client.get_server_time()
tt=time.gmtime(int((gt["serverTime"])/1000))
os.system(f'touch -t {tt[0],tt[1],0,tt[2],tt[3],tt[4],tt[5],0}')

def last_close(synbol, interval):
    return client.futures_historical_klines(synbol, interval, '1d')[-2][4]

def all_candles(synbol, interval, limit='10w'):
    return client.futures_historical_klines(synbol, interval, limit)

def all_closes(candles):
    return [close[4] for close in candles]

def give_rsi(close):
    close = pd.Series(close)
    close = pd.Series(close).astype(float)
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return list(rsi)

def pega_media_movel(close):
    close = pd.Series(close)
    close = pd.Series(close).astype(float)
    ma_25 = close.rolling(window=25).mean()
    ma_50 = close.rolling(window=50).mean()
    ma_100 = close.rolling(window=100).mean()
    return list(ma_25), list(ma_50), list(ma_100)

def entende_media(ma_25, ma_50, ma_100, n=-2):
    tipo = None

    if type(n) == int:

        ma_25 = ma_25[n]
        ma_50 = ma_50[n]
        ma_100 = ma_100[n]

        if ma_25 > ma_50 > ma_100:
            tipo = 'subindo'
        elif ma_25 < ma_50 < ma_100:
            tipo = 'descendo'
        elif ma_25 < ma_50 > ma_100 and ma_25 > ma_100 < ma_50:
            tipo = 'tendencia_descendo'
        elif ma_25 < ma_100 > ma_50 and ma_25 > ma_50 < ma_100:
            tipo = 'tendencia_subindo'
    return tipo

tempo = '1m'
# saves['btcusdt'] = {tempo : {}} tirei pq por em quanto n vai ser necessario

# pegar um já salvo
arquivo = open('fechamentos.txt', 'r')
fechamentos = eval(arquivo.read())
arquivo.close()

# escrever para salvar
# velas = all_candles('btcusdt', tempo)
# fechamentos = all_closes(velas)
# arquivo = open('fechamentos.txt', 'w')
# arquivo.write(str(fechamentos))
# arquivo.close()

rsi = give_rsi(fechamentos)
ma_25, ma_50, ma_100 = pega_media_movel(fechamentos)

# apartir da qui
# vari = f'{((ant_close - close) * 100)/close:.2f}%'
saves = {}
vari = None
for num, fec in enumerate(fechamentos):
    if num == 0:
        vari = 0
    else:
        vari = f'{((float(fechamentos[num-1]) - float(fec)) * 100)/float(fec):.2f}%'
    print(f'fechamento: {fec}\nvariação: {vari}\nrsi: {rsi[num]:.2f}\nmédia movel 25,50,100: {ma_25[num]:.2f} | {ma_50[num]:.2f} | {ma_100[num]:.2f}\n\n\n')
    time.sleep(1)
