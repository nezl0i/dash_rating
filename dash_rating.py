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
# app = dash.Dash()
#
# df = pd.read_csv(
#     'https://gist.githubusercontent.com/chriddyp/'
#     'cb5392c35661370d95f300086accea51/raw/'
#     '8e0768211f6b747c0db42a9ce9a0937dafcbd8b2/'
#     'indicators.csv')
#
# available_indicators = df['Indicator Name'].unique()
#
# app.layout = html.Div([
#     html.Div([
#
#         html.Div([
#             dcc.Dropdown(
#                 id='crossfilter-xaxis-column',
#                 options=[{'label': i, 'value': i} for i in available_indicators],
#                 value='Fertility rate, total (births per woman)'
#             ),
#             dcc.RadioItems(
#                 id='crossfilter-xaxis-type',
#                 options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
#                 value='Linear',
#                 labelStyle={'display': 'inline-block'}
#             )
#         ],
#         style={'width': '49%', 'display': 'inline-block'}),
#
#         html.Div([
#             dcc.Dropdown(
#                 id='crossfilter-yaxis-column',
#                 options=[{'label': i, 'value': i} for i in available_indicators],
#                 value='Life expectancy at birth, total (years)'
#             ),
#             dcc.RadioItems(
#                 id='crossfilter-yaxis-type',
#                 options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
#                 value='Linear',
#                 labelStyle={'display': 'inline-block'}
#             )
#         ], style={'width': '49%', 'float': 'right', 'display': 'inline-block'})
#     ], style={
#         'borderBottom': 'thin lightgrey solid',
#         'backgroundColor': 'rgb(250, 250, 250)',
#         'padding': '10px 5px'
#     }),
#
#     html.Div([
#         dcc.Graph(
#             id='crossfilter-indicator-scatter',
#             hoverData={'points': [{'customdata': 'Japan'}]}
#         )
#     ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
#     html.Div([
#         dcc.Graph(id='x-time-series'),
#         dcc.Graph(id='y-time-series'),
#     ], style={'display': 'inline-block', 'width': '49%'}),
#
#     html.Div(dcc.Slider(
#         id='crossfilter-year--slider',
#         min=df['Year'].min(),
#         max=df['Year'].max(),
#         value=df['Year'].max(),
#         step=None,
#         marks={str(year): str(year) for year in df['Year'].unique()}
#     ), style={'width': '49%', 'padding': '0px 20px 20px 20px'})
# ])
#
# @app.callback(
#     dash.dependencies.Output('crossfilter-indicator-scatter', 'figure'),
#     [dash.dependencies.Input('crossfilter-xaxis-column', 'value'),
#      dash.dependencies.Input('crossfilter-yaxis-column', 'value'),
#      dash.dependencies.Input('crossfilter-xaxis-type', 'value'),
#      dash.dependencies.Input('crossfilter-yaxis-type', 'value'),
#      dash.dependencies.Input('crossfilter-year--slider', 'value')])
# def update_graph(xaxis_column_name, yaxis_column_name,
#                  xaxis_type, yaxis_type,
#                  year_value):
#     dff = df[df['Year'] == year_value]
#
#     return {
#         'data': [go.Scatter(
#             x=dff[dff['Indicator Name'] == xaxis_column_name]['Value'],
#             y=dff[dff['Indicator Name'] == yaxis_column_name]['Value'],
#             text=dff[dff['Indicator Name'] == yaxis_column_name]['Country Name'],
#             customdata=dff[dff['Indicator Name'] == yaxis_column_name]['Country Name'],
#             mode='markers',
#             marker={
#                 'size': 15,
#                 'opacity': 0.5,
#                 'line': {'width': 0.5, 'color': 'white'}
#             }
#         )],
#         'layout': go.Layout(
#             xaxis={
#                 'title': xaxis_column_name,
#                 'type': 'linear' if xaxis_type == 'Linear' else 'log'
#             },
#             yaxis={
#                 'title': yaxis_column_name,
#                 'type': 'linear' if yaxis_type == 'Linear' else 'log'
#             },
#             margin={'l': 40, 'b': 30, 't': 10, 'r': 0},
#             height=450,
#             hovermode='closest'
#         )
#     }
#
# def create_time_series(dff, axis_type, title):
#     return {
#         'data': [go.Scatter(
#             x=dff['Year'],
#             y=dff['Value'],
#             mode='lines+markers'
#         )],
#         'layout': {
#             'height': 225,
#             'margin': {'l': 20, 'b': 30, 'r': 10, 't': 10},
#             'annotations': [{
#                 'x': 0, 'y': 0.85, 'xanchor': 'left', 'yanchor': 'bottom',
#                 'xref': 'paper', 'yref': 'paper', 'showarrow': False,
#                 'align': 'left', 'bgcolor': 'rgba(255, 255, 255, 0.5)',
#                 'text': title
#             }],
#             'yaxis': {'type': 'linear' if axis_type == 'Linear' else 'log'},
#             'xaxis': {'showgrid': False}
#         }
#     }
#
# @app.callback(
#     dash.dependencies.Output('x-time-series', 'figure'),
#     [dash.dependencies.Input('crossfilter-indicator-scatter', 'hoverData'),
#      dash.dependencies.Input('crossfilter-xaxis-column', 'value'),
#      dash.dependencies.Input('crossfilter-xaxis-type', 'value')])
# def update_y_timeseries(hoverData, xaxis_column_name, axis_type):
#     country_name = hoverData['points'][0]['customdata']
#     dff = df[df['Country Name'] == country_name]
#     dff = dff[dff['Indicator Name'] == xaxis_column_name]
#     title = '<b>{}</b><br>{}'.format(country_name, xaxis_column_name)
#     return create_time_series(dff, axis_type, title)
#
# @app.callback(
#     dash.dependencies.Output('y-time-series', 'figure'),
#     [dash.dependencies.Input('crossfilter-indicator-scatter', 'hoverData'),
#      dash.dependencies.Input('crossfilter-yaxis-column', 'value'),
#      dash.dependencies.Input('crossfilter-yaxis-type', 'value')])
# def update_x_timeseries(hoverData, yaxis_column_name, axis_type):
#     dff = df[df['Country Name'] == hoverData['points'][0]['customdata']]
#     dff = dff[dff['Indicator Name'] == yaxis_column_name]
#     return create_time_series(dff, axis_type, yaxis_column_name)
#
# app.css.append_css({
#     'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
# })
#
# if __name__ == '__main__':
#     app.run_server()
