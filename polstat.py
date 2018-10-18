import urllib.request
import argparse
import json
import hashlib
import pathlib
import os
import datetime
import re
import math


CACHE_DIR= os.getenv("HOME") + '/temp/cache'
ENCODING='utf-8'

parser = argparse.ArgumentParser()
parser.add_argument("comando",choices=['deputado','apelidos','situacao'])
parser.add_argument("-i", '--identificacao', default='jairbolsonaro',help='identificador do deputado')
args = parser.parse_args()


apelidos_deputados = {
    "jairbolsonaro" : "74847",
    "eduardocunha" : "74173",
    "chicoalencar" : "74171",
    "tiririca" : "160976",
    "celsorussomano" : "73441",
    "reginaldolopes" : "74161",
    "rodrigodecastro" : "141531",
    "luciovieiralima" : "94931",
    "marcionegromonte" : "178858",
    "luizcarlosheinze" : "73483",
    "danrlei" : "160552",
}


def check_caching (href,cache_dir=CACHE_DIR):
    cache_id_hashing = hashlib.sha1()
    cache_id_hashing.update(href.encode('utf-8'))
    digest = cache_id_hashing.hexdigest()
    cache_dir_path = pathlib.Path(cache_dir)
    if not cache_dir_path.exists():
        cache_dir_path.mkdir(parents=True)
    cache_file = pathlib.Path(cache_dir + "/" + digest)
    return {'exists': cache_file.exists(), 'file':str(cache_file)}

def get_data(href, tipo=''):

    dados_respostas = []
    data = ''
    while href != '':

        res_caching = check_caching(href)

        if res_caching['exists']:
            #print("In caching: ", res_caching['file'])
            with open(res_caching['file'],encoding=ENCODING) as cache_file:
                data = cache_file.read()
        else:
            request = urllib.request.Request(href, headers={'accept': 'application/json'})

            res = urllib.request.urlopen(request)
            if res.getcode() == 200:

                data = res.read().decode(ENCODING)
                cache_f = open(res_caching['file'],'w',encoding=ENCODING)
                cache_f.write(data)
                cache_f.close()
            else:
                print("Error: ", res.getcode())
                return ""
        # print("===\n", data, "\n====\n")

        #props = data.decode('utf-8')
        j_props = json.loads(data)
        if isinstance(j_props['dados'], list):
            dados_respostas = dados_respostas + j_props['dados']
        else:
            # assume data is dict
            dados_respostas = j_props['dados']
        next = [l for l in j_props['links'] if l['rel'] == 'next']
        if len(next) > 0:
            #print('Next URL = ', next)
            href = next[0]['href']
        else:
            href = ''

    return dados_respostas


def to_date_object(string_date):
    date_matcher = re.compile('(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d:\d\d)')

    if date_matcher.match(string_date):
        date_matched = date_matcher.match(string_date).group()
        year = int(date_matched[:4])
        month = int(date_matched[5:7])
        day = int(date_matched[8:10])
        return datetime.date(year, month, day)
    else:
        return None

def prop_id_to_cat(categories):
    dict_id_to_cat = dict()
    for cat in categories:
        for prop in cat['propositions']:
            if not prop in dict_id_to_cat:
                dict_id_to_cat[prop] = cat['id']
    return dict_id_to_cat

def is_approved(proposition):
    if proposition['statusProposicao']['idSituacao'] == '1140':
        return True
    if proposition['statusProposicao']['idTipoTramitacao'] == '203':
        tramitacoes = get_data("https://dadosabertos.camara.leg.br/api/v2/proposicoes/" + str(proposition['id']) + "/tramitacoes")

    return proposition['statusProposicao']['idTipoTramitacao'] == '203'

def is_project(proposition, categories, inv_categories):
    cat = categories[inv_categories[proposition['idTipo']]-1]['ref']

    return cat == 'laws' or cat == 'decree' or cat == 'decreelr' or cat == 'amend'

def add_heatmap_data(dict_data, index, date_event) :
    timestamp = datetime.datetime(date_event.year, date_event.month, date_event.day).timestamp()
    if timestamp in dict_data[index]:
        dict_data[index][timestamp] =  dict_data[index][timestamp] + 1
    else:
        dict_data[index][timestamp] =  1


