import base64

import streamlit as st
import streamlit.components.v1 as components
from table_reader.table_process import TableReader
from cv2 import imdecode
from numpy import asarray, uint8
from io import BytesIO


@st.cache_resource(ttl=120)
def load_reader():
    return TableReader()


@st.cache_data
def get_dict(tablename, dataframe):
    return {'name': tablename, 'DataFrame': dataframe}


def download_button(dataframe):
    buf = BytesIO()
    columns = dataframe.columns
    dataframe.to_excel(excel_writer=buf, columns=columns, index=False)
    buf.seek(0, 0)

    try:
        # some strings <-> bytes conversions necessary here
        b64 = base64.b64encode(buf.read()).decode()

    except AttributeError as e:
        b64 = base64.b64encode(buf).decode()

    dl_link = f"""
        <html>
        <head>
            <title>Start Auto Download file</title>
            <script src="http://code.jquery.com/jquery-3.2.1.min.js"></script>
            <script>
                $(function() {{
                $('a[data-auto-download]').each(function(){{
                var $this = $(this);
                setTimeout(function() {{
                window.location = $this.attr('href');
                                      }}, 500);
                                }});
                }});
            </script>
        </head>
            <body>
                <div class="wrapper">
                    <a data-auto-download href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}"></a>
                </div>
            </body>
        </html>
    """

    return dl_link


def download_df(dataframe):
    components.html(
        download_button(dataframe),
        height=0,
    )


reader = load_reader()

# list with dict {name, DataFrame}
# here contain all data who was uploaded and processed in one session
if 'table_list_of_dict' not in st.session_state:
    st.session_state['table_list_of_dict'] = []

# main

st.write(
    '''
     На этом сайте Вы можете конвертировать изображение или PDF файлы содержащие таблицы в excel файлы.<br>
     <br>
     <b>Примечание!</b> Все таблицы которые будут находится в одном PDF файле будут объеденины в одну таблицу<br>
     <br>
     <b>Совет</b><br>
     Для того что бы алгоритм качественнее прочитал файл лучше использовать сканы документов.<br>
     Так же для корректной работы алгоритма необходимо что бы таблица располагалась ровно,<br> 
     допускается некоторый поворот таблицы, но не более 90 градусов.<br>
     <br>
     Если  Вы захотите изменить какие-либо значения в таблице, тогда выберете нужную ячейку, замените значение и нажмите Enter.  
    ''',
    unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Upload your PDFs or image here and click on 'Process'",
    accept_multiple_files=True, type=['pdf', 'png', 'jpeg', 'jpg'])

# process uploaded data
if st.button("Process"):
    for uploaded_file in uploaded_files:
        name, extension = uploaded_file.name.split('.')

        if extension == 'pdf':
            # all tables in one pdf document merge into one table
            df = reader.read(uploaded_file, is_pdf=True)
        else:
            file_bytes = asarray(bytearray(uploaded_file.read()), dtype=uint8)
            opencv_image = imdecode(file_bytes, 1)
            df = reader.read(opencv_image, is_pdf=False)

        try:
            # if user upload two some file pandas throw exception ValueError when compare just processed file and
            # contained in session storage some file. If this happened, then just processed file will be ignored
            d = get_dict(name, df)
            if d not in st.session_state['table_list_of_dict']:
                st.session_state['table_list_of_dict'].append(d)
        except ValueError:
            pass
    # uploaded_files.clear()

# display processed file into expander list
for index, val in enumerate(st.session_state['table_list_of_dict']):
    name = val['name']
    with st.expander(label=name):
        df = val['DataFrame']
        new_df = st.data_editor(df)
        st.session_state['table_list_of_dict'][index]['DataFrame'] = new_df
        # custom download button. Because st.download_button don't fit here
        with st.form(key=f'my_form{index}', clear_on_submit=False):
            submit = st.form_submit_button('Download like excel', on_click=lambda: download_df(df))
