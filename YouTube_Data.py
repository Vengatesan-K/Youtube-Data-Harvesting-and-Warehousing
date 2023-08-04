#------------------------------------------------------------Import packages and libraries--------------------------------------------------------#
import pandas as pd
import numpy as np
import requests
from googleapiclient.discovery import build
import isodate
from streamlit_option_menu import option_menu
import pymongo
import psycopg2
from streamlit_extras.badges import badge
from streamlit_extras.add_vertical_space import add_vertical_space
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from streamlit_lottie import st_lottie
import json
import plotly.express as px
from pymongo import mongo_client
from requests import HTTPError
import streamlit as st
from PIL import Image
import base64

#--------------------------------------------------------------NoSQL & SQL connection-------------------------------------------------------------#

client = pymongo.MongoClient("mongodb+srv://Username:password@cluster0.ntbf1lc.mongodb.net/?retryWrites=true&w=majority")
mydb = client["youtube_project"]
channel_list = mydb.list_collection_names()

conn = psycopg2.connect(host="localhost", user="username", password="password", port=port, database="database")
cur = conn.cursor()

#--------------------------------------------------------------Retrieve data from Youtube api-----------------------------------------------------#

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
                    'publishedAt':item['snippet']['publishedAt'],
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
                                Published_date = video['snippet']['publishedAt'],
                                Duration = isodate.parse_duration(video['contentDetails']['duration']),
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
                comment_publishedAt=comment['snippet']['topLevelComment']['snippet']['publishedAt']
                try:
                    comment_replies = comment['replies']['comments']
                    Reply_dict = {}
                    for j in range(len(comment_replies)):
                        Comment_Reply_id =  comment['replies']['comments'][j]['id']
                        Comment_Reply_author = comment['replies']['comments'][j]['snippet']['authorDisplayName']
                        Comment_Reply_like_count=comment['replies']['comments'][j]['snippet']['likeCount']
                        Comment_Reply_text = comment['replies']['comments'][j]['snippet']['textOriginal']
                        Comment_Reply_publishedAt=comment['replies']['comments'][j]['snippet']['publishedAt']
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

#---------------------------------------------------------------- Set Streamlit application page ------------------------------------------------#

st.set_page_config(page_title='Youtube Data Harvesting and Warehousing with MongoDB, SQL',
                   page_icon = "▶️", 
                   layout="wide")

reduce_header_height_style = """
    <style>
        div.block-container {padding-top:0rem;}
        div.Sidebar   {padding-top:0rem;}
    </style>
"""
st.markdown(reduce_header_height_style, unsafe_allow_html=True)

hide_st_style ="""
        <style>
        MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """      
#st.markdown(hide_st_style,unsafe_allow_html=True)

with st.sidebar:
    st_lottie("https://assets3.lottiefiles.com/packages/lf20_A6VCTi95cd.json",height=120)    
with st.sidebar:
    opt = option_menu(
        menu_title="Main Menu",
        options=["Home","---", "Upload", "Migrate", "Insights","About"],
        icons=["youtube","","cloud-arrow-up", "database-up", "clipboard2-data-fill","patch-question"],
        menu_icon="menu-up",
        default_index=0,
        orientation="vertical"
    )

#------------------------------------------------------------------------- Home page --------------------------------------------------------------#

