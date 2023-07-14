# -*- coding: utf-8 -*-
"""streamlit_clinik _1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1oAAItFOT1OSYqWtfJB18EJkN0GmR8zp5
"""

import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib as mpl
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler,OrdinalEncoder,StandardScaler,OneHotEncoder
from sklearn.compose import make_column_transformer,ColumnTransformer
import plotly.graph_objects as go
from imblearn.under_sampling import EditedNearestNeighbours
from sklearn.metrics import f1_score,roc_auc_score,precision_score,accuracy_score,confusion_matrix
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout,BatchNormalization
from tensorflow.keras.optimizers import Adam
import joblib
import streamlit as st
import plotly.graph_objects as go
mpl.rcParams['figure.max_open_warning'] = 30
st.title('Предсказание посещения поликлиники')

st.header('Введение')
st.write('''
В современном мире оптимизация работы медицинских учреждений становится все более важной задачей. 
Одной из ключевых проблем, с которой сталкиваются поликлиники, является непредсказуемость посещения пациентами назначенных им визитов.
Неявки пациентов могут приводить к неэффективному использованию ресурсов, задержкам в расписании и увеличению затрат. 
Чтобы решить эту проблему, в рамках данного проекта была разработана модель машинного обучения, которая позволяет предсказывать вероятность посещения поликлиники пациентом.
''')

st.header('Цель проекта')
st.write('''
Целью проекта является создание модели, которая, основываясь на исторических данных о пациентах, сможет предсказывать, придет ли пациент на назначенный визит или нет. 
Для достижения этой цели была использована база данных бразильской поликлиники, содержащая информацию о поле пациента, возрасте, дате обращения, дате записи, районе проживания и других факторах, которые могут влиять на вероятность посещения.
На основе этой базы данных была создана нейронная сеть, обученная предсказывать вероятность посещения поликлиники.
''')

st.header('Структура проекта')
st.write('''
Проект разделен на две основные части. Первая часть предоставляет пользователю возможность ввести данные нового пациента, после чего модель прогнозирует вероятность его посещения поликлиники. 
Это позволяет планировать ресурсы и расписание, и предупреждать возможные непришедшие пациенты заранее.
Вторая часть проекта посвящена анализу данных и выявлению факторов, влияющих на вероятность непосещения поликлиники. 
Модель позволяет определить категории пациентов, склонных к непосещению, что помогает лучше понять причины их отсутствия и принять соответствующие меры.
Кроме того, проект обсуждает полезность модели и возможные направления ее дальнейшего развития.
''')

st.header('Заключение')
st.write('''
Разработанная модель предсказания посещения поликлиники является полезным инструментом для оптимизации работы медицинских учреждений. 
Она позволяет предсказывать вероятность неприхода пациента и принимать соответствующие меры заранее. 
Кроме того, анализ данных помогает лучше понять факторы, влияющие на непосещение поликлиники, и предпринимать действия для улучшения ситуации.
Данный проект представляет только начало и может быть дальше развит и улучшен с учетом новых данных и методов машинного обучения.
''')

df=pd.read_csv('df.csv',index_col=0)

st.subheader('Пожалуйста введите данные о записи')

gender_pacient=st.selectbox('Выберите пол',['М','Ж'])
age=st.number_input('Возраст', step=1, format="%i")
today=st.text_input('Дата обращения (формат : Год-месяц-день-Часы:Минуты:Секунды)')
come=st.text_input('Дата записи (формат : Год-месяц-день)')
place={i for i in df['Neighbourhood']}
adress=st.selectbox('Выберите район проживания пациента',place)
stolalrship=st.selectbox('У пациента есть мед страховка ',['Да' , 'Нет'])
hronical=st.selectbox('У пациента есть хроничекие заболевания',['Да' , 'Нет'])
Handcap=st.selectbox('Есть ли инвалидность и если есть то какая группа, если нету указать 0',[0,1,2,3,4])
sms=st.selectbox('Есть ли у пациента sms оповещение',['Да','Нет'])
first_time=st.selectbox('Пациент впервые обратился в клинику',['Да','Нет'])

