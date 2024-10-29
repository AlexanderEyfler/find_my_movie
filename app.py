import streamlit as st
import pandas as pd
import numpy as np

st.title('Main page for testing!')

df = pd.read_excel('data/Hand_parsed.xlsx', engine='openpyxl')
if st.button('Мне повезет!'):
    random_ind = np.random.choice(df.index, size=5, replace=False)
    random_movies = df.loc[random_ind, ['movie_title', 'description']]
    # Вывод результата
    st.write("5 случайных фильмов для просмотра на вечер:")
    for _, row in random_movies.iterrows():
        st.write(f"**{row['movie_title']}** - {row['description']}")
        