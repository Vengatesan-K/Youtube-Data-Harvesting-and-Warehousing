import pandas as pd
import numpy as np
import requests
import seaborn as sns
from googleapiclient.discovery import build
import isodate
import streamlit as st
import seaborn as sns
from streamlit_option_menu import option_menu
import pymongo
import psycopg2

from streamlit_lottie import st_lottie

import json
import plotly.express as px
import pymongo
from pymongo import MongoClient

client = pymongo.MongoClient("mongodb+srv://Vengat2612:Vengat2612@cluster0.ntbf1lc.mongodb.net/?retryWrites=true&w=majority")
mydb = client["youtube_project"]
channel_list = mydb.list_collection_names()

conn = psycopg2.connect(host="localhost", user="postgres", password="Venkat@26", port=5432, database="youtube")
cur = conn.cursor()

def api_connect():
    api_key =  "AIzaSyAgW7lZYJQ22BRh7pyJvY1ZiJwHMNnJvOo"

    api_service_name = "youtube"
    
    api_version = "v3"
    
    youtube = build(api_service_name,api_version , developerKey=api_key)
    
    return youtube



def channel_details(youtube, channel_id):
    request = youtube.channels().list(
        part='snippet,contentDetails,statistics',
        id= channel_id)
    response = request.execute() 
    channel_info = {}
    for item in response['items']:
            data = {'Channel_id':item["id"],
                    'Channel_name':item['snippet']['title'],
                    'Subscribers':item['statistics']['subscriberCount'],
                    'Views':item['statistics']['viewCount'],
                    'Total_videos':item['statistics']['videoCount'],
                    'Playlist_id':item['contentDetails']['relatedPlaylists']['uploads'],
                    'Description':item['snippet']['description'],
                    'publishedAt':item['snippet']['publishedAt'].replace('T', ' ').replace('Z', ''),
                    'Country':item['snippet'].get('country')
                   }
            channel_info.update(data)
            return channel_info


def get_video_ids(youtube,channel_id):
    video_id = []
    # get Uploads playlist id
    res = youtube.channels().list(id=channel_id, 
                                  part='contentDetails').execute()
    playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    next_page_token = None
    
    while True:
        res = youtube.playlistItems().list(playlistId=playlist_id, 
                                           part='snippet', 
                                           maxResults=50,
                                           pageToken=next_page_token).execute()
        
        for i in range(len(res['items'])):
            video_id.append(res['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token = res.get('nextPageToken')
        
        if next_page_token is None:
            break
    return video_id



#print(video_ids)

def video_details(youtube,video_ids):
    video_ids = get_video_ids(youtube,channel_id)
    video_info = []
    
    for i in range(0, len(video_ids), 50):
        response = youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=','.join(video_ids[i:i+50])).execute()
        for video in response['items']:
            video_detail = dict(Channel_name = video['snippet']['channelTitle'],
                                Channel_id = video['snippet']['channelId'],
                                Video_id = video['id'],
                                Title = video['snippet']['title'],
                                Tags = video['snippet'].get('tags'),
                                Thumbnail = video['snippet']['thumbnails']['default']['url'],
                                Description = video['snippet']['description'],
                                Published_date = video['snippet']['publishedAt'].replace('T', ' ').replace('Z', ''),
                                Duration = isodate.parse_duration(video['contentDetails']['duration']).total_seconds(),
                                Views = video['statistics'].get("viewCount", 0),
                                Likes = video['statistics'].get('likeCount'),
                                Comments = video['statistics'].get('commentCount'),
                                Dislikes = video["statistics"].get("dislikeCount", 0),
                                Favorite_count = video['statistics']['favoriteCount'],
                                Definition = video['contentDetails']['definition'],
                                Caption_status = video['contentDetails']['caption']
                               )
            video_info.append(video_detail)
    return video_info



def comment_details(youtube,video_ids):
    video_ids = get_video_ids(youtube,channel_id)
    comments_info = []
    
    for i in range(len(video_ids)):
        request = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_ids[i],
            maxResults=20
        )
        try:
            response = request.execute()
            c=0
            for comment in response['items']:
                Video_id = comment['snippet']['videoId']
                commentts=comment['snippet']['topLevelComment']['snippet']['textOriginal']
                comment_author = comment['snippet']['topLevelComment']['snippet']['authorDisplayName']
                comment_like_count=comment['snippet']['topLevelComment']['snippet']['likeCount']
                comment_id = comment['snippet']['topLevelComment']['id']
                comment_publishedAt=comment['snippet']['topLevelComment']['snippet']['publishedAt'].replace('T', ' ').replace('Z', '')
                try:
                    comment_replies = comment['replies']['comments']
                    Reply_dict = {}
                    for j in range(len(comment_replies)):
                        Comment_Reply_id =  comment['replies']['comments'][j]['id']
                        Comment_Reply_author = comment['replies']['comments'][j]['snippet']['authorDisplayName']
                        Comment_Reply_like_count=comment['replies']['comments'][j]['snippet']['likeCount']
                        Comment_Reply_text = comment['replies']['comments'][j]['snippet']['textOriginal']
                        Comment_Reply_publishedAt=comment['replies']['comments'][j]['snippet']['publishedAt'].replace('T', ' ').replace('Z', '')
                        Reply_dict.update({'comment_Id':Comment_Reply_id,'comment': Comment_Reply_text,
                                           'comment_author':Comment_Reply_author,
                                           'comment_like_count':Comment_Reply_like_count,
                                           'comment_publishedAt':Comment_Reply_publishedAt})
                except:
                    Reply_dict=None
                    comments_info.append({'Video_id': Video_id,'commentts':commentts,'comment_author':comment_author,
                                         'comment_like_count':comment_like_count,'comment_id':comment_id,
                                         'comment_publishedAt':comment_publishedAt,'Reply_dict':Reply_dict})

        except:
            pass
        
    return comments_info


