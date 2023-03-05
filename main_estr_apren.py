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

def last_close(synbol, interval): # pegar o ultimo fechamento
    return client.futures_historical_klines(synbol, interval, '1d')[-2][4]

def all_candles(synbol, interval, limit='10w'): # pegar todas as velas # a variavel limit é o tempo em que ele vai pegar as velas
    return client.futures_historical_klines(synbol, interval, limit)

def all_closes(candles): # para pegar todos os fechamentos de uma variavel que ja tenha as velas
    return [close[4] for close in candles]

def give_rsi(close): # para pegar os rsi dos fechamentos
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

def pega_media_movel(close): # para pegar as medias moveis de um fechamento
    close = pd.Series(close)
    close = pd.Series(close).astype(float)
    ma_25 = close.rolling(window=25).mean()
    ma_50 = close.rolling(window=50).mean()
    ma_100 = close.rolling(window=100).mean()
    return list(ma_25), list(ma_50), list(ma_100)

def entende_media(ma_25, ma_50, ma_100, n=-2): # simplificação das médias móveis
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

def rsi_simplificado(rsi): # simplificação da tendencia
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

tempo = '1m' # o tempo em que as velas vão correr
# saves['btcusdt'] = {tempo : {}} tirei pq por em quanto n vai ser necessario

# usar os fechamentos que ja foram salvos
arquivo = open('fechamentos.txt', 'r')
fechamentos = eval(arquivo.read())
arquivo.close()

# pegar novos fechamentos e salvar
# velas = all_candles('btcusdt', tempo)
# fechamentos = all_closes(velas)
# arquivo = open('fechamentos.txt', 'w')
# arquivo.write(str(fechamentos))
# arquivo.close()

# variaveis que serão armazenadas o rsi e as médias móveis
rsi = give_rsi(fechamentos)
ma_25, ma_50, ma_100 = pega_media_movel(fechamentos)

# vari = f'{((ant_close - close) * 100)/close:.2f}%' para descobrir a variação

quant_save = 2 # quantidade do histórico que sera salvo para 
vari = None

# esqueleto da variavel saves:

# como funciona essa variavel:
# [{ # para apostas em tempo de 1
#   'primeira_variacao': vari_ant,
#   'segunda_variacao': [vari],
#   'rsi': rsi,
#   'tendencia': entende_media(ma_25, ma_50, ma_100, n=num-1),
#   'aposta': {'cima': {GLA}, 'baixo': {GLA}, 'apostar': False, 'direcao': None}
#   }]

# [{ # para apostas em tempo variado
#   'primeira_variacao': vari_ant,
#   'segunda_variacao': [vari],
#   'rsi': rsi,
#   'tendencia': entende_media(ma_25, ma_50, ma_100, n=num-1),
#   'aposta': {'cima': {GLA}, 'baixo': {GLA}, 'apostar': False, 'direcao': None, 'tempo': tempo}
#   }]

# main

saves = [] # variavel para salvar as estratégias
em_aposta = False
tempo_de_espera = 0
acertividade_geral = {'green': 0, 'loss': 0, 'tempo_de_espera': [], 'vari_ganho': [], 'vari_perda': []}
save_existente = False
apostas = []
# iniciando o loop sobre os fechamentos
for num, fec in enumerate(fechamentos):
    # usando variação com :.1f # uma casa depois da virgula
    # rsi 0-20=-2, 20-40=-1, 40-60=0, 60-80=1, 80-100=2
    
    if not num < quant_save: # para não dar erro no inicio
        vari = float(f'{((float(fechamentos[num-1]) - float(fec)) * 100)/float(fec):.1f}')
        vari_ant = float(f'{(float(fechamentos[num-2]) - (float(fechamentos[num-1])) * 100)/(float(fechamentos[num-1])):.1f}')

        for n, save in enumerate(saves): # verificando cada save para validação
            if (vari_ant == save['primeira_variacao']): # se a variação anterior bater com a primeira_variação do save

                if (rsi_simplificado(rsi[num-1]) == save['rsi']) and (entende_media(ma_25, ma_50, ma_100, n=num-1) == save['tendencia']): # caso o resto bata tambem
                    save_existente = True # salva como ja existente, para n acabar criando outro

                    # muda os valores dentro da chave 'aposta' caso seja necessario
                    if vari > 0.50:
                        saves[n]['aposta']['cima']['green'] += 1
                        saves[n]['aposta']['baixo']['green'] -= 1
                    elif vari < -0.50:
                        saves[n]['aposta']['cima']['green'] -= 1
                        saves[n]['aposta']['baixo']['green'] += 1
                    saves[n]['segunda_variacao'].append(vari)

                    for direcao in ['cima', 'baixo']:
                        saves[n]['aposta'][direcao]['acertividade'] = (saves[n]['aposta'][direcao]['green'] * 100) / (saves[n]['aposta'][direcao]['green'] + saves[n]['aposta'][direcao]['loss'])
                    
                    if saves[n]['aposta']['cima']['acertividade'] > saves[n]['aposta']['baixo']['acertividade']:
                        saves[n]['aposta']['direcao'] = 'cima'
                    elif saves[n]['aposta']['cima']['acertividade'] < saves[n]['aposta']['baixo']['acertividade']:
                        saves[n]['aposta']['direcao'] = 'baixo'
                    else:
                        saves[n]['aposta']['direcao'] = None

                    if saves[n]['aposta']['cima']['acertividade'] > 80 or saves[n]['aposta']['baixo']['acertividade'] > 80:
                        saves[n]['aposta']['apostar'] = True
                    else:
                        saves[n]['aposta']['apostar'] = True

        if save_existente == False: # cria a estratégia caso não exista a estratégia
            saves.append({
                        'primeira_variacao': vari_ant,
                        'segunda_variacao': [vari],
                        'rsi': rsi_simplificado(rsi[num-1]),
                        'tendencia': entende_media(ma_25, ma_50, ma_100, n=num-1), 
                        'aposta': {'cima': {'green': 0, 'loss': 0, 'acertividade': 0}, 'baixo': {'green': 0, 'loss': 0, 'acertividade': 0}, 'apostar': False, 'direcao': None}
                        })
        else:
            save_existente = True

        for n, save in enumerate(saves): # verificando cada save para simulador de aposta
            if (vari == save['primeira_variacao']) and (rsi_simplificado(rsi[num]) == save['rsi']) and (entende_media(ma_25, ma_50, ma_100, n=num) == save['tendencia']):
                pass
                # criar um sistema de aposta

