# -*- coding: utf-8 -*-
"""streamlit_clinik _1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1oAAItFOT1OSYqWtfJB18EJkN0GmR8zp5
"""

import pandas as pd
import numpy as np
from datetime import datetime

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

#Model


# Компиляция модели


gender_pacient=st.selectbox('Выберите число',['М','Ж'])
age=st.number_input('Возраст', step=1, format="%i")
today=st.text_input('Дата обращения (формат : Год-месяц-день-Часы:Минуты:Секунды)')
come=st.text_input('Дата аписи (формат : Год-месяц-день)')
adress=st.text_input('Улица проживания пациента')
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
    
# Нажатие кнопки для формирования датафрейма
if st.button('Сформировать датафрейм'):
    names=['Gender','Age','ScheduledDay','AppointmentDay','Neighbourhood','Scholarship','Hipertension & Diabetes','Handcap','SMS_received','first_come']
    data=pd.DataFrame(dict(zip(names,[gender_pacient,age,today,come,adress,stolalrship,hronical,Handcap,sms,first_time])), index=[0])
    data = ready_data(data)
    
preprocessor = joblib.load('preprocessor.pkl')

df=pd.read_csv('KaggleV2-May-2016.csv')





st.write(data)
data=preprocessor.fit_transform(data)
# модель
st.write(data)
model = Sequential()
opt = Adam(learning_rate=0.001)
model.add(Dense(128, input_dim=data.shape[1], activation='relu'))
model.add(BatchNormalization())
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.4))
model.add(Dense(32, activation='relu'))
model.add(BatchNormalization())
model.add(Dense(1, activation='sigmoid'))
weights = {0: 1., 1: 4.}

model.load_weights('my_model_weights.h5')

predictions = model.predict(data)
st.write(f'Вероятность посещения пациента - {np.round(predictions)*100} %')

st.header('Часть 2')
st.subheader('Аналитика по данным по которым проходило обучение и выявление клиента который более склонен не посещать запись')
st.write('Для подготовки модели были взяты данные сторонней клиники')


fig, ax = plt.subplots()
ax.hist(df['No-show'], bins='auto')
plt.title('Распределение целевого признака')
# Отобразите гистограмму в Streamlit
st.pyplot(fig)
st.text('В данных сильный дисбаланс целевого показателя')

fig, ax = plt.subplots()
ax.hist(df['Diff'], bins='auto')
st.pyplot(fig)
plt.title('Разница между записью и посещением больницы');
plt.xlabel('Количество дней');

st.write('Построим матрицу кореляции для признаков наших данных')
st.text('Чем ближе к -1 то образная кореляция и ели ближе к +1 то положительная кореляция признаков')
plt.figure(figsize=(16,10))
sns.heatmap(df.corr(),annot=True)
plt.title('Матрица кореляции признаков')
st.pyplot()

st.write('Вывод : нас интересует признак No_show он отвечает за появление пациента он положительо корелирует с двумя данными признаками - Разница межу датами записи и приема и sms оповещением')

st.subheader('Построим признаки для выявления груп которые чаще не приходят по записи')

columns_to_exclude = ['AppointmentDay','ScheduledDay','PatientId','No-show']

for i in [i for i in df.columns if i not in columns_to_exclude]:
    pivot = df.pivot_table(index=i, columns='No-show', values='AppointmentDay', aggfunc='count')

    pivot['total'] = pivot[0] + pivot[1]
    pivot = pivot.dropna()
    pivot[0] = np.round(pivot[0] / pivot['total'] * 100, 2)
    pivot[1] = np.round(pivot[1] / pivot['total'] * 100, 2)
    mean = np.median(pivot[1])
    pivot.drop(columns='total', inplace=True)

    fig, ax = plt.subplots(figsize=(16,5))
    pivot.plot(kind='bar', ax=ax, title=f'Соотношение отказов в {i}', ylabel='%')
    ax.axhline(mean, color='r', linestyle='--')
    ax.text(-0.5, mean+1, f'Медиана: {mean:.2f}', color='r')

    st.pyplot(fig)

    bad = []
    for j in range(len(pivot)):
        if pivot.iloc[j][1] > mean+0.3:
            bad.append(pivot.index[j])

    if len(bad) > 1:
        fig, ax = plt.subplots(figsize=(10,5))
        pivot.loc[bad][1].plot(kind='bar', ax=ax, grid=True, title=f'В признаке {i} категории, которые имеют больше отказов')
        st.pyplot(fig)
    elif len(bad) == 1:
        st.write(f'В признаке {i} чаще отказываются в категории {bad}')

st.subheader('Вывод')

df['day_of_Scheduled'] = df['ScheduledDay'].dt.strftime("%j")
fig, ax = plt.subplots(figsize=(16,8))

df.loc[df['No-show']==0].pivot_table(index='day_of_Scheduled',values='No-show',aggfunc='count').plot(style='o-', ax=ax)
df.loc[df['No-show']==1].pivot_table(index='day_of_Scheduled',values='Age',aggfunc='count').plot(style='o-', ax=ax)

ax.grid(True)
ax.set_title('Гафик количества пропусков и поещений')
ax.legend(['Прешли','Пропустили'])

st.pyplot(fig)

st.subhead('Вывод')
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
plt.legend(['Прешли','Пропустили'])
plt.title('График процента пропусков и посещений')

# Показываем график в Streamlit
st.pyplot(fig)

df=df.drop('day_of_Scheduled',axis=1)

#3d

target=df['No-show']
features=df.drop(['No-show','ScheduledDay','AppointmentDay'],axis=1)
ordinal=OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=999999)
features=ordinal.fit_transform(features)
minmax=MinMaxScaler()
features_scaller=minmax.fit_transform(features)
features_pca['target']=target.reset_index(drop=True)

fig = go.Figure(data=[go.Scatter3d(
    x=features_pca[1],
    y=features_pca[2],
    z=features_pca[3],
    mode='markers',
    marker=dict(
        size=4,
        color=features_pca['target'],
        colorscale='Greys',
        opacity=0.9,
        colorbar=dict(title='Target')

    ),name='Data',showlegend=True
)])
# Настройка меток осей
fig.update_layout(scene=dict(
    xaxis_title='X',
    yaxis_title='Y',
    zaxis_title='Z'
))
fig.update_layout(
    legend=dict(
        title='3d Модель связи признаков',
        x=0.85,
        y=0.95
    )
)

# Отображение графика в Streamlit
st.plotly_chart(fig)

st.subheader('Вывод')
