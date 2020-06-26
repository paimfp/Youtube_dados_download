#%%
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from pytube import YouTube
import json
import traceback

URL_BUSCA_BPLAY = 'https://www.youtube.com/channel/UClsm8e0m-a-pLQTE31YmasQ/search?query='

def pegar_id_cod(cod):
    '''
        Usa a url de busca do BernoulliPlay para pegar o link de visualização do código `cod`.

        `cod`: string com código alpha numérico\n
        `return`: dic do ID do vídeo com código especificado e título do vídeo.
    '''
    ## REFERÊNCIA DO TÍTULO DO VÍDEO E COD YOUTUBE:
    #title = dic_json['contents']['twoColumnBrowseResultsRenderer']['tabs'][6]['expandableTabRenderer']['content']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]['videoRenderer']['title']['simpleText']
    #id_yt = dic_json['contents']['twoColumnBrowseResultsRenderer']['tabs'][6]['expandableTabRenderer']['content']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]['videoRenderer']['videoId']

    ## FUNÇÃO ANTIGA USANDO HTML, NÃO TAG SCRIPT:
    # def link_com_codigo_BPlay(cod): # Usa a url de busca do BernoulliPlay para pegar o link de visualização do código 'cod'
    # source = requests.get(URL_BUSCA_BPLAY + cod).text
    # soup = BeautifulSoup(source, "html.parser")
    # for link in soup.select('a[href^="/watch"]'):
    #     if cod.upper() in link.text.upper():
    #         parte_video = link.get('href')
    #         print(parte_video)
    #         return ('https://www.youtube.com' + parte_video)
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'}
    source = requests.get(URL_BUSCA_BPLAY + cod, headers=headers).text
    soup = BeautifulSoup(source, "html.parser")
    cont = 0
    for script in soup.find_all('script'):
        if script:
            script = script.text.strip()
            if script.startswith('window["ytInitialData"]'):
                i = 0
                while True:
                    try:
                        dic_json = json.loads((script[script.find('=')+1:i]))
                        break
                    except:
                        i -= 1
                for tab in dic_json['contents']['twoColumnBrowseResultsRenderer']['tabs']:
                    if tab:
                        tab_contents = tab.get('expandableTabRenderer',{}).get('content',{}).get('sectionListRenderer',{}).get('contents')
                        if tab_contents:
                            for content in tab_contents:
                                tabs_contents_render = content.get('itemSectionRenderer',{}).get('contents')
                                if tabs_contents_render:
                                    for tab_cont_cont in tabs_contents_render:
                                        if tab_cont_cont:
                                            title = tab_cont_cont.get('videoRenderer',{}).get('title',{}).get('simpleText')
                                            if title:
                                                if cod in title:
                                                    id_yt = tab_cont_cont.get('videoRenderer',{}).get('videoId')
                                                    return {'id' : [id_yt], 'nome' : [title]}

def agrupar_ids_cod(codigos_xlsx = 'codigos.xlsx', dados_parciais_xlsx = 'cods_ids_parciais.xlsx'):
    try:
        dados_parciais = pd.read_excel(dados_parciais_xlsx)
        cods_feitos = dados_parciais.iloc[:,2].to_list()
    except:
        print('\nComeçando do zero, criando arquivos...\n')
        dados_parciais = pd.DataFrame()
        cods_feitos =[]
    try:
        df_todos_cods = pd.read_excel(codigos_xlsx)
        list_todos_cods = df_todos_cods.iloc[:,0].to_list()
        list_todos_cods = [x.replace('0', 'Ø').upper() for x in list_todos_cods]
    except Exception:
        print('Erro: Sem arquivo com pra pegar os codigos!')
        traceback.print_exc()
    print(f'Total de códigos: {len(list_todos_cods)}')
    print(f'Feitos parcial: {len(cods_feitos)}')
    print('Progresso:\n')
    num_cods_passados = 0

    for cod in list_todos_cods:
        num_cods_passados += 1
        val = int((((num_cods_passados/len(list_todos_cods))*500)//10))
        str_progress_bar = '<' + '='*val + ' '*(50-val) + '> ' + str(((num_cods_passados/len(list_todos_cods))*100))[:4] + ' %'
        print(f'\r{str_progress_bar}', end='')
        if cod not in cods_feitos and cod.replace('Ø','0') not in cods_feitos:
            cods_feitos.append(cod)
            #print(f'\r>> {(num_cods_passados/len(list_todos_cods))*100:.1f} %', end='')
            time.sleep(2)
            dic_cod = pegar_id_cod(cod)
            if dic_cod:
                dic_cod = {**dic_cod,**{'cod' : [cod]},}
                dados_parciais =  pd.concat([dados_parciais, pd.DataFrame(dic_cod)],ignore_index=True, sort=None)
            else:
                cod = cod.replace('Ø','0')
                dic_cod = pegar_id_cod(cod)
                if dic_cod:
                    dic_cod = {**dic_cod,**{'cod' : [cod]},}
                    dados_parciais =  pd.concat([dados_parciais, pd.DataFrame(dic_cod)],ignore_index=True, sort=None)
                else:
                    print(f'\nId do {cod} não encontrado!')
            dados_parciais.to_excel(dados_parciais_xlsx, encoding='utf16', index=False)

    dados_parciais.to_excel('codigos completos.xlsx', encoding='utf16', index=False)


def baixar_videos(n, nome_excel='_Dados_vídeos_gravados.xlsx', header=1):
    '''Baixa os n primeiros vídeos do excel gerado. (Por exemplo, ordenados por mais views no excel)
    Maior resolução em MP4 disponível, o nome do arquivo é o código do vídeo.'''
    
    dados = pd.read_excel(nome_excel, header=header)
    
    for linha in range(n):
        id_video = dados.iloc[linha,0]
        name = dados.iloc[linha,1]
        link = 'https://www.youtube.com/watch?v='+ id_video
        print(link, name)
        YouTube(link).streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download(filename = name)