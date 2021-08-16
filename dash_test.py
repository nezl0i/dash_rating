import pandas as pd
import dash
# import plotly.graph_objs as go
import dash_core_components as dcc
import dash_html_components as html
import pymysql
import plotly.express as px
from dash.dependencies import Input, Output
# import numpy as np

db_connection = pymysql.connect(user='root', password='astra', host='localhost', database='vcs')
cursor = db_connection.cursor()

filial = ['Матрица', 'Матрица SFSK', 'Матрица FSK', 'РиМ', 'МИР', 'Энергомера',
          'Квант(Миртек)', 'СЭТ(ПСЧ)', 'Меркурий', 'Альфа', 'ИТОГО', 'ИТОГО без FSK', 'Прошлая неделя']

CURRENT_DATE_VCS = '2021-04-05'
FROM_DATE = '00.00.0000'
TO_DATE = '00.00.0000'
UNIQUE_DATE = []
style_color = [1, ]

colors = {
    'background': '#F0F8FF',
    'text': '#008080',
    'matrica': '#FF4500',
    'matricaSFSK': '#FF7F50',
    'title': '#2F4F4F'
}

cursor.execute(f'SELECT DISTINCT(STR_TO_DATE(date_survey, "%Y-%m-%d")) AS survey FROM meter')

for val in cursor.fetchall():
    UNIQUE_DATE.append(val[0].strftime("%Y-%m-%d"))

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


def sql_qw(device_id, date_survey):
    frame = pd.read_sql(f'SELECT vf.small_name as Филиал, '
                        f'vf.full_name as ФЭС, '
                        f'm.total_devices as Всего, '
                        f'm.respond as Опрашивается, '
                        f'm.percent * 100 as "% опроса"'
                        f'FROM meter m '
                        f'LEFT JOIN vcs_filial vf '
                        f'ON m.filial_id = vf.id '
                        f'WHERE m.device_id = {device_id} AND m.filial_id != 12 '
                        f'AND m.date_survey = "{date_survey}" '
                        f'ORDER by percent DESC', con=db_connection)
    return frame


def sql_qw_avg(device_id, date_survey):
    frame = pd.read_sql(f'SELECT vf.small_name as Филиал, '
                        f'vf.full_name as ФЭС, '
                        f'm.total_devices as Всего, '
                        f'm.respond as Опрашивается, '
                        f'm.percent * 100 as "% опроса"'
                        f'FROM meter m '
                        f'LEFT JOIN vcs_filial vf '
                        f'ON m.filial_id = vf.id '
                        f'WHERE m.device_id = {device_id} AND m.filial_id = 12 '
                        f'AND m.date_survey = "{date_survey}" '
                        f'ORDER by percent DESC', con=db_connection)
    return frame


def set_color(y):
    return 'Red' if y <= 95.0 else 'green'


def create_percent_figure(device_id, date_survey):
    array = sql_qw(device_id, date_survey)
    figure = px.bar(array, x='Филиал', y='% опроса',
                    text='% опроса',
                    height=600,
                    title="Рейтинг по % опроса")
    figure.update_traces(texttemplate='%{text:.3s} %', textposition='inside',
                         marker=dict(color=list(map(set_color, array.to_dict('list')['% опроса']))),
                         hovertemplate=None)
    figure.update_layout(uniformtext_minsize=8,
                         uniformtext_mode='hide',
                         plot_bgcolor=colors['background'],
                         paper_bgcolor=colors['background'],
                         font_color=colors['text'],
                         font_size=12
                         )
    return figure


def create_total_percent_figure(device_id, date_survey):
    array = sql_qw_avg(device_id, date_survey)
    figure = px.bar(array, x='% опроса', y=['', ],
                    text='% опроса',
                    orientation='h',
                    height=250,
                    title=f'Общий % опроса по филиалам')
    figure.update_traces(texttemplate='%{text:.3s} %', textposition='inside',
                         marker_color='rgb(158,202,225)',
                         marker_line_color='rgb(8,48,107)',
                         marker_line_width=1.5,
                         opacity=0.6)
    figure.update_layout(uniformtext_minsize=8,
                         uniformtext_mode='hide',
                         barmode='group',
                         plot_bgcolor=colors['background'],
                         paper_bgcolor=colors['background'],
                         font_color=colors['text'],
                         font_size=12
                         )
    return figure


def create_device_figure(device_id, date_survey):
    figure = px.bar(sql_qw(device_id, date_survey), x='Филиал', y=['Всего', 'Опрашивается'], text='value',
                    title="Рейтинг по количеству ПУ",
                    height=600,
                    hover_name='ФЭС',
                    hover_data=['% опроса']
                    )
    figure.update_traces(textposition='outside')
    figure.update_layout(uniformtext_minsize=8,
                         uniformtext_mode='hide',
                         barmode='group',
                         plot_bgcolor=colors['background'],
                         paper_bgcolor=colors['background'],
                         font_color=colors['text'],
                         font_size=12

                         )
    return figure


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Рейтинг опроса"

