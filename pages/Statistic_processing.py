import streamlit as st
import pandas as pd
import io

if 'table_list_of_dict' not in st.session_state:
    st.session_state['table_list_of_dict'] = []

if 'processed_data_list_of_dict' not in st.session_state:
    st.session_state['processed_data_list_of_dict'] = []


@st.cache_data
def get_dict(tablename, dataframe):
    return {'name': tablename, 'DataFrame': dataframe}


# main

st.write(
    '''
    На этой странице Вы можете произвести статистическую обработку Ваших данных. <br>
    <br>
    Загрузите Ваш Excel файл, если ранее вы не загружали файлы, и выберете, слева, таблицу для которой хотите получить
    статистическую обработку.
    ''',
    unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Upload your Excel table here and click on 'Process'", accept_multiple_files=True, type=['xlsx', 'xls'])

# display loaded in session storage tables on sidebar
with st.sidebar:
    with st.expander(label='Tables'):
        st.write('Select table who you want get statistic')
        for idx, d in enumerate(st.session_state['table_list_of_dict']):
            if st.checkbox(d['name'], key=idx):
                # if user choose some table for processing? then put her in processed_list
                # list in session storage. These tables display on main frame
                if not (d in st.session_state['processed_data_list_of_dict']):
                    st.session_state['processed_data_list_of_dict'].append(d)
            else:
                # if checkbox off, then appropriate table delete from processed_list
                if d in st.session_state['processed_data_list_of_dict']:
                    st.session_state['processed_data_list_of_dict'].remove(d)

if st.button("Upload"):
    # load upload data in session storage
    for uploaded_file in uploaded_files:
        name = uploaded_file.name
        df = pd.read_excel(uploaded_file.getvalue())
        try:
            # if user upload two some file pandas throw exception ValueError when compare just processed file and
            # contained in session storage some file. If this happened, then just processed file will be ignored
            d = get_dict(name, df)
            if d not in st.session_state['table_list_of_dict']:
                st.session_state['table_list_of_dict'].append(d)
        except ValueError:
            pass
    # uploaded_files.clear()

# statistic processing and display result into expander list
for val in st.session_state['processed_data_list_of_dict']:
    name = val['name']
    with st.expander(label=name):
        df = val['DataFrame']
        st.dataframe(df)

        buffer = io.StringIO()
        df.info(buf=buffer)
        s = buffer.getvalue()
        st.text(s)
