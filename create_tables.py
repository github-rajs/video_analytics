import psycopg2


#database related variables
host='localhost'
ip='127.0.0.1'
port='5432'
user_name='aditya'
passwd='test1234'
database='appdb'


create_table_query1="CREATE TABLE IF NOT EXISTS video_analytics_data(\
   location varchar(50),\
   station_no varchar(50),\
   station_name varchar(50),\
   camera_id varchar(50),\
   cur_datetime timestamp,\
   alert_id integer,\
   alert_name varchar(30),\
   alert_triggered_time varchar(30),\
   total_num_alerts integer,\
   captured_image_name varchar(50)\
);"

create_table_query2="CREATE TABLE IF NOT EXISTS danger_area_polygons (\
   station_no varchar(50) PRIMARY KEY,\
   camera_id varchar(50) UNIQUE NOT NULL,\
   polygon_json jsonb UNIQUE NOT NULL,\
);"


connection = psycopg2.connect(user=user_name,
                              password=passwd,
                              host=host,
                              port=port,
                              database=database)
cursor = connection.cursor()

try:
    cursor.execute(create_table_query1)
    cursor.execute(create_table_query2)
    
except (Exception, psycopg2.Error) as error :
    print(error)