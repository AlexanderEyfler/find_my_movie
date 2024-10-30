import streamlit as st
import faiss
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import re
from pathlib import Path


script_path = Path(__file__).resolve()
script_dir = script_path.parent
path_rubert = script_dir.parent / 'data' / 'rubert-tiny2'

@st.cache_resource
def load_lambert_model():
    return SentenceTransformer(str(path_rubert))
model = load_lambert_model()

def find_movies_with_all_words(query, df):
    query_words = set(query.lower().split())
    matched_indices = set()
    
    def contains_all_words(text):
        if pd.isna(text):
            return False
        
        text_words = set(re.split(r'[,\s]+', text.lower()))
        return query_words.issubset(text_words)
    
    columns_to_search = ['movie_title', 'director', 'actors']
    
    for column in columns_to_search:
        matching_texts = df[df[column].apply(contains_all_words)]
        matched_indices.update(matching_texts.index)
    
    if matched_indices:
        return df.loc[list(matched_indices)].drop_duplicates()
    else:
        return df


def search_movies(query, movies_data, threshold=5, top_k=10):
    if len(movies_data) < top_k:
        top_k = len(movies_data)
    
    titles = movies_data['movie_title'].tolist()
    descriptions = movies_data['description'].tolist()
    images = movies_data['image_url'].tolist()
    actors = movies_data['actors'].tolist()
    directors = movies_data['director'].tolist()

    corpus = [(image, title, description) for image, title, description in zip(images, titles, descriptions)]

    title_embeddings = model.encode(titles).astype("float32")
    description_embeddings = model.encode(descriptions).astype("float32")

    # Создание FAISS индексов для быстрого поиска
    title_index = faiss.IndexFlatIP(title_embeddings.shape[1])
    title_index.add(title_embeddings)

    description_index = faiss.IndexFlatIP(description_embeddings.shape[1])
    description_index.add(description_embeddings)


    embeddings = description_embeddings
    index = description_index

    if len(query.split()) > threshold:
        # Длинный запрос: симметричный поиск
        query_embedding = model.encode([query])
        similarities = util.cos_sim(query_embedding, embeddings)
        results = [(corpus[i], similarities[0][i].item()) for i in range(len(corpus))]
    else:
        # Короткий запрос: асимметричный поиск с FAISS
        query_embedding = model.encode([query]).astype("float32")
        D, I = index.search(query_embedding, k=top_k)
        results = [(corpus[i], D[0][idx]) for idx, i in enumerate(I[0])]

    # Сортировка и выбор топ-K результатов
    results = sorted(results, key=lambda x: x[1], reverse=True)[:top_k]
    
    formatted_results = [
        {"image_url": res[0][0], "movie_title": res[0][1], "description": res[0][2], "similarity": res[1]}
        for res in results
    ]
    return formatted_results