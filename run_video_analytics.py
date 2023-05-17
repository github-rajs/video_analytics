
from ultralytics import YOLO
import torch
import cv2
from datetime import datetime,time
import time
import numpy as np
import json
from IPython.display import clear_output
import logging
import psycopg2
from config import DBCONN,YOLO_MODEL


#load model
model = YOLO(YOLO_MODEL.weight_file)
model.fuse()
CLASS_NAMES_DICT = model.model.names

#color code for detection bbox
color_codes={0:(0,0,255), 1:(0,255,0), 2:(0,255,0), 3:(0,255,0), 4:(0,0,255), 5:(0,0,255), 6:(0,0,255), 7:(0,255,0)}

#location coordinates to print warning messages
warning_msg_region={0:(450,200), 4:(45,250), 5:(45,300), 6:(45,350), 7:(45,400)}

#misc
conf_threshold=0.2
fps_per_sec=20
latency_between_frames=5

#to process alerts
shoes_id=7
non_safety_ids=[0,4,5,6,shoes_id]
non_safety_idss=non_safety_ids[0:-1]
"""refered from variable non_safety_ids.[0,0] refers to alert count and time difference in sec"""
non_safety_ids_json={0:[0,'00:00:00'],4:[0,'00:00:00'],5:[0,'00:00:00'],6:[0,'00:00:00'],20:[0,'00:00:00']} # 20 for crossing danger line
capture_person_image_dir='tmp/'

#control alert frequency
alert_threshold_count=200
alert_time_thresold_sec=20 

#database related variables
host=DBCONN.host
ip=DBCONN.ip
port=DBCONN.port
user_name=DBCONN.user_name
passwd=DBCONN.passwd
database=DBCONN.database
table=DBCONN.table1

#to increase/decrease polygon area(adjust line detection)
ald=0  

########################################## END OF VARIABLE DECLARATIONS ##########################################


create_table_ddl="CREATE TABLE IF NOT EXISTS video_analytics_data(\
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

fetch_polygon_cords_query="select polygon_json from danger_area_polygons;"

connection = psycopg2.connect(user=user_name,
                              password=passwd,
                              host=host,
                              port=port,
                              database=database)
cursor = connection.cursor()

cursor.execute(fetch_polygon_cords_query)
output = cursor.fetchall()
op=output[0][0]
area_1 = op['area1'] 
area_2 =  op['area2']


def store_data(alert_id,alert_time,tot_alerts,cap_img_name):
    alert_id=alert_id
    alert_time=alert_time
    tot_alerts=tot_alerts
    img_name=cap_img_name
    
    insert_query="insert into video_analytics_data values\
    ('bangalore','station01','electric','cam01',now(),{},'{}','{}',{},'{}');commit;".format(alert_id,str(CLASS_NAMES_DICT[alert_id]),alert_time,tot_alerts,img_name)
    print(insert_query)
    
    try:
        cursor.execute(insert_query)
    except (Exception, psycopg2.Error) as error :
        print(error)

           
def send_alert(alert_id,frame,tot_alert_count):
    alert_time=time.strftime("%m_%d_%H_%M_%S", time.localtime())
    
    if alert_id == 20:
        print('WARNING ALERT! : Person Crossing Danger Line Detected')
        to_renmae=capture_person_image_dir+alert_time+'_'+'danger_line_cross_'+str(alert_id)+'.jpg'
        cv2.imwrite(to_renmae,frame)
        store_data(alert_id,alert_time,tot_alert_count,to_renmae)
    else:
        print('WARNING ALERT! : {} Detected'.format(CLASS_NAMES_DICT[alert_id]))
        to_renmae=capture_person_image_dir+alert_time+'_'+str(CLASS_NAMES_DICT[alert_id])+'_'+str(alert_id)+'.jpg'
        cv2.imwrite(to_renmae,frame)
        store_data(alert_id,alert_time,tot_alert_count,to_renmae)

def process_alerts(alert_id,frame): 
    """alerts will be triggered when alert count and time interval reaches its threshold"""
        
    curr_time=time.strftime("%H:%M:%S", time.localtime())
    curr_time_t=datetime.strptime(curr_time, "%H:%M:%S")
    
    if non_safety_ids_json[alert_id][0] == 1:
        non_safety_ids_json[alert_id][1]=curr_time
    
    first_alert_time=non_safety_ids_json[alert_id][1]
    first_alert_time_t=datetime.strptime(first_alert_time, "%H:%M:%S")
    
    delta=curr_time_t - first_alert_time_t
    delta_sec=int(delta.total_seconds())
    
    if non_safety_ids_json[alert_id][0] >= alert_threshold_count and delta_sec>=alert_time_thresold_sec:
        send_alert(alert_id,frame,non_safety_ids_json[alert_id][0])
        print('{} alerts generated in {} seconds and are supressed'.format(str(non_safety_ids_json[alert_id][0]),str(delta_sec)))
        non_safety_ids_json[alert_id][0]=0  
        non_safety_ids_json[alert_id][1]='00:00:00'  
        print('alert count and time reset to : {} , {}'.format(str(non_safety_ids_json[alert_id][0]),str(non_safety_ids_json[alert_id][1])))
    else:
        non_safety_ids_json[alert_id][0]=non_safety_ids_json[alert_id][0]+1
        
         
