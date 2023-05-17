import cv2 as cv
import numpy as np
import json
import psycopg2

#database related variables
host='localhost'
ip='127.0.0.1'
port='5432'
user_name='aditya'
passwd='test1234'
database='appdb'
polygon1 = []          
polygon2 = []

create_table_query="CREATE TABLE IF NOT EXISTS danger_area_polygons (\
   station_no varchar(50) PRIMARY KEY,\
   camera_id varchar(50) UNIQUE NOT NULL,\
   polygon_json jsonb UNIQUE NOT NULL,\
);"

truncate_query='truncate table danger_area_polygons;'

fetch_polygon_cords_query="select polygon_json from danger_area_polygons;"


connection = psycopg2.connect(user=user_name,
                              password=passwd,
                              host=host,
                              port=port,
                              database=database)
cursor = connection.cursor()

def exec_db_command(cmdname,query):    
    if cmdname=='fetch':  
        try:
            cursor.execute(fetch_polygon_cords_query)
            output = cursor.fetchall()
            #cursor.close()
            #connection.close()
        except (Exception, psycopg2.Error) as error :
            print(error) 
            output='fetch failed'
            
    elif cmdname=='gen_poly':
        try:
            cursor.execute(query)
            #cursor.close()
            #connection.close()
            output='insert'
        except (Exception, psycopg2.Error) as error :
            print(error)
            output='insert failed'
    else:
        output='connection failed' 
             
    return output


def capture_frame(video_path):
    cap = cv.VideoCapture(video_path)            
    ret, frame = cap.read()
    cap.release()
    return frame

def click_event(event, x, y, flags, param):
    global polygon1, polygon2            
    if event == cv.EVENT_LBUTTONDOWN:                            
        font = cv.FONT_HERSHEY_COMPLEX_SMALL
        strXY = str(x) + " , " + str(y)
        cv.putText(frame, strXY, (x, y), font, 0.5, (0,128, 255), 1, cv.LINE_AA)
        cv.imshow("IMAGE", frame)
        if len(polygon1) < 4:
            polygon1.append([x, y])                 
        elif len(polygon2) < 4:
            polygon2.append([x, y])
        if len(polygon1) == 4 and len(polygon2) == 4:
            data = '{}"area1": {},"area2": {}{}'.format('{',polygon1,polygon2,'}') 
            insert_query="truncate table danger_area_polygons;insert into danger_area_polygons values('1001','2001','{}');commit;".format(data)   
            exec_db_command('gen_poly',insert_query)                       
            cv.setMouseCallback("IMAGE", dummy_callback)  
        
         
def dummy_callback(event, x, y, flags, param): 
    pass
   
def draw_polygons(frame):
    if len(polygon1) == 4:
        cv.polylines(frame, np.array([polygon1]), True, (0, 0, 255), 2)         
    if len(polygon2) == 4:
        cv.polylines(frame, np.array([polygon2]), True, (0, 0, 255), 2)        

def genrate_polygon(video_path): 
    global frame               
    cap = cv.VideoCapture(video_path)               
    ret, frame = cap.read()                         
    cv.imshow("IMAGE", frame)                       
    cv.setMouseCallback("IMAGE", click_event)                      
    cv.waitKey(0)
    cv.destroyAllWindows()
    
print('genrate_polygon(video_path) : to generate new polygon coords ')
print('exec_db_command(fetch,cords) : to fetch polygon cords from db')