from requests import HTTPError



st.set_page_config(page_title='Youtube Data Harvesting and Warehousing with MongoDB, SQL', layout="wide", page_icon = r'youtubeproject.png')
page_bg_img = """
<style>
[data-testid="stAppViewContainer"] {
background-image: url("https://mcdn.wallpapersafari.com/medium/20/68/7XpnOk.jpg");
background-size: cover;
}
</style>
"""
with st.sidebar:
    st_lottie("https://assets4.lottiefiles.com/packages/lf20_ej2lfhv2.json",height=100,width=200)
 
st.markdown(page_bg_img, unsafe_allow_html=True)
with st.sidebar:
    opt = option_menu(
        menu_title="Menu",
        options=["About", "Import", "Store", "Insights"],
        icons=["house", "upload", "table", "bar-chart-line-fill"],
        menu_icon="cast",
        default_index=0
    )
if opt == "About":
    st.title("YouTube Data Harvesting and Warehousing with MongoDB, SQL")
    st.write("Youtube is home to vloggers, dance videos, educational content and lots of useful data."  "Web scraping, the automatic extraction of data from a web page, is the best tool for collecting data from Youtube."
             "Using a Youtube scraper benefits an organization because the data analysis yields valuable insights about video performance, user sentiment, and your channel."
             "This useful data can be combined with data extracted from social media sites in order to be more comprehensive.")
    st.header("Benefits of Using a Youtube Scraper")
    st.write("Using a Youtube scraper makes it easy, fast, and cheap to extract useful data from Youtube."
             "Whether you’re a small business owner or part of the data department at a large organization, you can experience many benefits from scraping Youtube.")
    st.header("Channel data")
    st.write("When you scrape the page for a Youtube channel, you’ll get data related to subscribers, amount of videos, playlists, and more."
             "On the about page, you’ll find the total number of views for the channel.")
    st.header("Video performance data")
    st.write("When you scrape the page for a specific video, you’ll receive the number of views, likes, dislikes, channel subscribers, comments, and more."
             "While each of these metrics can be analyzed individually, it is important to keep the ration of the metrics in mind.")
    st.header("Sentiment data")
    st.write("The Youtube comment section is full of user sentiment data that reveals different reactions to the video’s content."
             "Before using a Youtube comment scraper, keep in mind that trolls are common in the comment section and therefore extreme negative comments should not be analyzed as legitimate feedback."
             "Thankfully, many loyal fans, casual viewers, and new viewers leave thoughtful comments either in response to or about the video’s content.")


