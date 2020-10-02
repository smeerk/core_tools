import psycopg2
import numpy as np
conn = psycopg2.connect("dbname=test user=stephan")
cur = conn.cursor()
import json
conn.commit()
import time
from core_tools.data.SQL.connector import sample_info
from core_tools.data.SQL.connector import set_up_data_storage

set_up_data_storage('localhost', 5432, 'stephan', 'magicc', 'test', '5dot', 'XLD', 'SQ19_blabla')

def insert_new_measurement_in_overview_table(exp_name):
		statement = "INSERT INTO measurements_overview "
		statement += "(set_up, project, sample, exp_name) VALUES ('"
		statement += str(sample_info.set_up) + "', '"
		statement += str(sample_info.project) + "', '"
		statement += str(sample_info.sample) + "', '"
		statement += exp_name + "');"
		return statement

def get_last_meas_id_in_overview_table():
		return "SELECT MAX(id) FROM measurements_overview;" 

def fill_meas_info_in_overview_table(meas_id, measurement_table_name=None, start_time=None, stop_time=None, metadata=None, snapshot=None):
		'''
		fill in the addional data in a record of the measurements overview table.

		Args:
			meas_id (int) : record that needs to be updated
			measurement_table_name (str) : name of the table that contains the raw measurement data
			start_time (long) : time in unix seconds since the epoch
			stop_time (long) : time in unix seconds since the epoch
			metadata (JSON) : json string to be saved in the database
			snapshot (JSON) : snapshot of the exprimental set up
		'''
		statement = ""

		if measurement_table_name is not None:
			statement += "UPDATE measurements_overview SET exp_data_location = '{}' WHERE ID = {};".format(measurement_table_name, meas_id)
		if start_time is not None:
			statement += "UPDATE measurements_overview SET start_time = to_timestamp('{}') WHERE ID = {};".format(start_time, meas_id)
		if stop_time is not None:
			statement += "UPDATE measurements_overview SET stop_time = to_timestamp('{}') WHERE ID = {};".format(stop_time, meas_id)
		if metadata is not None:
			statement += "UPDATE measurements_overview SET metadata = '{}' WHERE ID = {};".format(metadata, meas_id)
		if snapshot is not None:
			statement += "UPDATE measurements_overview SET snapshot = '{}' WHERE ID = {};".format(snapshot, meas_id)

		return statement

def make_new_data_table(name):
		statement = "CREATE TABLE {} ( ".format(name )
		statement += "id INT NOT NULL, "
		statement += "param_id BIGINT, "
		statement += "nth_set INT, "
		statement += "param_id_m_param BIGINT, "
		statement += "setpoint BOOL, "
		statement += "setpoint_local BOOL, "
		statement += "name_gobal varchar(1024), "
		statement += "name varchar(1024) NOT NULL,"
		statement += "label varchar(1024) NOT NULL,"
		statement += "unit varchar(1024) NOT NULL,"
		statement += "depencies varchar(1024), "
		statement += "shape jsonb, "
		statement += "size INT, "
		statement += "oid INT );"
		return statement

state = ['a', 1 , 100]

# stmt = insert_new_measurement_in_overview_table('test_table')
# cur.execute(stmt)

stmt = make_new_data_table('test_table_name')
cur.execute(stmt)
# meas_id = cur.fetchone()[0]

# stmt = fill_meas_info_in_overview_table(meas_id, 'test_table_name', start_time=time.time(), snapshot=json.dumps(state))
# cur.execute(stmt)

conn.commit()
