import dash
from dash.dependencies import Output, Event, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import plotly.graph_objs as go
from collections import deque
import sqlite3
import pandas as pd
import time


POS_NEG_NEUT=0.1

app_colors = {
    'background': '#0C0F0A',
    'text': '#0000FF',
    'blue':'#0000FF',
    'sentiment-plot':'#41EAD4',
    'volume-bar':'#FBFC74',
    'someothercolor':'#FF206E',
}

#gives layout to app
app = dash.Dash(__name__)
app.layout = html.Div(
    [   html.H2('Interactive Twitter Sentiment',style={'color':app_colors['blue']}),
        html.H3('Search:', style={'color':app_colors['text']}),
        dcc.Input(id='sentiment_term', value='india', type='text',style={'color':app_colors['someothercolor']}),
        # dcc.Graph(id='liveGraph', animate=True),
        # dcc.Graph(id='longTerm', animate=False),
        html.Div(className='row', children=[html.Div(dcc.Graph(id='liveGraph', animate=False), className='col s12 m6 l6'),
                                            html.Div(dcc.Graph(id='longTerm', animate=False), className='col s12 m6 l6')],style={'backgroundColor': app_colors['blue'],},),

        html.Div(className='row', children=[html.Div(id="recentTweetsTable", className='col s12'),]),
        dcc.Interval(
            id='liveGraphUpdate',
            interval=1*1000
        ),
        dcc.Interval(
            id='longGraphUpdate',
            interval=60*1000
        ),
        dcc.Interval(
            id='recentTableUpdate',
            interval=60*1000
        ),

    ], style={'backgroundColor': app_colors['background'], 'margin-top':'30px', 'height':'2000px',},
)


#to give color to tweets based on sentiment score
def color(s):
    if s >= POS_NEG_NEUT:
        # positive
        return "#002C0D"
    elif s <= -POS_NEG_NEUT:
        # negative:
        return "#270000"

    else:
        return app_colors['background']


#to generate tweets table
def generate_table(df, max_rows=10):
    return html.Table(className="responsive-table",
                      children=[
                          html.Thead(
                              html.Tr(
                                  children=[
                                      html.Th(col.title()) for col in df.columns.values],
                                  style={'color':app_colors['text']}
                                  )
                              ),
                          html.Tbody(
                              [
                                  
                              html.Tr(
                                  children=[
                                      html.Td(data) for data in d
                                      ], style={'color':app_colors['text'],
                                                'background-color':color(d[2])}
                                  )
                               for d in df.values.tolist()])
                          ]
    )

@app.callback(Output('recentTweetsTable', 'children'),
              [Input(component_id='sentiment_term', component_property='value')],
              events=[Event('recentTableUpdate', 'interval')])        
def updateLatestTweets(sentiment_term):
    conn = sqlite3.connect('twitter2.db')
    c = conn.cursor()
    df = pd.read_sql("SELECT * FROM tweet WHERE Tweets LIKE ? ORDER BY UnixTime DESC LIMIT 10", conn ,
    params=('%' + sentiment_term + '%',))
    df['date'] = pd.to_datetime(df['UnixTime'], unit='ms')
    df = df[['date','Tweets','Sentiment_Score']]
    
    return generate_table(df, max_rows=10)


#to draw short term/live graph
@app.callback(Output('liveGraph', 'figure'),
              [Input(component_id='sentiment_term', component_property='value')],
              events=[Event('liveGraphUpdate', 'interval')])
def updateGraph(sentiment_term):
    try:
        conn = sqlite3.connect('twitter2.db')
        c = conn.cursor()
        df = pd.read_sql("SELECT * FROM tweet WHERE Tweets LIKE ? ORDER BY UnixTime DESC LIMIT 15", conn ,
        params=('%' + sentiment_term + '%',))
        df.sort_values('UnixTime', inplace=True)
        df['sentimentSmooth'] = df['Sentiment_Score'].rolling(int(len(df)/10)).mean()
        # df['date'] = pd
        df['date'] = pd.to_datetime(df['UnixTime'], unit='ms')
        # seconds = df['unix']/1000
        # df['date'] = time.ctime(seconds)
        df.set_index('date', inplace=True)

        # df = df.resample('10s').mean()
        df.dropna(inplace=True)
        X = df.index
        Y = df.sentimentSmooth
        
        data = plotly.graph_objs.Scatter(
                x=X,
                y=Y,
                name='Scatter',
                mode= 'lines+markers'
                )

        return {'data': [data],'layout' : go.Layout(xaxis=dict(range=[min(X),max(X)]),
                                                    yaxis=dict(range=[min(Y),max(Y)]),
                                                    title='Short Term Graph For: {}'.format(sentiment_term))}

    except Exception as e:
        with open('errors.txt','a') as fl:
            fl.write(str(e))
            fl.write('\n')

#to draw long term graph
@app.callback(Output('longTerm', 'figure'),
              [Input(component_id='sentiment_term', component_property='value')],
              events=[Event('longGraphUpdate', 'interval')])
def updateGraph(sentiment_term):
    try:
        conn = sqlite3.connect('twitter2.db')
        c = conn.cursor()
        df = pd.read_sql("SELECT * FROM tweet WHERE Tweets LIKE ? ORDER BY UnixTime DESC LIMIT 1000", conn ,
        params=('%' + sentiment_term + '%',))
        df.sort_values('UnixTime', inplace=True)
        df['sentimentSmooth'] = df['Sentiment_Score'].rolling(int(len(df)/10)).mean()

        df['date'] = pd.to_datetime(df['UnixTime'],unit='ms')
        df.set_index('date', inplace=True)

        # df = df.resample('2min').mean()
        df.dropna(inplace=True)
        X = df.index
        Y = df.sentimentSmooth
        data = plotly.graph_objs.Scatter(
                x=X,
                y=Y,
                name='Scatter',
                mode= 'lines+markers'
                )

        return {'data': [data],'layout' : go.Layout(xaxis=dict(range=[min(X),max(X)]),
                                                    yaxis=dict(range=[min(Y),max(Y)]),
                                                    title='Long Term Graph For: {}'.format(sentiment_term))}

    except Exception as e:
        with open('errors.txt','a') as fl:
            fl.write(str(e))
            fl.write('\n')

external_css = ["https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/css/materialize.min.css"]
for css in external_css:
    app.css.append_css({"external_url": css})


external_js = ['https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js',
               'https://pythonprogramming.net/static/socialsentiment/googleanalytics.js']
for js in external_js:
    app.scripts.append_script({'external_url': js})
            
            
if __name__ == '__main__':
    app.run_server(debug=True)