elif opt == "Import":
    st.title("YouTube Data Harvesting")
    col1, col2 = st.columns([6, 2])
    with col1:
        channel_id = st.text_input("Enter the channel id")
        page_names = ["Enter", "Preview", "Upload"]
        page = st.radio("select", page_names, horizontal=True, label_visibility="hidden")

        if channel_id and page  == "Enter":
            st.write("You can now preview the json file or upload the file in MongoDB")

        if page == "Preview":
            channel_stats = channel_details(api_connect(), channel_id)
            video_ids = get_video_ids(api_connect(),channel_id)
            video_stats = video_details(api_connect(),video_ids)
            comment_stats = comment_details(api_connect(),video_ids)
            preview_file = dict(channel_info=channel_stats, video_info = video_stats,comments_info=comment_stats)
            st.write(preview_file)
   
        if page == "Upload":
            channel_stats = channel_details(api_connect(), channel_id)
            video_ids = get_video_ids(api_connect(),channel_id)
            video_stats = video_details(api_connect(),video_ids)
            comment_stats = comment_details(api_connect(),video_ids)
            file_upload = dict(channel_info=channel_stats, video_info = video_stats, comments_info=comment_stats,)
            channel_name = file_upload["channel_info"]["Channel_name"]
            col = mydb[channel_name]
            col.insert_one(file_upload)
            
elif opt == "Store":
    st.title("YouTube Data Harvesting and Warehousing")  # Have to get the list channel_name here
    channel_id = st.text_input("Enter the channel id")
    id_selected = st.selectbox("Select a channel name to migrate the data from mongodb to sql",
                               options=channel_list)
    migrate = st.button("Migrate")

    if migrate:
        channel_dict = channel_details(api_connect(), channel_id)
        channel_df = pd.DataFrame([channel_dict])
        channel_df["Subscribers"] = channel_df["Subscribers"].astype("int64")
        channel_df["Views"] = channel_df["Views"].astype("int64")
        # print(channel_df)
        cur.execute(
            "CREATE TABLE IF NOT EXISTS CHANNEL(CHANNEL_ID VARCHAR(50) PRIMARY KEY, CHANNEL_NAME VARCHAR(75), "
            "SUBSCRIBER_COUNT INT, CHANNEL_VIEW_COUNT INT, CHANNEL_DESCRIPTION TEXT)")
        conn.commit()
        a = "INSERT INTO CHANNEL(CHANNEL_ID, CHANNEL_NAME, SUBSCRIBER_COUNT, CHANNEL_VIEW_COUNT, CHANNEL_DESCRIPTION) " \
            "VALUES(%s, %s, %s, %s, %s)"
        for index, value in channel_df.iterrows():
            val = value["Channel_id"]
            cur.execute(f"SELECT * FROM CHANNEL WHERE CHANNEL_ID = '{val}'")
            w = cur.fetchall()
            if len(w) > 0:
                cur.execute(f"DELETE FROM CHANNEL WHERE CHANNEL_ID = '{val}'")
                conn.commit()
            result_1 = (
                value["Channel_id"], value["Channel_name"], value["Subscribers"], value["Views"],
                value["Description"])
            cur.execute(a, result_1)
        conn.commit()
        
        video_ids = get_video_ids(api_connect(),channel_id)
        video_dict = video_details(api_connect(),video_ids)
        video_df = pd.DataFrame(video_dict)
        video_df["Views"] = video_df["Views"].astype("int64")
        video_df["Likes"] = video_df["Likes"].astype("int64")
        video_df["Favorite_count"] = video_df["Favorite_count"].astype("int64")
        video_df["Duration"] = video_df["Duration"].astype("int64")
        video_df['Published_date'] = pd.to_datetime(video_df['Published_date']).astype("datetime64[ns]")
        # print(video_df.head(2))
        # print(video_df.info())
        cur.execute(
            "CREATE TABLE IF NOT EXISTS VIDEO(CHANNEL_ID VARCHAR(75), VIDEO_ID VARCHAR(100) PRIMARY KEY, VIDEO_TITLE "
            "TEXT, VIDEO_DESCRIPTION TEXT, VIDEO_DURATION INT, VIDEO_CAPTION VARCHAR(10), "
            "VIEW_COUNT INT, LIKE_COUNT INT, DISLIKE_COUNT INT, FAVOURITE_COUNT INT, COMMENT_COUNT INT, "
            "PUBLISHED_AT TIMESTAMP)")
        conn.commit()
        c = "INSERT INTO VIDEO(CHANNEL_ID, VIDEO_ID, VIDEO_TITLE, VIDEO_DESCRIPTION, VIDEO_DURATION, VIDEO_CAPTION, " \
            "VIEW_COUNT, LIKE_COUNT, DISLIKE_COUNT, FAVOURITE_COUNT, COMMENT_COUNT, PUBLISHED_AT) VALUES(%s, %s, %s, " \
            "%s, " \
            "%s, %s, %s, %s, %s, %s, %s, %s)"
        for index, value_2 in video_df.iterrows():
            val_2 = value_2["Video_id"]
            cur.execute(f"SELECT * FROM VIDEO WHERE VIDEO_ID = '{val_2}'")
            y = cur.fetchall()
            if len(y) > 0:
                cur.execute(f"DELETE FROM VIDEO WHERE VIDEO_ID = '{val_2}'")
                conn.commit()
            result_3 = (
                value_2["Channel_id"], value_2["Video_id"], value_2["Title"], value_2["Description"],
                value_2["Duration"], value_2["Caption_status"], value_2["Views"], value_2["Likes"],
                value_2["Dislikes"], value_2["Favorite_count"], value_2["Comments"], value_2["Published_date"])
            cur.execute(c, result_3)
        conn.commit()
        
         
        comments_dict = comment_details(api_connect(),video_ids)
        comments_df = pd.DataFrame(comments_dict)
        comments_df['comment_publishedAt'] = pd.to_datetime(comments_df['comment_publishedAt']).dt.date
        # print(comments_df.info())
        # print(comments_df.head(2))
        cur.execute("CREATE TABLE IF NOT EXISTS COMMENTS(VIDEO_ID VARCHAR(75), COMMENT_ID VARCHAR(75) PRIMARY KEY, "
                    "PUBLISHED_AT VARCHAR(30), COMMENTED_BY VARCHAR(50), COMMENT_GIVEN TEXT)")
        conn.commit()
        d = "INSERT INTO COMMENTS(VIDEO_ID, COMMENT_ID, PUBLISHED_AT,  COMMENTED_BY, COMMENT_GIVEN) VALUES(%s, %s, " \
            "%s, %s, %s)"
        for index, value_3 in comments_df.iterrows():
            val_3 = value_3["comment_id"]
            cur.execute(f"SELECT * FROM COMMENTS WHERE COMMENT_ID = '{val_3}'")
            z = cur.fetchall()
            if len(z) > 0:
                cur.execute(f"DELETE FROM COMMENTS WHERE COMMENT_ID = '{val_3}'")
                conn.commit()
            result_4 = (
                value_3["Video_id"], value_3["comment_id"], value_3["comment_publishedAt"], value_3["comment_author"],
                value_3["commentts"])
            cur.execute(d, result_4)
        conn.commit()
        