app.layout = html.Div(
    children=[
        # ==========================================
        #               Create header              #
        # ==========================================
        html.Div(
            children=[
                html.P(children="📊", className="header-emoji"),
                html.H1(
                    children="ПАО \"РОССЕТИ КУБАНЬ\"", className="header-title"
                ),
                html.P(
                    id='period',
                    children=f'Рейтинг опроса интеллектуальных приборов учета'
                             f' программного комплекса ИВК "ПИРАМИДА-СЕТИ"'
                             f' за период с {FROM_DATE} по {TO_DATE}',
                    className="header-description",
                ),
            ],
            className="header",
        ),
        # ==========================================
        #     Create dropdown "Наименование ПУ"    #
        # ==========================================
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Наименование ПУ", className="menu-title"),
                        dcc.Dropdown(
                            id="devices",
                            options=[
                                {"label": val, "value": i}
                                for i, val in enumerate(filial, 1)
                            ],
                            value=11,
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                # ==========================================
                #      Create dropdown "Дата отчета"       #
                # ==========================================
                html.Div(
                    children=[
                        html.Div(children="Дата отчета", className="menu-title"),
                        dcc.Dropdown(
                            id="date_vcs",
                            options=[
                                {"label": val, "value": val}
                                for val in sorted(UNIQUE_DATE)
                            ],
                            value=CURRENT_DATE_VCS,
                            clearable=False,
                            searchable=False,
                            className="dropdown",
                        ),
                    ],
                ),
                # ==========================================
                #           Create DataPicker              #
                # ==========================================
                # html.Div(
                #     children=[
                #         html.Div(
                #             children="Отчетный период",
                #             className="menu-title"
                #         ),
                #         dcc.DatePickerRange(
                #             id="date-range",
                #             min_date_allowed=FROM_DATE,
                #             max_date_allowed=data.Date.max().date(),
                #             start_date=data.Date.min().date(),
                #             end_date=data.Date.max().date(),
                #         ),
                #     ]
                # ),
            ],
            className="menu",
        ),
        # ==========================================
        #          График "Процент опроса"         #
        # ==========================================
        html.Div(  # Start DIV Graph
            children=[  # Start children
                html.Div(
                    children=dcc.Graph(
                        id="percent_rating",
                        figure=create_percent_figure(11, CURRENT_DATE_VCS),
                        # config={"displayModeBar": False},
                    ),
                    className="percent",
                ),
            ],  # End Children
            className="graph_percent",
        ),  # End DIV Graph

        html.Div(  # Start DIV Graph
            children=[  # Start children
                html.Div(
                    children=dcc.Graph(
                        id="total_percent_rating",
                        figure=create_total_percent_figure(11, CURRENT_DATE_VCS),
                        # config={"displayModeBar": False},
                    ),
                    className="percent",
                ),
            ],  # End Children
            className="graph_percent",
        ),  # End DIV Graph
        # ==========================================
        #     График "Количество опрашиваемых ПУ"  #
        # ==========================================
        html.Div(  # Start DIV Graph
            children=[  # Start children
                html.Div(
                    children=dcc.Graph(
                        id="devices_rating",
                        figure=create_device_figure(11, CURRENT_DATE_VCS),
                        # config={"displayModeBar": False},
                    ),
                    className="device",
                ),
            ],  # End Children
            className="graph_device",
        ),  # End DIV Graph
    ]
)


@app.callback(
    [
        Output("period", "children"),
        Output("percent_rating", "figure"),
        Output("devices_rating", "figure"),
        Output("total_percent_rating", "figure")
    ],
    [
        Input("date_vcs", "value"),
        Input("devices", "value"),
        # Input("date-range", "start_date"),
        # Input("date-range", "end_date"),
    ],
)
def update_charts(date_vcs, devices):
    global FROM_DATE
    global TO_DATE
    cursor.execute(f'SELECT DISTINCT from_date, to_date FROM meter WHERE date_survey="{date_vcs}"')
    tmp = []

    for item in cursor.fetchall():
        tmp.append(item[0].strftime("%d.%m.%Y"))
        tmp.append(item[1].strftime("%d.%m.%Y"))
    FROM_DATE = tmp[0]
    TO_DATE = tmp[1]
    output_period = (f'Рейтинг опроса интеллектуальных приборов учета'
                     f' программного комплекса ИВК "ПИРАМИДА-СЕТИ"'
                     f' за период с {FROM_DATE} по {TO_DATE}',
                     )

    return (
            output_period,
            create_percent_figure(devices, date_vcs),
            create_device_figure(devices, date_vcs),
            create_total_percent_figure(devices, date_vcs)
    )


if __name__ == "__main__":
    app.run_server(debug=True,
                   host='127.0.0.1')

#
# mask = (
#         (data.region == region)
#         & (data.type == avocado_type)
#         & (data.Date >= start_date)
#         & (data.Date <= end_date)
# )
# filtered_data = data.loc[mask, :]
# price_chart_figure = {
#     "data": [
#         {
#             "x": filtered_data["Date"],
#             "y": filtered_data["AveragePrice"],
#             "type": "lines",
#             "hovertemplate": "$%{y:.2f}<extra></extra>",
#         },
#     ],
#     "layout": {
#         "title": {
#             "text": "Average Price of Avocados",
#             "x": 0.05,
#             "xanchor": "left",
#         },
#         "xaxis": {"fixedrange": True},
#         "yaxis": {"tickprefix": "$", "fixedrange": True},
#         "colorway": ["#17B897"],
#     },
# }
#
# volume_chart_figure = {
#     "data": [
#         {
#             "x": filtered_data["Date"],
#             "y": filtered_data["Total Volume"],
#             "type": "lines",
#         },
#     ],
#     "layout": {
#         "title": {"text": "Avocados Sold", "x": 0.05, "xanchor": "left"},
#         "xaxis": {"fixedrange": True},
#         "yaxis": {"fixedrange": True},
#         "colorway": ["#E12D39"],
#     },
# }