if opt == "Home":
            st.image("Blacl.png")
            st.write("Youtube is home to vloggers, dance videos, educational content and lots of useful data. Web scraping, the automatic extraction of data from a web page, is the best tool for collecting data from Youtube. Using a Youtube scraper benefits an organization because the data analysis yields valuable insights about video performance, user sentiment, and your channel. This useful data can be combined with data extracted from social media sites in order to be more comprehensive.")
            st.write("[:open_book: Learn More  >](https://en.wikipedia.org/wiki/YouTube)")     
            st.markdown('__<p style="text-align:left; font-size: 25px; color: #1c0000">Benefits of youtube data harvesting </P>__',
                unsafe_allow_html=True)
            st.write("Using a Youtube scraper makes it easy, fast, and cheap to extract useful data from Youtube. Whether you’re a small business owner or part of the data department at a large organization, you can experience many benefits from scraping Youtube.")
            st.markdown('__<p style="text-align:left; font-size: 25px; color: #1c0000">Channel data </P>__',
                unsafe_allow_html=True)
            st.write("When you scrape the page for a Youtube channel, you’ll get data related to subscribers, amount of videos, playlists, and more. On the about page, you’ll find the total number of views for the channel.")
            st.markdown('__<p style="text-align:left; font-size: 25px; color: #1c0000">Video Perfomance data</P>__',
                unsafe_allow_html=True)
            st.write("When you scrape the page for a specific video, you’ll receive the number of views, likes, dislikes, channel subscribers, comments, and more. While each of these metrics can be analyzed individually, it is important to keep the ration of the metrics in mind.")
            st.markdown('__<p style="text-align:left; font-size: 25px; color: #1c0000">Sentimental data </P>__',
                unsafe_allow_html=True)
            st.write("Thankfully, many loyal fans, casual viewers, and new viewers leave thoughtful comments either in response to or about the video’s content.. Then, your comment section essentially becomes a source of data related to fan requests or different types of videos they would like to see. Scraping the comment section makes it easier to make your subscribers happy and provide relevant content.")
 
#----------------------------------------------------------------------- About page ---------------------------------------------------------------#           

elif opt == "About":
            st.markdown('__<p style="text-align:left; font-size: 25px; color: #020000">Youtube Data Harvesting and Warehousing</P>__',
                unsafe_allow_html=True)
            tab1,tab2 = st.tabs(["Features","Apps used"])
            with tab1:
             st.markdown('__<p style="text-align:left; font-size: 20px; color: #1c0000">Features of this project :</P>__',
                 unsafe_allow_html=True)
             st.write("The Streamlit application allows users to access and analyze data from multiple YouTube channels.")
             st.caption("The application have the following features :")
             st.write("1. Able to input a YouTube channel ID and retrieve all the relevant data (Channel name, subscribers, total video count, playlist ID, video ID, likes,dislikes, comments of each video) using Google API.")
             st.write("2. Option to store the data in a MongoDB database as a data lake.")
             st.write("3. Able to collect data for up to 10 different YouTube channels and store them in the data lake by clicking a upload button.")
             st.write("4. Option to select a channel name and migrate its data from the data lake to a SQL database as tables.")
             st.write("5. Able to search and retrieve data from the SQL database using different search options, including joining tables to get channel details.")
            with tab2:
             st.markdown('__<p style="text-align:left; font-size: 20px; color: #1c0000">Applications and Libraries Used :</P>__',
                unsafe_allow_html=True)
             st.write("  * Python")
             st.write("  * PostgresSql")
             st.write("  * MongoDB")
             st.write("  * Streamlit")
             st.write("  * Plotly")
            add_vertical_space(1)
            st.markdown('__<p style="text-align:left; font-size: 20px; color: #1c0000">Conclusion</P>__',
                unsafe_allow_html=True)
            st.write("For Youtube creators and organizations running their own accounts, Youtube houses lots of useful data that can be extracted for analysis. A web scraping tool automatically extracts data from a given web page quickly, securely, and affordably. Perfect for organizations of any size, a Youtube scraper makes extracting data related to views, comments, likes/dislikes, and even more reveals lots about the state of your Youtube channel making it easier to make better decisions moving forward.")
            st.markdown('__<p style="text-align:left; font-size: 20px; color: #1c0000"> Connect with me on </P>__',
                unsafe_allow_html=True)
            tab1,tab2,tab3 = st.tabs(["LinkedIn","Email","GitHub"])
            with tab1:
                st.write("https://www.linkedin.com/in/vengatesan2612")
            with tab2:
                st.write("kannanvenkatesh772@gmail.com")
            with tab3:
                st.write("https://github.com/Vengatesan-K")
                badge(type="github", name="Vengatesan2997/PhonePe-Pulse-Data-Visualization")

#--------------------------------------------------------------------- Upload page ----------------------------------------------------------------#
            