id_consultas = 0
if args.comando == 'situacao':
    situacoesProposicao = get_data('https://dadosabertos.camara.leg.br/api/v2/referencias/situacoesProposicao')
    print('Situacoes de uma proposicao')
    for sit in situacoesProposicao:
        print(sit['id'], ' => ', sit['nome'])
    quit()

elif args.comando == 'apelidos':
    ap = sorted(apelidos_deputados.keys())
    for i in ap:
        print(i)
    quit()
elif args.comando == 'deputado':
    if args.identificacao in apelidos_deputados:
        id_consultas = apelidos_deputados[args.identificacao]
    else:
        id_consultas = args.identificacao

proposicoes = get_data("https://dadosabertos.camara.leg.br/api/v2/proposicoes?idAutor=" + str(id_consultas) + "&itens=100")
tiposProposicao = get_data('https://dadosabertos.camara.leg.br/api/v2/referencias/tiposProposicao')
tiposTramitacao = get_data('https://dadosabertos.camara.leg.br/api/v2/referencias/tiposTramitacao')
situacoesProposicao = get_data('https://dadosabertos.camara.leg.br/api/v2/referencias/situacoesProposicao')

with open('deputados.json') as f_dep:
    deps = json.loads(f_dep.read())
    dep_info = [d for d in deps if d['id'] == int(id_consultas)][0]
    print(dep_info['nome'], ' - ', dep_info['siglaPartido'])

full_result = dict()
full_result['deputado'] = {'id': str(id_consultas), 'nome':dep_info['nome'], 'partido':dep_info['siglaPartido'],'estado':dep_info['siglaUf']}
full_result['proposicoes'] = dict()
full_result['heatmap-data'] = dict()
full_result['heatmap-data-approved'] = dict()
full_result['statistics'] = dict()


dict_proposicao = dict()
for prop in tiposProposicao:
    dict_proposicao[str(prop['id'])] = prop['nome']


categories = []
with open('data/categorias.json') as cat_f:
    categories = json.loads(cat_f.read())
inv_categories = prop_id_to_cat(categories)

for cat in categories:
    full_result["heatmap-data-" + cat['ref']] = dict()

num_p = 1
problemas = []
detailed_propositions = []
sum_tipo_prop = dict()
sum_cat_prop = dict()

for i in proposicoes:

    prop = get_data(i['uri'])
    prop_date = to_date_object(prop['dataApresentacao'])
    prop['date'] = prop_date
    detailed_propositions.append(prop)

    if prop['idTipo'] in sum_tipo_prop:
        sum_tipo_prop[prop['idTipo']] = sum_tipo_prop[prop['idTipo']] + 1
    else:
        sum_tipo_prop[prop['idTipo']] = 1

    prop_cat = inv_categories[prop['idTipo']]
    if prop_cat in sum_cat_prop:
        sum_cat_prop[prop_cat] = sum_cat_prop[prop_cat] + 1
    else:
        sum_cat_prop[prop_cat] = 1

    if i['ano'] == 0:
        problemas.append(i)
    num_p = num_p + 1

prop_by_date = sorted(detailed_propositions, key=lambda k: k['date'])


detailed_propositions.sort(key=lambda k: k['date'])
for p in detailed_propositions:

    full_result['proposicoes'][p['id']] = {
        'id':p['id'],
        'nome':p['siglaTipo'] + " " + str(p['numero']) + "/" + str(p['date'].year),
        'data':str(p['date']),
        'numero':p['numero'],
        'aprovado':is_approved(p),
        'eProjeto':is_project(p,categories,inv_categories),
        'ano':p['ano'],
        'siglaTipo':p['siglaTipo'],
        'ementa':p['ementa'],
        'url':p['urlInteiroTeor']
    }

    add_heatmap_data(full_result, 'heatmap-data',p['date'])

init_sum_cat_year = dict()
for c in categories:
    init_sum_cat_year[c['id']] = 0

by_year = 1
sum_cat_year = dict(init_sum_cat_year)

current_year = prop_by_date[0]['date'].year
for prop in prop_by_date:

    if prop['date'].year != current_year:
        print(" Total Events for year " + str(current_year) + ": " + str(by_year))

        for scy in sum_cat_year:
            cat_desc = [c for c in categories if c['id'] == scy]

        by_year = 1
        sum_cat_year = dict(init_sum_cat_year)
        current_year = prop['date'].year
    else:
        by_year = by_year + 1


    sum_cat_year[inv_categories[prop['idTipo']]] = sum_cat_year[inv_categories[prop['idTipo']]] + 1

    if is_approved(prop):
        add_heatmap_data(full_result, 'heatmap-data-approved',prop['date'])

    add_heatmap_data(full_result,
                     "heatmap-data-"+categories[inv_categories[prop['idTipo']]-1]['ref'],
                     prop['date'])

