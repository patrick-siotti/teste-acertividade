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

def rsi_simplificado(rsi):
    if rsi >= 0 and rsi < 20:
        rsi_sim = -2
    elif rsi >= 20 and rsi < 40:
        rsi_sim = -1
    elif rsi >= 40 and rsi < 60:
        rsi_sim = 0
    elif rsi >= 60 and rsi < 80:
        rsi_sim = 1
    elif rsi >= 80 and rsi <= 100:
        rsi_sim = 2
    
    return rsi_sim

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

# vari = f'{((ant_close - close) * 100)/close:.2f}%' para descobrir a variação
quant_save = 2 # quantidade do histórico que sera salvo para 
vari = None

# como funciona essa variavel:
# [{'variacao': [variação_de_entrada, [lista_contendo_variações_seguintes]],
#  'rsi': [rsi_da_primeira_variação, rsi_da_segunda_variação],
#  'tendencia': [tendencia da primeira variação, tendencia da segunda variação], 
#  'primeira_vari': 0, inteiro com a variação da primeira aposta
#  'deslocamento_final': 0, inteiro com o deslocamento final
#  'green': 0, 'loss': 0,  inteiros para acerto e falha
#  'acertividade': 0, flutuante com a acertividade
#  'apostar': False}] booleano se deve apostar ou não

saves = [] # variavel para salvar as estratégias
em_aposta = False
tempo_de_espera = 0
acertividade_geral = {'green': 0, 'loss': 0, 'tempo_de_espera': [], 'vari_ganho': [], 'vari_perda': []}
save_existente = False
for num, fec in enumerate(fechamentos):
    # usando variação com :.1f # uma casa depois da virgula
    # rsi 0-20=-2, 20-40=-1, 40-60=0, 60-80=1, 80-100=2
    # print(f'fechamento: {fec}\nvariação: {vari:.1f}\nrsi: {rsi[num]:.2f}\nmédia movel 25,50,100: {ma_25[num]:.2f} | {ma_50[num]:.2f} | {ma_100[num]:.2f}\n\n\n')
        
    if not num < quant_save:
        vari = float(f'{((float(fechamentos[num-1]) - float(fec)) * 100)/float(fec):.1f}')
        vari_ant = float(f'{(float(fechamentos[num-2]) - (float(fechamentos[num-1])) * 100)/(float(fechamentos[num-1])):.1f}')

        # se ja não foi criado uma dessas, sendo vc a segunda variação, e verificar se bateu como deveria bater, se caso ouver, verificar a acertividade e se deve atualizar alguma informação
        for n, save in enumerate(saves):
            if (vari_ant == save['variacao'][0]):
                save_existente = True

                if (rsi_simplificado(rsi[num-1]) == save['rsi'][0]) and (entende_media(ma_25, ma_50, ma_100, n=num-1) == save['tendencia'][0]):
                # verificar se bateu
                    # antes de adicionar, ver se o rsi bateu e se a tendencia bateu
                    # repensar se esse é o melhor esqueleto
                    if vari > 0.50 or vari < -0.50:
                        saves[n]['variacao'][1].append(vari)
                    elif vari < 0.50 and vari < -0.50:
                        saves[n]['variacao_menor'].append(vari)

            
            # verificar se ja não foi criado uma dessas sendo vc a primeira variação, verificando se a aposta esta ativa

        if save_existente == False:
            saves.append({
                        'variacao': [vari_ant, ([vari]) if (vari > 0.50 or vari < -0.50) else []],
                        'variacao_menor': ([vari]) if (vari < 0.50 and vari > -0.50) else [],
                        'rsi': [rsi_simplificado(rsi[num-1]), rsi_simplificado(rsi[num])], 
                        'tendencia': [entende_media(ma_25, ma_50, ma_100, n=num-1), entende_media(ma_25, ma_50, ma_100, n=num)], 
                        'primeira_vari': vari_ant, 
                        'deslocamento_final': vari_ant + vari, 
                        'green': 0, 'loss': 0, 
                        'acertividade': 0, 
                        'apostar': False
                        })
        else:
            save_existente = True