def ready_data(data):
    # Заполнение пропущенных значений нулями
    data = data.fillna(0)

    data['Gender'] = np.where(data['Gender']=='М', 1, 0)
    data['first_come'] = np.where(data['first_come']=='Нет', 1, 0)
    data['Scholarship'] = np.where(data['Scholarship']=='Да', 1, 0)
    data['SMS_received'] = np.where(data['SMS_received']=='Да', 1, 0)
    data['Hipertension & Diabetes'] = np.where(data['Hipertension & Diabetes']=='Да', 1, 0)

    data['AppointmentDay'] = pd.to_datetime(data['AppointmentDay'], format='%Y-%m-%d')
    data['ScheduledDay'] = pd.to_datetime(data['ScheduledDay'], format="%Y-%m-%d-%H:%M:%S")

    data['Day_scheduled'] = data['ScheduledDay'].dt.weekday
    data['Day_Appointment'] = data['AppointmentDay'].dt.weekday
    data['Hours_Scheduled'] = data['ScheduledDay'].dt.hour

    data['Diff'] = (data['AppointmentDay'] - data['ScheduledDay']).dt.days
    data = data.drop(['AppointmentDay','ScheduledDay'],axis=1)

    return data
    
@st.cache_data()
def prepocessor(data):
    
    preprocessor = ColumnTransformer(
    transformers=[
        ('num', MinMaxScaler(), ['Age', 'Diff']),
        
        ('ord', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1), ['Day_scheduled','Neighbourhood', 'Day_Appointment', 'Hours_Scheduled'])
    ],
        remainder='passthrough')
    df=pd.read_csv('df.csv',index_col=0)
    target=df['No-show']
    features=df.drop(['No-show','ScheduledDay','AppointmentDay','Alcoholism'],axis=1)
    preprocessor.fit(features)
    return preprocessor 

# модель

model = Sequential()
opt = Adam(learning_rate=0.001)
model.add(Dense(128, input_dim=12, activation='relu'))
model.add(BatchNormalization())
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.4))
model.add(Dense(32, activation='tanh'))
model.add(BatchNormalization())
model.add(Dense(1, activation='sigmoid'))
weights = {0: 1., 1: 4.}

model.load_weights('my_model_weights.h5')

# Нажатие кнопки для формирования датафрейма
if st.button('Записать пациента', key='predict'):
    names = ['Gender', 'Age', 'ScheduledDay', 'AppointmentDay', 'Neighbourhood', 'Scholarship', 'Hipertension & Diabetes', 'Handcap', 'SMS_received', 'first_come']
    data = pd.DataFrame(dict(zip(names, [gender_pacient, age, today, come, adress, stolalrship, hronical, Handcap, sms, first_time])), index=[0])
    data = ready_data(data)
    preprocessor = prepocessor(data)
    data_transformed = preprocessor.transform(data)
    predictions = model.predict(data_transformed)
    prediction = predictions[0][0]
    rounded_prediction = round(prediction * 100, 2)
    st.write(f'Вероятность посещения пациента - {rounded_prediction} %')