print(" Total Events for year " + str(prop['date'].year) + ": " + str(by_year))

print('\nPeriod for event evaluation: ')
print(str(detailed_propositions[0]['date']) + " - " + str(detailed_propositions[len(detailed_propositions)-1]['date']))

primeiro_evento = detailed_propositions[0]['date']
ultimo_evento = detailed_propositions[len(detailed_propositions)-1]['date']
anos_decorridos = ultimo_evento.year - primeiro_evento.year
meses_decorridos = ultimo_evento.month + (12-primeiro_evento.month)
total_meses = meses_decorridos + 12*anos_decorridos

print(anos_decorridos, ' year and ',meses_decorridos,' months')
print('... or ',total_meses, ' months')



# full_result['statistics']['nome'] =
# full_result['statistics']['partido'] =
full_result['statistics']['first-date'] = str(primeiro_evento)
full_result['statistics']['last-date'] = str(ultimo_evento)
full_result['statistics']['deputado'] = full_result['deputado']



def sum_heatmap(heat_dict, reference):
    total = 0
    for i in heat_dict[reference]:
        total = total + heat_dict[reference][i]
    return total


n_projetos = sum_heatmap(full_result,'heatmap-data-laws') + sum_heatmap(full_result,'heatmap-data-decree') + sum_heatmap(full_result,'heatmap-data-decreelr') + sum_heatmap(full_result,'heatmap-data-amend')
n_projetos_aprovados = len(full_result['heatmap-data-approved'])
n_projetos_aprovados = sum_heatmap(full_result,'heatmap-data-approved')
#n_proposicoes = len(full_result['heatmap-data'])
n_proposicoes = sum_heatmap(full_result,'heatmap-data')
if n_projetos > 0:
    print("Projects: " + str(n_projetos) + " (1 project for each " + str(round(total_meses/n_projetos,2)) + " month)")
    full_result['statistics']['month-projects'] = round(total_meses/n_projetos,2)

if full_result['deputado']['id'] == '160976':
    # deputado == Tiririca => acrescentar 1 projeto devido a erro no sistema camara que nao computa projeto
    # http://www.camara.gov.br/proposicoesWeb/fichadetramitacao?idProposicao=559088
    n_projetos_aprovados = 1
if n_projetos_aprovados > 0:
    print("Approved projects: " + str(n_projetos_aprovados) + " (1 project for each " + str(round(total_meses/n_projetos_aprovados,2)) + " months)")
    full_result['statistics']['month-approved-projects'] = round(total_meses/n_projetos_aprovados,2)

if n_proposicoes > 0:
    print("Propositions: " + str(n_proposicoes) + " (1 proposition for each " + str(round(4.36*total_meses/n_proposicoes,2)) + " week)")
    full_result['statistics']['weeks-propositions'] = round(4.36*total_meses/n_proposicoes,2)






for scy in sum_cat_year:
    cat_desc = [c for c in categories if c['id'] == scy]

dep_data_dir = pathlib.Path("data/" + str(id_consultas))
if not dep_data_dir.exists():
    dep_data_dir.mkdir(parents=True)
dep_data_dir_str = str(dep_data_dir)


with open(dep_data_dir_str + "/proposicoes.json",'w') as f_prop:
    f_prop.write(json.dumps(full_result))

with open(dep_data_dir_str + "/heatmap.json",'w') as f_prop:
    f_prop.write(json.dumps(full_result['heatmap-data']))

with open(dep_data_dir_str + "/heatmap-approved.json",'w') as f_prop:
    f_prop.write(json.dumps(full_result['heatmap-data-approved']))

for k in full_result.keys():
    if k.startswith('heatmap-data-'):
        with open(dep_data_dir_str + "/" + k + ".json",'w') as h_f:
            h_f.write(json.dumps(full_result[k]))
        h_f.close()

with open(dep_data_dir_str + "/statistics.json",'w') as f_stat:
    f_stat.write(json.dumps(full_result['statistics']))