def create_alert(cls_id,orig_images,cords_list,shoes_xyxy):
    if cls_id in non_safety_idss:
        process_alerts(cls_id,orig_images)
        warning_message="Warning!..{} detected".format(CLASS_NAMES_DICT[cls_id])
        cv2.putText(orig_images, warning_message, warning_msg_region[cls_id], cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
    else:
        pass
    if len(shoes_xyxy) > 0:
          orig_images=detect_person_crossline(orig_images,shoes_xyxy)    
    else:
          pass
    return orig_images


def detect_person_crossline(frame,shoe_boxes):
    for shoe_box in shoe_boxes:
        #x1, y1, x2, y2 = shoe_box

        if shoe_box[0] > area_1[0][0] and shoe_box[2] < area_1[1][0] and shoe_box[1] > area_1[0][1] and shoe_box[3] < area_1[1][1]:
            cv2.putText(frame, "Warning! Person crossed the Yellow Line", (45, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            process_alerts(20,frame)
        elif shoe_box[0] > area_2[0][0] and shoe_box[2] < area_2[1][0] and shoe_box[1] > area_2[0][1] and shoe_box[3] < area_2[1][1]:
            cv2.putText(frame, "Warning! Person crossed the Yellow Line", (45, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            process_alerts(20,frame)
        else:
            pass
    return frame 
#Logic 
#   (X1 > x1) & (X2 < X2) &(Y1 > y1) & (Y2 < Y2)
#   xyxy=[12,323,343,322]
#   line1 = [[622, 283], [421, 719]]
#   line2 = [[422, 253], [221, 119]]

#shoe_box[0] = bbox_x1 
#shoe_box[2] = bbox_x2
#shoe_box[1] = bbox_y1
#shoe_box[3] = bbox_y2
#
#line1[0][0] = x1
#line1[1][0] = x2
#line1[0][1] = y1
#line1[1][1] = y2     
    
def plot_bbox(results):
     for result in results:
         xyxys=result.boxes.xyxy.cpu().numpy().astype(int)
         classids=result.boxes.cls.cpu().numpy().astype(int)
         confs=result.boxes.conf.cpu().numpy().astype(float)
         orig_images=result.orig_img
         shoes_index_pos=np.where(classids==shoes_id)    
         shoe_bbox=xyxys[shoes_index_pos]
         #print(shoes_index_pos)
         #print(shoe_bbox)

     if len(confs) != 0:   
         for i in range(0,len(confs),1):
             xyxy=xyxys[i]
             cls_id=classids[i]
             conf=confs[i]
             if conf > conf_threshold:#and cls_id in non_safety_ids:
                torch_xyxy = torch.tensor([xyxy])
                x1, y1, x2, y2 = torch_xyxy.squeeze().tolist()
                cords_list=[x1,y1,x2,y2]
                res=str(CLASS_NAMES_DICT[cls_id])
                frame_color=color_codes[cls_id]
                cv2.rectangle(orig_images, (int(x1), int(y1)), (int(x2), int(y2)), frame_color, 1) 
                #cv2.putText(orig_images,res, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, frame_color, 1)
                orig_images=create_alert(cls_id,orig_images,cords_list,shoe_bbox)
             else:
                 pass      
     else:
          pass  
     return orig_images

def stream_vid(capture_index):    
    video = cv2.VideoCapture(capture_index)
    assert video.isOpened()
    video.set(cv2.CAP_PROP_FPS, fps_per_sec)
    video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    video.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)
    
    while True:
        start_time = time.time()
        ret, frame = video.read()
        assert ret
        
        results = model(frame)
        frame =  plot_bbox(results)
        
        end_time = time.time()
        fps = 1/np.round(end_time - start_time, 2)

        cv2.putText(frame, f'FPS: {int(fps)}', (10,600), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 1)
        cv2.polylines(frame,[np.array(area_1,np.int32)],True,(0,0,255),1)
        cv2.polylines(frame,[np.array(area_2,np.int32)],True,(0,0,255),1)
        cv2.imshow('Video Analytics', frame)
        #clear_output(wait=True)
        if cv2.waitKey(latency_between_frames) == ord('q'):
            break

    video.release()
    cv2.destroyAllWindows()