if st.button('Показать аналитику по данным', key='analyse'):
    st.title('Часть 2: Анализ данных и визуализация')

    st.header('Введение')
    st.write('''
    Во второй части нашего проекта мы проведем анализ данных, используя различные методы визуализации. 
    Мы рассмотрим каждый признак в отдельности, исследуем закономерности и взаимосвязи между ними. 
    Дополнительно, мы проанализируем временной ряд для выявления трендов и пиков пропусков данных. 
    Наконец, мы построим трехмерную визуализацию, отображающую распределение признаков.
    ''')
    
    st.header('Анализ каждого признака')
    st.write('''
    Мы начнем с анализа каждого признака из нашей базы данных. 
    Для этого мы построим соответствующие графики, которые позволят нам лучше понять распределение данных и выявить интересные особенности. 
    Мы рассмотрим пол пациента, возраст, дату обращения, дату записи, район проживания и другие признаки, содержащиеся в нашем наборе данных.
    ''')
    
    # Здесь вы можете добавить код для визуализации и анализа данных каждого признака
    
    st.header('Анализ временного ряда')
    st.write('''
    Особое внимание будет уделено временному ряду данных. 
    Мы построим график, отображающий изменение количества пропусков данных во времени. 
    Это позволит нам выявить закономерности и тренды, связанные с пропусками, и поможет лучше понять, в какие периоды наблюдается наибольшее количество пропусков.
    ''')
    
    # Здесь вы можете добавить код для анализа временного ряда
    
    st.header('Трехмерная визуализация')
    st.write('''
    В заключение, мы создадим трехмерную визуализацию, которая поможет нам представить распределение признаков в трехмерном масштабе. 
    Это позволит нам визуально исследовать связи между различными признаками и обнаружить возможные взаимосвязи или паттерны, которые могут быть невидимы на двумерных графиках.''')
    
    
    fig, ax = plt.subplots()
    ax.hist(df['No-show'], bins='auto')
    plt.title('Распределение целевого признака (Посещения/Пропуски)')
    # Отобразите гистограмму в Streamlit
    st.pyplot(fig)
    st.write('Изначально в данных присутствовал сильный дисбаланс целевого признака была реализован метод SMOTE для того что бы решить эту проблему')
    
    fig, ax = plt.subplots()
    ax.hist(df['Diff'], bins='auto')
    
    plt.title('Разница между записью и посещением больницы')
    plt.xlabel('Количество дней')
    st.pyplot(fig)
    st.write('Можно увидеть что люди чаще записываються в пределах 5 дней.')
    
    st.write('Построим матрицу кореляции для наших признаков')
    st.write('-1<=отрицательная кореляция, положительная кореляция =>+1')
    
    # Define columns
    col1, col2 = st.columns((0.7, 0.3))
    
    # Draw the plot in the first column
    with col1:
        fig, ax = plt.subplots(figsize=(16,10))
        sns.heatmap(df[[i for i in df.columns if i not in ['AppointmentDay', 'ScheduledDay','Neighbourhood']]].corr(), annot=True, ax=ax)
        ax.set_title('Матрица кореляции признаков')
        st.pyplot(fig)
    
    # Write the text in the second column
    with col2:
        st.write('Вывод : нас интересует признак No_show он отвечает за появление пациента, он положительно коррелирует с двумя данными признаками - Разница межу датами записи и приема и sms оповещением')
    
    st.subheader('Построим признаки для выявления групп которые чаще не приходят по записи')
    
    columns_to_exclude = ['AppointmentDay','ScheduledDay','PatientId','No-show']
    output_text = {
        'Gender': 'Мы не видим сильных различий между посещением и пропусками в зависимости от пола',
        'Age': 'Мы можем увидеть, что более молодые люди склонны к пропускам записи, основной возраст до 18 лет. Другая группа людей от 18 до 30 также превышает медианное значение, и мы видим, что чем старше пациенты становятся, тем меньше у них пропусков. Все группы, которые превышают порог, можно посмотреть в колонке Age 2.1.',
        'Neighbourhood': 'Выявлены три района, у которых больше всего пропусков. С остальными районами можно ознакомиться в следующем графике.',
        'Scholarship': 'Мы видим, что люди с медицинской страховкой чаще пропускают приемы.',
        'Handcap':'Люди с 3 и 4 группой инвалидности так же склонны к пропускам записи',
        'SMS_received':'Значительно превышает процент пропусков у людей которые получают смс оповещение',
        'first_come':'Люди которые впервые бывают в поликлинике чаще не приходят по записи',
        'Day_Appointment':'Люди которые записаны на пятницу или субботу чаще пропускают запись',
        'Hours_Scheduled':'Обычно люди которые записываются по 20.00 пропускают запись ,со всеми часами можно ознакомиться в таблице ниже',
        'Diff':'Если люди записываются за две недели они попадают в группу риска ну и чем позже тем риск становится больше',
        'Alcoholism':'Каждая группа не превысила порог .',
        'Day_scheduled': 'Люди которые совершали запись в пятницу меньше всех не приходят по записи.',
        'Hipertension & Diabetes':'Люди без хронических заболеваний чаще пропускают приемы,но это сильно коррелирует с возрастом пациентов'
    
    }
    
    plot_check = {}
    
    for i in [i for i in df.columns if i not in columns_to_exclude]:
        pivot = df.pivot_table(index=i, columns='No-show', values='AppointmentDay', aggfunc='count')
    
        pivot['total'] = pivot[0] + pivot[1]
        pivot = pivot.dropna()
        pivot[0] = np.round(pivot[0] / pivot['total'] * 100, 2)
        pivot[1] = np.round(pivot[1] / pivot['total'] * 100, 2)
        mean = np.median(pivot[1])
        pivot.drop(columns='total', inplace=True)
    
        fig, ax = plt.subplots(figsize=(20,8))
        pivot.plot(kind='bar', ax=ax, title=f'Соотношение отказов в {i}', ylabel='%')
        ax.axhline(mean, color='r', linestyle='--')
        ax.text(-0.5, mean+1, f'Медиана: {mean:.2f}', color='r')
    
        col1, col2 = st.columns((0.8, 0.2))
    
        with col1:
            st.pyplot(fig)
            
        with col2:
            if plot_check.get(i, False) == False:
                st.write(f"График: {i}")
                # Write the output text for this plot
                st.write(f"Вывод: {output_text.get(i, '')}")
                plot_check[i] = True
    
        bad = []
        for j in range(len(pivot)):
            if pivot.iloc[j][1] > mean+0.3:
                bad.append(pivot.index[j])
    
        if len(bad) > 1:
            fig, ax = plt.subplots(figsize=(15,7))
            pivot.loc[bad][1].plot(kind='bar', ax=ax, grid=True, title=f'В признаке {i} категории, которые имеют больше отказов')
            with col1:
                st.pyplot(fig)
            with col2:
                if plot_check.get(i + '2.1', False) == False:
                    st.write(f"График: {i} - 2.1")
                    plot_check[i + '2.1'] = True
        elif len(bad) == 1:
            with col2:
    
                # Write the output text for this plot
                if plot_check.get(i, False) == False:
                    st.write(f"Вывод: {output_text.get(i, '')}")
                    plot_check[i] = True
    
    st.subheader('Вывод')
    st.write("Исходя из предоставленных данных, можно сделать следующий вывод:")
    st.write("Чаще всего не приходят на прием молодые люди, проживающие в определенных районах. Они часто являются новыми пациентами в поликлинике, обладают медицинской страховкой и не имеют хронических заболеваний.")
    st.write("Интересно отметить, что записи после 20 часов вечера обычно оказываются ложными.")
    st.write("Также стоит отметить, что пациенты, записанные на прием в пятницу или субботу, чаще пропускают прием, однако те, кто записался на пятницу, на самом деле чаще всего приходят по записи.")
    st.write("Кроме того, риск пропуска приема увеличивается, если пациент записывается на прием позднее, чем через 14 дней.")
    
    
    

    df['ScheduledDay'] = pd.to_datetime(df['ScheduledDay'])
    df['day_of_Scheduled'] = df['ScheduledDay'].dt.strftime("%j")

    # Создание DataFrame'ов для графиков
    came = df.loc[df['No-show']==0].pivot_table(index='day_of_Scheduled',values='No-show',aggfunc='count')
    not_came = df.loc[df['No-show']==1].pivot_table(index='day_of_Scheduled',values='Age',aggfunc='count')

    # Создание графиков
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=came.index, y=came['No-show'], mode='lines', name='Пришли'))
    fig.add_trace(go.Scatter(x=not_came.index, y=not_came['Age'], mode='lines', name='Пропустили'))

    fig.update_layout(title='График количества пропусков и посещений',
                      xaxis_title='День',
                      yaxis_title='Количество',
                      legend_title='Статус',
                      hovermode='x unified')

    # Отображение графика в Streamlit
    st.plotly_chart(fig)
    
    total = df.pivot_table(index='day_of_Scheduled',values='No-show',aggfunc='count')
    
    # Получаем количество записей для каждого дня для тех, кто пришел и пропустил
    attended = df.loc[df['No-show']==0].pivot_table(index='day_of_Scheduled',values='No-show',aggfunc='count')
    missed = df.loc[df['No-show']==1].pivot_table(index='day_of_Scheduled',values='No-show',aggfunc='count')
    
    # Нормализация данных до процентов
    attended_percentage = attended / total * 100
    missed_percentage = missed / total * 100
    
    # Создаем фигуру и оси используя matplotlib
    fig, ax = plt.subplots(figsize=(16,8))
    
    # Построение графиков
    attended_percentage.plot.bar(ax=ax,grid=True)
    missed_percentage.plot.bar(ax=ax,grid=True,color='r')
    plt.xlabel('Дни в году')
    plt.legend(['Пришли','Пропустили'])
    plt.title('График процента пропусков и посещений')
    
    # Показываем график в Streamlit
    st.pyplot(fig)
    
    df=df.drop('day_of_Scheduled',axis=1)
    st.markdown("## Вывод")
    st.markdown("Из анализа данных видно, что в начале периода наблюдались **пропуски в посещении** в поликлинику в том же количестве, что и активные записи, что отрицательно сказывалось на результативности работы. Однако, во второй половине периода удалось значительно снизить пропуски до уровня в **среднем 20%** от общего числа записей.")
    st.markdown("Учитывая, что пропуски могут быть обусловлены факторами, не учтенными в наших данных, и с учетом точности модели в **75%**, мы можем дальше сократить пропуски до уровня около **10%**. Это может иметь значительное положительное влияние на работу поликлиники, позволяя составлять более точное расписание и эффективно управлять финансовыми ресурсами.")
    #3d
    

    @st.cache_data()
    def get_pca_data():
        df = pd.read_csv('df.csv',index_col=0)
        target=df['No-show']
        features=df.drop(['No-show','ScheduledDay','AppointmentDay'],axis=1)
        ordinal=OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=999999)
        features=ordinal.fit_transform(features)
        minmax=MinMaxScaler()
        features_scaller=minmax.fit_transform(features)
        pca=PCA(3)
        features_pca=pd.DataFrame(pca.fit_transform(features_scaller),columns=[1,2,3])
        features_pca['target']=target.reset_index(drop=True)
        return features_pca


    st.markdown("## Вывод")
    st.markdown("После сокращения размера нашего данных с использованием метода **Главных компонент** мы обнаружили **8 четко определенных групп**. Эти группы представляют собой ценную информацию, которую мы можем использовать для определения внутренних зависимостей и разработки специфических предложений. Такой подход позволит нам улучшить понимание наших клиентов и принимать меры, которые приведут к положительным результатам и увеличению прибыли.")
    
    st.markdown("Кроме того, мы заметили, что данные о **пропусках и посещениях** сильно переплетены друг с другом. Это указывает на важность дальнейшей работы в этом направлении для повышения процента отказов. Аналитика и исследования в этой области могут помочь нам выявить факторы, влияющие на эту взаимосвязь, и разработать эффективные стратегии для улучшения эффективности нашей работы и увеличения процента отказов.")
    
    st.markdown("С учетом этих результатов, мы видим огромный потенциал для развития нашей поликлиники. Путем дальнейшего анализа данных и применения новых методов машинного обучения мы можем сделать более точные прогнозы, предлагать персонализированные решения и существенно улучшить удовлетворенность и результативность наших пациентов.")


    st.markdown("## Общий итог")
    st.markdown("Разработанная модель предоставляет возможность упростить работу администратора поликлиники, оптимизировать расписание врачей и сократить затраты. Она открывает дальнейшие возможности для развития, такие как интеграция данных о расписании для более логичной записи пациентов, создание модели временных рядов для прогнозирования будущих записей и пропусков, а также доработка модели для достижения более высокого качества с использованием новых данных.")
    
    st.markdown("В итоге, использование данной модели позволяет оптимизировать работу поликлиники, улучшить эффективность и экономию ресурсов. Это открывает новые перспективы для повышения качества обслуживания пациентов и создания более эффективной и прогрессивной поликлиники.")
if st.checkbox('Показать 3D график'):
        features_pca=get_pca_data()
        data = [
            go.Scatter3d(
                x=features_pca[1],
                y=features_pca[2],
                z=features_pca[3],
                mode='markers',
                marker=dict(
                    size=4,
                    color=features_pca['target'],
                    colorscale='Viridis',
                    opacity=0.9,
                    colorbar=dict(title='Target')
                ),
                name='Data',
                showlegend=True
            )
        ]
        
        # Создание графика
        fig = go.Figure(data=data)
        
        # Настройка меток осей
        fig.update_layout(scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z'
        ))
        
        # Настройка легенды
        fig.update_layout(
            legend=dict(
                title='3D Модель связи признаков',
                x=0.85,
                y=0.95
            )
        )
        
        # Отображение графика в Streamlit
        st.plotly_chart(fig)
