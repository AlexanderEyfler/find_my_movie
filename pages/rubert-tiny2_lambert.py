import streamlit as st
import time
import pandas as pd
from src.lamberts_funcs import search_movies, find_movies_with_all_words
from sentence_transformers import SentenceTransformer
from pathlib import Path

script_path = Path(__file__).resolve()
script_dir = script_path.parent
path_df = script_dir.parent / 'data' / 'all_data.csv'

@st.cache_data
def load_data():
    df = pd.read_csv(path_df)
    return df

movies_data = load_data()
movies_data = movies_data.rename(columns={'film_name': 'movie_title', 'image': 'image_url'})

st.title("Умный поиск фильмов")
st.subheader("В проекте участвовали: :blue[Алексей], :blue[Александр], :red[Диана], :blue[Ламберт] :sunglasses:")

txt = st.text_area("Описание фильма")

if st.button("Найти фильм"):
    if txt:        
        start_time = time.time()
        movies_data = find_movies_with_all_words(txt, movies_data)
        movies_data = movies_data.drop_duplicates(subset=['movie_title'])
        results = search_movies(txt, movies_data)
        end_time = time.time()

        st.write("Результаты поиска:")
        if results:  
            for row in results:
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if row['image_url'].startswith("http"):
                            st.image(row['image_url'], width=100)
                        else:
                            st.write("Изображение недоступно")
                    with col2:
                        st.write(f"**{row['movie_title']}**") 
                        st.write(row['description'])
                    st.markdown("---")
            else:
                st.write("Ничего больше не найдено по вашему запросу.")
            
            processing_time = end_time - start_time
            st.write(f"Время обработки: {processing_time:.2f} секунд")
    else:
        st.warning("Пожалуйста, введите описание фильма перед поиском.")
