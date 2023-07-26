import streamlit as st
from haystack.document_stores import ElasticsearchDocumentStore
from haystack.pipelines import DocumentSearchPipeline
from haystack.nodes import EmbeddingRetriever
from time import time
import datetime

date_from = ''
date_to = ''


# @st.cache_data
def load_db():
    # Conectar com o ElasticSearch e criar um indice
    document_store = ElasticsearchDocumentStore(
        host="localhost",
        username="",
        password="",
        index="legis_jorge_v3",
        create_index=True,
        similarity="cosine",
    )

    return document_store


# @st.cache_data
def retriever():
    # Escolha do modelo para criar os embeddings na legislacao
    _retriever = EmbeddingRetriever(
        document_store=load_db(),
        use_gpu=True,
        embedding_model="../modelo/LegalBertPt_FP",
        model_format="sentence_transformers",
        max_seq_len=512
    )
    return _retriever


# @st.cache_data
# def data():
#    return pd.read_csv('C:\\Users\Renato Vidal\Documents\TJ-Semantico\data\legislatura\TESTE_RENATO_v2.csv')

@st.cache_data
def data():
    return load_db().get_all_documents()


def filtered_documents(orgao_justica='Selecione um orgao de justiça', orgao_julgador='Selecione um orgao julgador',
                       date_from=datetime.date.today(), date_to=datetime.date.today()):
    dados = data()

    amount_of_documents = 0

    date_from = datetime.datetime.combine(date_from, datetime.time(0, 0))
    date_to = datetime.datetime.combine(date_to, datetime.time(0, 0))

    today = datetime.datetime.combine(datetime.date.today(), datetime.time(0, 0))

    for dado in dados:
        if orgao_justica != 'Selecione um orgao de justiça':
            if orgao_justica == dado.meta['orgao_justica']:
                amount_of_documents += 1

        if orgao_julgador != 'Selecione um orgao julgador':
            if orgao_julgador == dado.meta['orgao_julgador']:
                amount_of_documents += 1

        if date_from != today:
            if date_from <= datetime.datetime.strptime(dado.meta['data_julgador'], '%Y-%m-%dT%H:%M:%S'):
                amount_of_documents += 1

        if date_to != today:
            if date_to >= datetime.datetime.strptime(dado.meta['data_julgador'], '%Y-%m-%dT%H:%M:%S'):
                amount_of_documents += 1

    return amount_of_documents


@st.cache_data
def get_orgao_filters():
    dados = data()

    orgao_justica = set()
    orgao_julgador = set()

    for doc in dados:
        orgao_julgador.add(doc.meta['orgao_julgador'])
        orgao_justica.add(doc.meta['orgao_justica'])

    return [list(orgao_julgador), list(orgao_justica)]


def query(query, orgao_justica='Selecione um orgao de justiça', orgao_julgador='Selecione um orgao julgador',
          date_from=datetime.date.today(), date_to=datetime.date.today()):
    pipeline = DocumentSearchPipeline(retriever())

    start = time()

    filters = {}

    date_today = datetime.date.today()

    if orgao_justica != 'Selecione um orgao de justiça':
        filters.update({
            "orgao_justica": orgao_justica
        })

    if orgao_julgador != 'Selecione um orgao julgador':
        filters.update({
            "orgao_julgador": orgao_julgador
        })

    if date_from != datetime.date.today():
        filters.update({
            "data_julgador": {
                "$gte": date_from,
                "$lte": date_today
            }
        })

    if date_to != datetime.date.today():
        filters.update({
            "data_julgador": {
                "$gte": date_from,
                "$lte": date_to
            }
        })

    result = pipeline.run(query, params={"Retriever": {"top_k": 3}, "filters": filters})
    print('Tempo decorrido:', (time() - start), 'segundos')

    return result['documents']


st.title('Teste 174k Trechos - TJ')

with st.form(key='my_form', ):
    col1, col2 = st.columns([3, 1])

    orgao_filters = get_orgao_filters()

    orgao_julgador = orgao_filters[0]
    orgao_justica = orgao_filters[1]

    with col1:
        orgao_justica = ['Selecione um orgao de justiça'] + orgao_justica
        orgao_justica = col1.selectbox('Selecione o orgao de justiça:', orgao_justica)

        orgao_julgador = ['Selecione um orgao julgador'] + orgao_julgador
        orgao_julgador = col1.selectbox('Selecione o orgao julgador:', orgao_julgador)

    with col2:
        date_from = col2.date_input(
            "De",
            datetime.date.today())

        date_to = col2.date_input(
            "Até",
            datetime.date.today())

        submit_buttom = col2.form_submit_button(label='Aplicar filtros')

#st.write('Total de documentos:', filtered_documents(orgao_justica, orgao_julgador, date_from, date_to))
busca = st.text_input('Busca', '')

try:
    query = query(busca, orgao_justica, orgao_julgador, date_from, date_to)
    st.title('Nossos resultados')
    for i in range(len(query)):
        st.title(f'Resultado {i + 1}')
        st.write('TEXTO:', query[i].meta['texto_original'])
        st.write('ID:', query[i].meta['id'])
        st.write('DATA:', query[i].meta['data_julgador'])
        st.write('JURISPRUDÊNCIA:', query[i].meta['jurisprudencia'])
        st.write('NORMAS:', query[i].meta['normas'])
        st.write('ORGÃO JUSTIÇA:', query[i].meta['orgao_justica'])
        st.write('ORGÃO JULGADOR:', query[i].meta['orgao_julgador'])
except:

    st.write('Esperando texto de busca')
