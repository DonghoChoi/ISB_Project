#!/usr/bin/python
# Author: Dongho Choi

import math
import time
import pandas as pd
from math import log
from sshtunnel import SSHTunnelForwarder # for SSH connection
import pymysql.cursors # MySQL handling API
import sys
sys.path.append("./configs/")
import server_config # (1) info2_server (2) exploration_db


if __name__ == "__main__":

    # READ DATA FROM SERVER
    #read_Data_from_Server()
    # Server connection
    server = SSHTunnelForwarder(
        (server_config.info2_server['host'], 22),
        ssh_username=server_config.info2_server['user'],
        ssh_password=server_config.info2_server['password'],
        remote_bind_address=('127.0.0.1', 3306))

    server.start()

    connection = pymysql.connect(host='127.0.0.1',
                                 port=server.local_bind_port,
                                 user=server_config.exploration_db['user'],
                                 password=server_config.exploration_db['password'],
                                 db=server_config.exploration_db['database'])
    connection.autocommit(True)
    cursor = connection.cursor()
    print("MySQL connection established.")

    # Get the participants list from the table of 'final_participants'
    df_participants = pd.read_sql('SELECT * FROM final_participants', con=connection)
    print("Participants Table READ")

    df_user_pages_visit_list = pd.read_sql('SELECT * FROM user_pages_visit_list', con=connection)
    print("User pages visit list Table Read")

    # READ AND FILL THE PARTICIPANTS LIST WITH COMBINATIONS
    participants_list = df_participants['userID'].tolist()
    num_participants = len(participants_list) # number of participants
    print('number of participants:{0}'.format(num_participants))

    ## Measures related to the online browsing
    for i in range(0, num_participants):
        current_userID = participants_list[i]
        print("current userID - ",current_userID)

        df_temp_visits = df_user_pages_visit_list.loc[df_user_pages_visit_list['userID']==current_userID]
        df_temp_visits = df_temp_visits.sort_values(['visit_times','spent_time'])
        print(df_temp_visits)
        user_total_visits = df_temp_visits['visit_times'].sum()
        user_total_pages = len(df_temp_visits)
        print("user_total_visits - {0}, user_total_pages - {1}".format(user_total_visits,user_total_pages))

        var_D = 0
        for j in range(0,len(df_temp_visits)):
            var_p_j = (df_temp_visits.iloc[j]['visit_times'])/user_total_visits
            var_D = var_D - var_p_j * log(var_p_j,user_total_pages)
            print("var_D = ",var_D)

        var_L = 0
        k = user_total_pages//3
        for j in range(0,k):
            var_p_j = (df_temp_visits.iloc[j]['visit_times'])/user_total_visits
            var_L = var_L + var_p_j
            print("val_L = ",var_L)

        sql = "INSERT INTO user_online_diversity (userID,total_domains,online_diversity,online_loyalty) VALUES (" + str(
                current_userID) + "," + str(user_total_pages) + "," + str(
                var_D) + "," + str(var_L) + ");"
        print(sql)
        cursor.execute(sql)

    server.stop()
    print("END")