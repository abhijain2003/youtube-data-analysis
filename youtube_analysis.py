# Import required libraries
from googleapiclient.discovery import build
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output


api_key = 'AIzaSyDx2Kn42HjKyDemyO7VJW9s223jYvduTG4'
channel_id = 'UCGYlNGlloLLZiAL3zBgbMgQ'

youtube = build('youtube', 'v3', developerKey=api_key)

# function to get channel data


def get_upload_id(youtube, channel_id):
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=channel_id
    )
    response = request.execute()

    upload_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    return upload_id


upload_id = get_upload_id(youtube, channel_id)


# function to get video id
def get_video_id(youtube, upload_id):

    request = youtube.playlistItems().list(
        part="contentDetails",
        playlistId=upload_id,
        maxResults=50
    )
    response = request.execute()

    video_ids = []

    for i in range(len(response['items'])):
        video_ids.append(response['items'][i]['contentDetails']['videoId'])

    next_page_token = response.get('nextPageToken')
    next_page = True

    while next_page:
        if next_page_token is None:
            next_page = False
        else:
            request = youtube.playlistItems().list(
                part="contentDetails",
                playlistId=upload_id,
                maxResults=50,
                pageToken=next_page_token)
            response = request.execute()

            for i in range(len(response['items'])):
                video_ids.append(response['items'][i]
                                 ['contentDetails']['videoId'])

            next_page_token = response.get('nextPageToken')

    return video_ids


video_ids = get_video_id(youtube, upload_id)

# function to get video details


def get_video_details(youtube, video_ids):
    all_video_detail = []
    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=",".join(video_ids[i:i+50]))
        response = request.execute()

        for video in response['items']:
            video_dict = dict(
                title=video['snippet']['title'],
                publishedDate=video['snippet']['publishedAt'],
                channelName=video['snippet']['channelTitle'],
                views=video['statistics']['viewCount'],
                likes=video['statistics']['likeCount'],
                favoriteCount=video['statistics']['favoriteCount'],
                duration=video['contentDetails']['duration'],
                comments=video['statistics'].get('commentCount', 0)
            )
            all_video_detail.append(video_dict)

    return all_video_detail


all_video_data = get_video_details(youtube, video_ids)

df = pd.DataFrame(all_video_data)

convert_dict = {'comments': int,
                'favoriteCount': int,
                'views': int,
                'likes': int
                }

df = df.astype(convert_dict)
df['publishedDate'] = pd.to_datetime(df['publishedDate']).dt.date


app = dash.Dash(__name__)

app.layout = html.Div(children=[html.H1('Youtube Channel Performance Dashboard', style={'textAlign': 'center', 'color': '#503D36', 'font-size': 40}),
                                html.Div(["Input Year: ", dcc.Input(id='input-year', value='2010',
                                                                    type='number', style={'height': '50px', 'font-size': 35}), ],
                                         style={'font-size': 40}),
                                html.Br(),
                                html.Br(),
                                html.Div(dcc.Graph(id='bar-plot')),
                                ])


# add callback decorator


@app.callback(Output(component_id='bar-plot', component_property='figure'),
              Input(component_id='input-year', component_property='value'))
# Add computation to callback function and return graph
def get_graph(entered_year):
    # Select 2019 data
    
    year_data = df[pd.to_datetime(df['publishedDate']).dt.year == int(entered_year)]

    month_data = year_data[['publishedDate', 'views']]
    month_data['publishedDate'] = pd.DatetimeIndex(month_data['publishedDate']).month
    month_data = pd.DataFrame(month_data.groupby('publishedDate')['views'].sum())
    month_data.reset_index(inplace=True)
    
    print(month_data)
    #Group the data by Month and compute average over arrival delay time.
   
    fig = px.bar(month_data, x='publishedDate', y='views',
                 title='Bar chart of Youtube Channel Performance Dashboard of Selected Year monthly')
    fig.update_layout()
    return fig


# Run the app
if __name__ == '__main__':
    app.run_server()