elif opt == "Upload":
    st.markdown('__<p style="text-align:left; font-size: 28px; color: #020000">Youtube Data Harvesting </P>__',
                unsafe_allow_html=True)
    col1, col2 = st.columns([8, 2])
    with col1:
        st.write("[👆🏽Click Here to YouTube >](https://www.youtube.com/)")
        st.info('Get Channel ID through clicking  Viewpage source📰',icon="ℹ️")
        channel_id = st.text_input("Enter the channel id :")
        page_names = ["Enter", "Preview", "Upload"]
        page = st.radio("select", page_names, horizontal=True, label_visibility="hidden")
        
        if channel_id and page  == "Enter":
            st.success("You can now preview the json file or upload the file to MongoDB")

        if page == "Preview":
            channel_stats = channel_details(api_connect(), channel_id)
            video_ids = get_video_ids(api_connect(),channel_id)
            video_stats = video_details(api_connect(),video_ids)
            comment_stats = comment_details(api_connect(),video_ids)
            preview_file = dict(channel_info=channel_stats, video_info = video_stats,comments_info=comment_stats)
            st.success("🖱️Scroll down to preview the json file")
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
            st.success("Successfully Uploaded to 🍃Atlas Datalake[🛢](https://cloud.mongodb.com/v2/6474913853b9fd0dd4fe8718#/metrics/replicaSet/6474923ad341901bd7b280ae/explorer/Venkat/Youtube/find) ")
    with col2:
        st_lottie("https://assets6.lottiefiles.com/packages/lf20_j9L70r6Tum.json")

#------------------------------------------------------------ Migrate page ----------------------------------------------------------------------#
          