else:
    st.title("YouTube Data Analysis")
    st.subheader("Simplify and analyze the migrated data from the selected ten questions to gain valuable insights")

    question_list = ["Select", "What are the names of all the videos and their corresponding channels?",
                     "Which channels have the most number of videos, and how many videos do they have?",
                     "What are the top 10 most viewed videos and their respective channels?",
                     "How many comments were made on each video, and what are their corresponding video names?",
                     "Which videos have the highest number of likes, and what are their corresponding channel names?",
                     "What is the total number of likes and dislikes for each video, and what are their corresponding "
                     "video names?",
                     "What is the total number of views for each channel, and what are their corresponding channel "
                     "names?",
                     "What are the names of all the channels that have published videos in the year 2022?",
                     "What is the average duration of all videos in each channel, and what are their corresponding "
                     "channel names?",
                     "Which videos have the highest number of comments, and what are their corresponding channel names?"
                     ]
    question_selected = st.selectbox("Select the question from below options", options=question_list)

    if question_selected == "Select":
        st.write("   ")

    if question_selected == "What are the names of all the videos and their corresponding channels?":
        cur.execute("SELECT CHANNEL.CHANNEL_NAME, VIDEO.VIDEO_TITLE FROM CHANNEL JOIN VIDEO ON VIDEO.CHANNEL_ID = "
                    "CHANNEL.CHANNEL_ID")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Channel Name', 'Video title'])
        st.table(df)

    if question_selected == "Which channels have the most number of videos, and how many videos do they have?":
        cur.execute("SELECT CHANNEL.CHANNEL_NAME , COUNT(VIDEO_ID) AS VIDEO_COUNT FROM VIDEO JOIN CHANNEL ON "
                    "CHANNEL.CHANNEL_ID = VIDEO.CHANNEL_ID GROUP BY CHANNEL.CHANNEL_ID, VIDEO.CHANNEL_ID ORDER BY "
                    "VIDEO_COUNT DESC LIMIT 3")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Channel Name', 'Number of videos'])
        st.table(df)

    if question_selected == "What are the top 10 most viewed videos and their respective channels?":
        cur.execute("SELECT CHANNEL.CHANNEL_NAME, VIDEO.VIEW_COUNT FROM CHANNEL JOIN VIDEO ON VIDEO.CHANNEL_ID = "
                    "CHANNEL.CHANNEL_ID ORDER BY VIEW_COUNT DESC LIMIT 10")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Channel Name', 'Top view count'])
        st.table(df)

    if question_selected == "How many comments were made on each video, and what are their corresponding video names?":
        cur.execute("SELECT VIDEO.VIDEO_TITLE, COUNT(COMMENT_ID) AS TOTAL_COMMENT FROM COMMENTS JOIN VIDEO ON "
                    "VIDEO.VIDEO_ID = COMMENTS.VIDEO_ID GROUP BY VIDEO_TITLE ORDER BY TOTAL_COMMENT DESC")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Video Title', 'Comments count'])
        st.table(df)

    if question_selected == "Which videos have the highest number of likes, and what are their corresponding channel " \
                            "names?":
        cur.execute("SELECT CHANNEL.CHANNEL_NAME, VIDEO.VIDEO_TITLE, VIDEO.LIKE_COUNT FROM VIDEO JOIN CHANNEL ON "
                    "VIDEO.CHANNEL_ID = CHANNEL.CHANNEL_ID ORDER BY VIDEO.LIKE_COUNT DESC LIMIT 10")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Channel Name', 'Video Title', 'Like Count'])
        st.table(df)

    if question_selected == "What is the total number of likes and dislikes for each video, and what are their " \
                            "corresponding video names?":
        cur.execute("SELECT VIDEO_TITLE, LIKE_COUNT, DISLIKE_COUNT FROM VIDEO")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Video Title', 'Like Count', 'Dislike Count'])
        st.table(df)

    if question_selected == "What is the total number of views for each channel, and what are their corresponding " \
                            "channel names?":
        cur.execute("SELECT CHANNEL_NAME, CHANNEL_VIEW_COUNT FROM CHANNEL ORDER BY CHANNEL_VIEW_COUNT DESC")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Channel Name', 'View Count'])
        st.table(df)

    if question_selected == "What are the names of all the channels that have published videos in the year 2022?":
        cur.execute("SELECT CHANNEL_NAME FROM CHANNEL JOIN VIDEO ON CHANNEL.CHANNEL_ID = VIDEO.CHANNEL_ID WHERE "
                    "EXTRACT(YEAR FROM VIDEO.PUBLISHED_AT) = 2022 GROUP BY CHANNEL.CHANNEL_NAME")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Channels published video in the year 2022'])
        st.table(df)

    if question_selected == "What is the average duration of all videos in each channel, and what are their " \
                            "corresponding channel names?":
        cur.execute("SELECT CHANNEL.CHANNEL_NAME, AVG(VIDEO.VIDEO_DURATION)::INT AS AVERAGE_DURATION FROM VIDEO JOIN "
                    "CHANNEL ON CHANNEL.CHANNEL_ID = VIDEO.CHANNEL_ID GROUP BY CHANNEL.CHANNEL_ID")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Channel Name', 'Average video duration in Seconds'])
        st.table(df)

    if question_selected == "Which videos have the highest number of comments, and what are their corresponding " \
                            "channel names?":
        cur.execute("SELECT CHANNEL.CHANNEL_NAME, VIDEO.VIDEO_TITLE, VIDEO.COMMENT_COUNT FROM VIDEO JOIN CHANNEL ON "
                    "CHANNEL.CHANNEL_ID = VIDEO.CHANNEL_ID ORDER BY VIDEO.COMMENT_COUNT DESC LIMIT 10")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Channel Name', 'Video Title', 'Comment count'])
        st.table(df)







