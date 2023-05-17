# video_analytics

Database - PostgreSQL
 
 1.configure db and other details in config.py
 
 2.to create database tables, run create_tables.py
 
 3.to create new polygon areas on video file,
 
 from create_polygon imort genrate_polygon
 genrate_polygon(video_path)
 
 4.to run video analytics
 
 from  video_analytics import stream_vid
 stream_vid(capture_index)
 