elif opt == "Migrate":
    st.markdown('__<p style="text-align:left; font-size: 28px; color: #020000">Youtube Data Warehousing </P>__',
                unsafe_allow_html=True)
    col1, col2 = st.columns([8, 2])
    with col1:
        channel_id = st.text_input("Enter the channel id :")
        id_selected = st.selectbox("Select a channel name to migrate the data from MongoDB to SQL :twisted_rightwards_arrows:",
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
        st.success("Successfully migrated to SQL Warehouse!")
    with col2 :
        st_lottie("https://assets10.lottiefiles.com/packages/lf20_jk6e0huv.json")

#------------------------------------------------------------------ Insights page ----------------------------------------------------------------#        

else:
    st.markdown('__<p style="text-align:left; font-size: 28px; color: #020000">Youtube Data Analysis </P>__',
                unsafe_allow_html=True)
    col1, col2 = st.columns([7,3])
    with col1 :
        st.markdown('__<p style="text-align:left; font-size: 20px; color: #020000">Select the questions to gain valuable insights from the migrated data :chart_with_upwards_trend: : </P>__',
               unsafe_allow_html=True)
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
        question_selected = st.selectbox("Pick the question from below options :ballot_box_with_check:", options=question_list)
    
    if question_selected == "Select":
        st.write("   ")

    if question_selected == "What are the names of all the videos and their corresponding channels?":
        cur.execute("SELECT CHANNEL.CHANNEL_NAME, VIDEO.VIDEO_TITLE FROM CHANNEL JOIN VIDEO ON VIDEO.CHANNEL_ID = "
                    "CHANNEL.CHANNEL_ID")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Channel Name', 'Video title'])
        st.dataframe(df,use_container_width=True)

    if question_selected == "Which channels have the most number of videos, and how many videos do they have?":
        cur.execute("SELECT CHANNEL.CHANNEL_NAME , COUNT(VIDEO_ID) AS VIDEO_COUNT FROM VIDEO JOIN CHANNEL ON "
                    "CHANNEL.CHANNEL_ID = VIDEO.CHANNEL_ID GROUP BY CHANNEL.CHANNEL_ID, VIDEO.CHANNEL_ID ORDER BY "
                    "VIDEO_COUNT DESC LIMIT 5")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Channel Name', 'Number of videos'])
        tab1,tab2 = st.tabs(["Table","Chart"])
        with tab1:
         st.dataframe(df)
        fig = px.bar(df,
                     x=['Channel Name', 'Number of videos'][0],
                     y=['Channel Name', 'Number of videos'][1],
                     orientation='v',
                     title='Channels with most number of videos and count',
                     color=['Channel Name', 'Number of videos'][0],
                     height=400
                    )
        fig.update_layout(
                    width=850, height=450,
                    title={
                           'x': 0.45,
                           'xanchor': 'center',
                           'y': 0.9,
                           'yanchor': 'top'
                           }
                    )
        with tab2:
         st.plotly_chart(fig,use_container_width=True)

    if question_selected == "What are the top 10 most viewed videos and their respective channels?":
        cur.execute("SELECT CHANNEL.CHANNEL_NAME, VIDEO.VIEW_COUNT FROM CHANNEL JOIN VIDEO ON VIDEO.CHANNEL_ID = "
                    "CHANNEL.CHANNEL_ID ORDER BY VIEW_COUNT DESC LIMIT 10")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Channel Name', 'Top view count'])
        tab1,tab2 = st.tabs(["Table","Chart"])
        with tab1:
         st.dataframe(df)       
        fig = px.pie(df, values='Top view count',
                             names='Channel Name',
                             title='Top 10 Most-viewd videos and their channels',
                             color_discrete_sequence=px.colors.sequential.Agsunset,
                             labels={'Channel Name':'Channel Name'})
        fig.update_layout(
                    width=850, height=450,
                    title={
                           'x': 0.45,
                           'xanchor': 'center',
                           'y': 0.9,
                           'yanchor': 'top'
                           }
                    )
        with tab2:
         st.plotly_chart(fig,use_container_width=True)

    if question_selected == "How many comments were made on each video, and what are their corresponding video names?":
        cur.execute("SELECT VIDEO.VIDEO_TITLE, COUNT(COMMENT_ID) AS TOTAL_COMMENT FROM COMMENTS JOIN VIDEO ON "
                    "VIDEO.VIDEO_ID = COMMENTS.VIDEO_ID GROUP BY VIDEO_TITLE ORDER BY TOTAL_COMMENT DESC")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Video Title', 'Comments count'])
        st.dataframe(df,use_container_width=True)

    if question_selected == "Which videos have the highest number of likes, and what are their corresponding channel " \
                            "names?":
        cur.execute("SELECT CHANNEL.CHANNEL_NAME, VIDEO.VIDEO_TITLE, VIDEO.LIKE_COUNT FROM VIDEO JOIN CHANNEL ON "
                    "VIDEO.CHANNEL_ID = CHANNEL.CHANNEL_ID ORDER BY VIDEO.LIKE_COUNT DESC LIMIT 10")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Channel Name', 'Video Title', 'Like Count'])
        tab1,tab2 = st.tabs(["Table","Chart"])
        with tab1:
         st.dataframe(df,use_container_width=True)
        fig = px.bar(df,
                     x=['Channel Name', 'Video Title', 'Like Count'][2],
                     y=['Channel Name', 'Video Title', 'Like Count'][1],
                     orientation='h',
                     title='Videos with highest like counts and their channels',
                     color=['Channel Name', 'Video Title', 'Like Count'][0]
                    )
        fig.update_layout(
                    width=850, height=450,
                    title={
                           'x': 0.45,
                           'xanchor': 'center',
                           'y': 0.9,
                           'yanchor': 'top'
                           }
                    )
        
        with tab2:
         st.plotly_chart(fig,use_container_width=True)

    if question_selected == "What is the total number of likes and dislikes for each video, and what are their " \
                            "corresponding video names?":
        cur.execute("SELECT VIDEO_TITLE, LIKE_COUNT, DISLIKE_COUNT FROM VIDEO")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Video Title', 'Like Count', 'Dislike Count'])
        st.dataframe(df,use_container_width=True)

    if question_selected == "What is the total number of views for each channel, and what are their corresponding " \
                            "channel names?":
        cur.execute("SELECT CHANNEL_NAME, CHANNEL_VIEW_COUNT FROM CHANNEL ORDER BY CHANNEL_VIEW_COUNT DESC")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Channel Name', 'View Count'])
        tab1,tab2 = st.tabs(["Table","Chart"])
        with tab1:
         st.dataframe(df,use_container_width=True)
        fig = px.bar(df,
                     x=['Channel Name', 'View Count'][1],
                     y=['Channel Name', 'View Count'][0],
                     orientation='h',
                     title='Total number of views for each channels',
                     color=['Channel Name', 'View Count'][0]
                    )
        fig.update_layout(
                    width=850, height=450,
                    title={
                           'x': 0.45,
                           'xanchor': 'center',
                           'y': 0.9,
                           'yanchor': 'top'
                           }
                    )
        
        with tab2:
         st.plotly_chart(fig,use_container_width=True)

    if question_selected == "What are the names of all the channels that have published videos in the year 2022?":
        cur.execute("SELECT CHANNEL_NAME FROM CHANNEL JOIN VIDEO ON CHANNEL.CHANNEL_ID = VIDEO.CHANNEL_ID WHERE "
                    "EXTRACT(YEAR FROM VIDEO.PUBLISHED_AT) = 2022 GROUP BY CHANNEL.CHANNEL_NAME")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Channels published video in the year 2022'])
        tab1,tab2 = st.tabs(["Table","Chart"])
        with tab1:
         st.dataframe(df)
               
        tokens = (df['Channels published video in the year 2022'])
        comment_words =''
    # Converts each token into lowercase
        for i in range(len(tokens)):
         tokens[i] = tokens[i].lower()
     
         comment_words += " ".join(tokens)+" "
     
        #channel_titles = [df['Channels published video in the year 2022'][1] for key in df]
        # text = ' '.join(channel_titles)
        wordcloud = WordCloud(width=800,height=400,background_color='black').generate(comment_words)
        with tab2:
         st.caption("Published channels in 2022")
         plt.title('2022 published channels',fontweight ="bold")
         plt.figure(figsize=(4,2))
         plt.imshow(wordcloud,interpolation='spline36')
         st.pyplot(plt,use_container_width=False)
        
    if question_selected == "What is the average duration of all videos in each channel, and what are their " \
                            "corresponding channel names?":
        cur.execute("SELECT CHANNEL.CHANNEL_NAME, AVG(VIDEO.VIDEO_DURATION)::INT AS AVERAGE_DURATION FROM VIDEO JOIN "
                    "CHANNEL ON CHANNEL.CHANNEL_ID = VIDEO.CHANNEL_ID GROUP BY CHANNEL.CHANNEL_ID")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Channel Name', 'Average video duration in Seconds'])
        tab1,tab2 = st.tabs(["Table","Chart"])
        with tab1:
         st.dataframe(df)
        fig = px.bar(df,
                     x=['Channel Name', 'Average video duration in Seconds'][1],
                     y=['Channel Name', 'Average video duration in Seconds'][0],
                     orientation='h',
                     title='Average duration of all videos for each channels',
                     color=['Channel Name', 'Average video duration in Seconds'][0]
        )
        fig.update_layout(
                    width=850, height=450,
                    title={
                           'x': 0.45,
                           'xanchor': 'center',
                           'y': 0.9,
                           'yanchor': 'top'
                           }
                    )
        with tab2:
         st.plotly_chart(fig,use_container_width=True)

    if question_selected == "Which videos have the highest number of comments, and what are their corresponding " \
                            "channel names?":
        cur.execute("SELECT CHANNEL.CHANNEL_NAME, VIDEO.VIDEO_TITLE, VIDEO.COMMENT_COUNT FROM VIDEO JOIN CHANNEL ON "
                    "CHANNEL.CHANNEL_ID = VIDEO.CHANNEL_ID ORDER BY VIDEO.COMMENT_COUNT DESC LIMIT 10")
        fetch = cur.fetchall()
        df = pd.DataFrame(fetch, columns=['Channel Name', 'Video Title', 'Comment count'])
        tab1,tab2 = st.tabs(["Table","Chart"])
        with tab1:
         st.dataframe(df)
         st.info('"None" indicates Comments are disabled by channel author.',icon="ℹ️")
        fig = px.bar(df,
                     x=['Channel Name', 'Video Title', 'Comment count'][2],
                     y=['Channel Name', 'Video Title', 'Comment count'][1],
                     orientation='v',
                     title='Videos with highest number of comments and their channels',
                     color=['Channel Name', 'Video Title', 'Comment count'][0]
                    )
        fig.update_layout(
                    width=850, height=450,
                    title={
                           'x': 0.45,
                           'xanchor': 'center',
                           'y': 0.9,
                           'yanchor': 'top'
                           }
                    )
        with tab2:
         st.plotly_chart(fig,use_container_width=True)
         st.info('"None" indicates Comments are disabled by channel author.',icon="ℹ️")
    with col2:
        st_lottie("https://assets5.lottiefiles.com/packages/lf20_qp1q7mct.json")
        
#---------------------------------------------------------- The End ------------------------------------------------------------------------------#
        




