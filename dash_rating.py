import pandas as pd
import dash
import plotly.graph_objs as go
import dash_core_components as dcc
import dash_html_components as html
import pymysql
import plotly.express as px
from dash.dependencies import Input, Output

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
external_stylesheets = ['style.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Рейтинг опроса ПАО "РОССЕТИ КУБАНЬ"'
# 'rowCount': 3 , 'columnCount': 2

CURRENT_DATE_VCS = '2021-04-05'
FROM_DATE = '0000-00-00'
TO_DATE = '0000-00-00'
UNIQUE_DATE = []

style_color = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
colors = {
    'background': '#F0F8FF',
    'text': '#008080',
    'matrica': '#FF4500',
    'matricaSFSK': '#FF7F50',
    'title': '#2F4F4F'
}

db_connection = pymysql.connect(user='root', password='astra', host='localhost', database='vcs')
cursor = db_connection.cursor()
cursor.execute(f'SELECT DISTINCT(STR_TO_DATE(date_survey, "%Y-%m-%d")) AS survey FROM meter')

for val in cursor.fetchall():
    UNIQUE_DATE.append(val[0].strftime("%Y-%m-%d"))

filial = ['Матрица', 'Матрица SFSK', 'Матрица FSK', 'РиМ', 'МИР', 'Энергомера',
          'Квант(Миртек)', 'СЭТ(ПСЧ)', 'Меркурий', 'Альфа', 'ИТОГО', 'ИТОГО без FSK', 'Прошлая неделя']


def sql_qw(column, column2):
    answer = pd.read_sql(f'SELECT vf.small_name as Филиал, '
                         f'm.total_devices as Всего, '
                         f'm.respond as Опрашивается, '
                         f'm.percent * 100 as percent '
                         f'FROM meter m '
                         f'LEFT JOIN vcs_filial vf '
                         f'ON m.filial_id = vf.id '
                         f'WHERE m.device_id = {column} AND m.filial_id != 12 '
                         f'AND m.date_survey = "{column2}" '
                         f'ORDER by percent DESC', con=db_connection)
    return answer


def figure_total(column, column2):
    fig = px.bar(sql_qw(column, column2), x='Филиал', y=['Всего', 'Опрашивается'], text='value')
    fig.update_traces(textposition='outside')
    fig.update_layout(uniformtext_minsize=8,
                      uniformtext_mode='hide',
                      barmode='group',
                      plot_bgcolor=colors['background'],
                      paper_bgcolor=colors['background'],
                      font_color=colors['text'],
                      font_size=14
                      )
    return fig


def figure(column, column2):
    fig = px.bar(sql_qw(column, column2), x='Филиал', y='percent', text='percent', color=style_color[::])
    fig.update_traces(texttemplate='%{text:.3s} %', textposition='inside')
    fig.update_layout(uniformtext_minsize=8,
                      uniformtext_mode='hide',
                      plot_bgcolor=colors['background'],
                      paper_bgcolor=colors['background'],
                      font_color=colors['text'],
                      font_size=14
                      )
    return fig


# app.layout = html.Div(children=[
#     html.Div(className= 'row',
#              children=[
#                  html.Div(className='user_control'),
#                  html.Div(className='user-bar')
#              ])
# ])
app.layout = html.Div(
    style={
        'backgroundColor': colors['background']
    },

    children=[

        html.H1(
            children='Рейтинг опроса',
            style={
                'textAlign': 'center',
                'color': colors['title']
            }
        ),

        html.Div(id='dt', children=f'Рейтинг по филиалам в период с {FROM_DATE} по {TO_DATE}.',
                 style={
                     'textAlign': 'center',
                     'color': colors['text']
                 }
                 ),

        html.Div(children=[

            html.Label(
                children="Тип счетчика",
                style={'color': colors['title']}
            ),

            dcc.Dropdown(
                id='gis-column',
                options=[{'label': val, 'value': i} for i, val in enumerate(filial, 1)],
                value='1',
                style={'color': colors['title']}
            ),
        ],
            style={
                'width': '10%',
                'margin-left': '40px',
                'display': 'inline-block'
            }
        ),

        html.Div(children=[

            html.Label(
                children="Дата ВКС",
                style={'color': colors['title']}
            ),

            dcc.Dropdown(
                id='gis-column_date',
                options=[{'label': val, 'value': val} for val in sorted(UNIQUE_DATE)],
                value=CURRENT_DATE_VCS,
                style={'color': colors['title']}
            ),
        ],

            style={
                'width': '10%',
                'margin-left': '10px',
                'display': 'inline-block'
            }
        ),

        html.H2(
            children='Рейтинг по % опросу',
            style={
                'textAlign': 'center',
                'color': colors['title']
            }
        ),

        dcc.Graph(
            id='example-graph',
            figure=figure(1, CURRENT_DATE_VCS)
        ),

        html.H2(
            children='Рейтинг по количеству ПУ',
            style={
                'textAlign': 'center',
                'color': colors['title']
            }
        ),

        dcc.Graph(
            id='example-graph-2',
            figure=figure_total(1, CURRENT_DATE_VCS)
        )
    ])


@app.callback(
    [dash.dependencies.Output('example-graph-2', 'figure'),
     dash.dependencies.Output('example-graph', 'figure'),
     dash.dependencies.Output('dt', 'children')],
    [dash.dependencies.Input('gis-column', 'value'),
     dash.dependencies.Input('gis-column_date', 'value')])
def update_graph2(gis_column, gis_column_date):
    global FROM_DATE
    global TO_DATE
    cursor.execute(f'SELECT DISTINCT from_date, to_date FROM meter WHERE date_survey="{gis_column_date}"')
    tmp = []
    for item in cursor.fetchall():
        tmp.append(item[0].strftime("%d.%m.%Y"))
        tmp.append(item[1].strftime("%d.%m.%Y"))
    FROM_DATE = tmp[0]
    TO_DATE = tmp[1]
    return figure_total(gis_column, gis_column_date), figure(gis_column, gis_column_date), \
           f'Рейтинг по филиалам в период с {FROM_DATE} по {TO_DATE}.'


if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)

