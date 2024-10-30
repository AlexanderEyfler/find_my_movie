import streamlit as st
from pathlib import Path
import pandas as pd
import numpy as np
import faiss
import requests
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# 0. Определяем пути до файлов
script_path = Path(__file__).resolve()
script_dir = script_path.parent
path_bi_encoder = script_dir.parent / 'data' / 'sasha' / 'local_bi_encoder'
path_df = script_dir.parent / 'data' / 'all_data.csv'
path_embed = script_dir.parent / 'data' / 'description_embeddings.npy'

# 1. Загрузка данных с кэшированием
@st.cache_data
def load_data():
    df = pd.read_csv(path_df)
    return df

df = load_data()
descriptions = df['description'].tolist()

# 2. Загрузка локально сохраненной модели с кэшированием
@st.cache_resource
def load_bi_encoder_model():
    return SentenceTransformer(str(path_bi_encoder))

bi_encoder_model = load_bi_encoder_model()

# 3. Загрузка предварительно вычисленных эмбеддингов с кэшированием
@st.cache_data
def load_description_embeddings():
    return np.load(path_embed)

description_embeddings = load_description_embeddings()

# 4. Создание индекса FAISS с кэшированием
@st.cache_resource
def create_faiss_index(embeddings):
    dimension_of_ind = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension_of_ind)
    index.add(embeddings)
    return index

index_faiss = create_faiss_index(description_embeddings)

# 5. Функция для запроса к модели NLI через API
API_TOKEN = st.secrets["huggingface"]["api_token"]
cross_encoder_model_name = 'cointegrated/rubert-base-cased-nli-threeway'
NLI_API_URL = f"https://api-inference.huggingface.co/models/{cross_encoder_model_name}"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "x-wait-for-model": "true"
    }

def query_nli(premise, hypothesis):
    inputs = f"{premise} [SEP] {hypothesis}"
    payload = {
        "inputs": inputs,
        "parameters": {
            "candidate_labels": ["entailment", "contradiction", "neutral"]
        }
    }
    response = requests.post(NLI_API_URL, headers=HEADERS, json=payload)
    if response.status_code != 200:
        raise ValueError(f"Request failed with status code {response.status_code}: {response.text}")
    output = response.json()
    if 'labels' in output and 'scores' in output:
        labels = output['labels']
        scores = output['scores']
        proba = dict(zip(labels, scores))
        entailment_score = proba.get('entailment', 0.0)
        return entailment_score
    else:
        raise ValueError(f"Unexpected response format: {output}")

# 6. Функция для получения оценок entailment с кэшированием
@st.cache_data
def get_entailment_scores(user_query, descriptions):
    entailment_scores = []
    for description in tqdm(descriptions, desc='Переранжирование результатов'):
        try:
            score = query_nli(user_query, description)
            entailment_scores.append(score)
        except ValueError as e:
            st.write(f"Ошибка при обработке описания: {e}")
            entailment_scores.append(0.0)
    return entailment_scores

# 7. Интерфейс Streamlit
st.title("Поиск фильмов по текстовому описанию")
# Создание формы для ввода запроса и выбора числа результатов
with st.form(key='search_form'):
    user_query = st.text_input("Введите описание фильма или запрос:")
    N = 50 # максимальное число быстро отобранных фильмов
    K = st.slider("Количество результатов для отображения:", min_value=1, max_value=N, value=5, step=1)
    submit_button = st.form_submit_button(label='Найти')

if submit_button:
    if not user_query.strip():
        st.warning("Введите описание фильма или запрос!")
    else:
        # 8. Обработка пользовательского запроса
        with st.spinner('Вычисление эмбеддингов запроса...'):
            query_embedding = bi_encoder_model.encode([user_query], convert_to_numpy=True)
            query_embedding = np.array(query_embedding, dtype='float32')

        # 9. Поиск топ-N кандидатов с помощью FAISS
        with st.spinner('Поиск кандидатов с помощью FAISS...'):
            distances, indices = index_faiss.search(query_embedding, N)
        candidate_indices = indices[0]
        candidate_descriptions = [descriptions[idx] for idx in candidate_indices]

        # 10. Получение оценок entailment (переранжирование)
        with st.spinner('Переранжирование результатов...'):
            rerank_scores = get_entailment_scores(user_query, candidate_descriptions)

        # 11. Обработка и вывод результатов
        results = list(zip(candidate_indices, rerank_scores))
        results.sort(key=lambda x: x[1], reverse=True)

        # Вывод топ-K результатов
        top_results = results[:K]

        # Проверяем, что в топ-K есть результаты
        if not top_results:
            st.info("Нет результатов, соответствующих вашему запросу!")
        else:
            st.header(f"Топ-{K} фильмов, соответствующих вашему запросу:")
            for idx, score in top_results:
                film_name = df.iloc[idx]['film_name']
                imdb_rating = df.iloc[idx]['IMDb']
                director = df.iloc[idx]['director']
                actors = df.iloc[idx]['actors']
                description = df.iloc[idx]['description']
                image_url = df.iloc[idx]['image']

                # Создаем две колонки: одна для изображения, другая для информации
                col1, col2 = st.columns([1, 3])

                with col1:
                    st.image(image_url, width=150, caption=film_name)

                with col2:
                    st.subheader(film_name)
                    st.markdown(f"**Рейтинг IMDb:** {imdb_rating}")
                    st.markdown(f"**Режиссер:** {director}")
                    st.markdown(f"**Актеры:** {actors}")
                    st.markdown(f"**Описание:** {description}")
                    st.markdown(f"**Сходство:** {score:.3f}")
                    st.markdown("---")
