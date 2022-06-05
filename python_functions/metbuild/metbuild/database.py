class Database:
    def __init__(self):
        import sys
        import pymysql
        from pymysql import MySQLError
        import boto3
        import os
        self.__dbhost = os.environ["DBSERVER"]
        self.__dbpassword = os.environ["DBPASS"]
        self.__dbusername = os.environ["DBUSER"]
        self.__dbname = os.environ["DBNAME"]
        self.__bucket = os.environ["BUCKET"]
        self.__s3client = boto3.client("s3")
        try:
            self.__db = pymysql.connect(host=self.__dbhost,
                                        user=self.__dbusername,
                                        passwd=self.__dbpassword,
                                        db=self.__dbname,
                                        connect_timeout=5)
            self.__cursor = self.__db.cursor()
        except MySQLError as e:
            print('Got error {!r}, errno is {}'.format(e, e.args[0]))
            sys.exit(1)

    def cursor(self):
        return self.__cursor

    def s3client(self):
        return self.__s3client

    def bucket(self):
        return self.__bucket

    def generate_file_list(self, service, param, start, end, storm, nowcast, multiple_forecasts):
        import sys
        if service == "gfs-ncep":
            return self.generate_generic_file_list("gfs_ncep", param, start, end, nowcast, multiple_forecasts)
        elif service == "nam-ncep":
            return self.generate_generic_file_list("nam_ncep", param, start, end, nowcast, multiple_forecasts)
        elif service == "hwrf":
            return self.generate_hwrf_file_list(start, end, storm, nowcast, multiple_forecasts)
        elif service == "coamps-tc":
            return self.generate_coamps_file_list(start, end, storm, nowcast, multiple_forecasts)
        else:
            print("ERROR: Invalid data type")
            sys.exit(1)

    def generate_generic_file_list(self, table, param_type, start, end, nowcast, multiple_forecasts):
        from datetime import timedelta
        if table == "nam_ncep" and param_type == "rain":
            return self.generate_generic_file_list_ignore_zero_hour(table, start, end)
        else:
            if nowcast:
                return self.generate_generic_file_list_nowcast(table, start, end)
            else:
                if multiple_forecasts:
                    return self.generate_generic_file_list_multiple_forecasts(table, start, end)
                else:
                    return self.generate_generic_file_list_single_forecast(table, start, end)

    def generate_generic_file_list_ignore_zero_hour(self, table, start, end):
        """ 
        This is a very specific use case. The NAM model doesn't report precip rate in the operational setting
        so we need to use accumulated precip, however, at the zero hour, no precip has accumulated. Rather than
        constantly interpolating to/from zero, we will just ignore zero hour forecasts when the rainfall is requested
        from the NAM model
        """
        sql = "select t1.id,t1.forecastcycle,t1.forecasttime,t1.filepath from " + table + \
              " t1 JOIN(select forecasttime, max(id) id FROM "+table+" group by forecasttime order by forecasttime) t2 " \
              "ON t1.id = t2.id AND t1.forecasttime = t2.forecasttime AND t1.forecasttime >= '" + start.strftime(
              "%Y-%m-%d %H:%M:%S") + "' AND t1.forecasttime <= '" + end.strftime(
              "%Y-%m-%d %H:%M:%S") + "' AND t1.forecastcycle != t1.forecasttime;"
        self.cursor().execute(sql)
        rows = self.cursor().fetchall()
        return_list = []
        for f in rows:
            return_list.append([f[2], f[3]])
        return return_list

    def generate_generic_file_list_nowcast(self, table, start, end):
        sql = "select t1.id,t1.forecastcycle,t1.forecasttime,t1.filepath from " + table + \
             " t1 JOIN(select forecasttime, max(id) id FROM "+table+" group by forecasttime order by forecasttime) t2 " \
             "ON t1.id = t2.id AND t1.forecasttime = t2.forecasttime AND t1.forecastcycle >= '" + start.strftime(
             "%Y-%m-%d %H:%M:%S") + "' AND t1.forecastcycle <= '" + end.strftime(
             "%Y-%m-%d %H:%M:%S") + "' AND t1.forecastcycle = t1.forecasttime;"
        self.cursor().execute(sql)
        rows = self.cursor().fetchall()
        return_list = []
        for f in rows:
            return_list.append([f[2], f[3]])
        return return_list

    def generate_generic_file_list_multiple_forecasts(self, table, start, end):
        sql = "select t1.id,t1.forecastcycle,t1.forecasttime,t1.filepath from " + table + \
              " t1 JOIN(select forecasttime, max(id) id FROM "+table+" group by forecasttime order by forecasttime) t2 " \
              "ON t1.id = t2.id AND t1.forecasttime = t2.forecasttime AND t1.forecasttime >= '" + start.strftime(
              "%Y-%m-%d %H:%M:%S") + "' AND t1.forecasttime <= '" + end.strftime(
              "%Y-%m-%d %H:%M:%S") + "';"
        self.cursor().execute(sql)
        rows = self.cursor().fetchall()
        return_list = []
        for f in rows:
            return_list.append([f[2], f[3]])
        return return_list


    def generate_generic_file_list_single_forecast(self, table, start, end):
        sql = "select t1.id,t1.forecastcycle,t1.forecasttime,t1.filepath from " + table + \
              " t1 JOIN(select forecasttime, max(id) id FROM "+table+" group by forecasttime order by forecasttime) t2 " \
              "ON t1.id = t2.id AND t1.forecasttime = t2.forecasttime AND t1.forecasttime >= '" + start.strftime(
              "%Y-%m-%d %H:%M:%S") + "' AND t1.forecasttime <= '" + end.strftime(
              "%Y-%m-%d %H:%M:%S") + "';"
        self.cursor().execute(sql)
        row = self.cursor().fetchone()

        first_time = row[1]

        sql = "select id,forecastcycle,forecasttime,filepath from " + table + \
                " where forecastcycle = '"+first_time.strftime("%Y-%m-%d %H:%M:%S")+"' AND forecasttime >= '"+ \
                start.strftime("%Y-%m-%d %H:%M:%S") + "' AND forecasttime <= '" + end.strftime("%Y-%m-%d %H:%M:%S")+ \
                "' order by forecasttime;"
        self.cursor().execute(sql)
        rows = self.cursor().fetchall()
        return_list = []
        for f in rows:
            return_list.append([f[2], f[3]])
        return return_list


    def generate_hwrf_file_list(self, start, end, storm, nowcast, multiple_forecasts):

       # ... Generate some selections into a temporary table. This essentially duplicates the gfs style database
        sql_tmptable = "create temporary table tmptbl1 select id,forecastcycle,forecasttime,filepath from hwrf where stormname = '"+storm+"';"
        sql_tmptable2 = "create temporary table tmptbl2 select * from tmptbl1;"
        sql = "select t1.id,t1.forecastcycle,t1.forecasttime,t1.filepath from tmptbl1 " \
             " t1 JOIN(select forecasttime, max(id) id FROM tmptbl2 group by forecasttime order by forecasttime) t2 " \
             "ON t1.id = t2.id AND t1.forecasttime = t2.forecasttime AND t1.forecasttime >= '" + start.strftime(
             "%Y-%m-%d %H:%M:%S") + "' AND t1.forecasttime <= '" + end.strftime(
             "%Y-%m-%d %H:%M:%S") + "';"

        self.cursor().execute(sql_tmptable)
        self.cursor().execute(sql_tmptable2)
        self.cursor().execute(sql)
        rows = self.cursor().fetchall()
        return_list = []
        for f in rows:
            return_list.append([f[2], f[3]])
        self.cursor().execute("drop temporary table tmptbl1;")
        self.cursor().execute("drop temporary table tmptbl2;")
        return return_list
    
    def generate_coamps_file_list(self, start, end, storm, nowcast, multiple_forecasts):
        from datetime import timedelta
        if nowcast:
            return self.generate_coamps_file_list_nowcast(start, end, storm)
        else:
            if multiple_forecasts:
                return self.generate_coamps_file_list_multiple_forecasts(start, end, storm)
            else:
                return self.generate_coamps_file_list_single_forecast(start, end, storm)
    
    def generate_coamps_file_list_nowcast(self, start, end, storm):
       # ... Generate some selections into a temporary table. This essentially duplicates the gfs style database
        sql_tmptable = "create temporary table tmptbl1 select id,forecastcycle,forecasttime,filepath from coamps_tc where stormname = '"+storm+"';"
        sql_tmptable2 = "create temporary table tmptbl2 select * from tmptbl1;"
        sql = "select t1.id,t1.forecastcycle,t1.forecasttime,t1.filepath from tmptbl1" \
             " t1 JOIN(select forecasttime, max(id) id FROM tmptbl2 group by forecasttime order by forecasttime) t2 " \
             "ON t1.id = t2.id AND t1.forecasttime = t2.forecasttime AND t1.forecastcycle >= '" + start.strftime(
             "%Y-%m-%d %H:%M:%S") + "' AND t1.forecastcycle <= '" + end.strftime(
             "%Y-%m-%d %H:%M:%S") + "' AND t1.forecastcycle = t1.forecasttime;"
        self.cursor().execute(sql_tmptable)
        self.cursor().execute(sql_tmptable2)
        self.cursor().execute(sql)
        rows = self.cursor().fetchall()
        return_list = []
        for f in rows:
            return_list.append([f[2], f[3]])
        self.cursor().execute("drop temporary table tmptbl1;")
        self.cursor().execute("drop temporary table tmptbl2;")
        return return_list
    
    def generate_coamps_file_list_single_forecast(self, start, end, storm):
       # ... Generate some selections into a temporary table. This essentially duplicates the gfs style database
        sql_tmptable = "create temporary table tmptbl1 select id,forecastcycle,forecasttime,filepath from coamps_tc where stormname = '"+storm+"';"
        sql_tmptable2 = "create temporary table tmptbl2 select * from tmptbl1;"
        sql = "select t1.id,t1.forecastcycle,t1.forecasttime,t1.filepath from tmptbl1" \
              " t1 JOIN(select forecasttime, max(id) id FROM tmptbl2 group by forecasttime order by forecasttime) t2 " \
              "ON t1.id = t2.id AND t1.forecasttime = t2.forecasttime AND t1.forecasttime >= '" + start.strftime(
              "%Y-%m-%d %H:%M:%S") + "' AND t1.forecasttime <= '" + end.strftime(
              "%Y-%m-%d %H:%M:%S") + "';"
        self.cursor().execute(sql_tmptable)
        self.cursor().execute(sql_tmptable2)
        self.cursor().execute(sql)
        row = self.cursor().fetchone()

        first_time = row[1]

        sql = "select id,forecastcycle,forecasttime,filepath from tmptbl1" \
                " where forecastcycle = '"+first_time.strftime("%Y-%m-%d %H:%M:%S")+"' AND forecasttime >= '"+ \
                start.strftime("%Y-%m-%d %H:%M:%S") + "' AND forecasttime <= '" + end.strftime("%Y-%m-%d %H:%M:%S")+ \
                "' order by forecasttime;"
        self.cursor().execute(sql)
        rows = self.cursor().fetchall()
        return_list = []
        for f in rows:
            return_list.append([f[2], f[3]])
        self.cursor().execute("drop temporary table tmptbl1;")
        self.cursor().execute("drop temporary table tmptbl2;")
        return return_list
    
    def generate_coamps_file_list_multiple_forecasts(self, start, end, storm):
       # ... Generate some selections into a temporary table. This essentially duplicates the gfs style database
        sql_tmptable = "create temporary table tmptbl1 select id,forecastcycle,forecasttime,filepath from coamps_tc where stormname = '"+storm+"';"
        sql_tmptable2 = "create temporary table tmptbl2 select * from tmptbl1;"
        sql = "select t1.id,t1.forecastcycle,t1.forecasttime,t1.filepath from tmptbl1" \
              " t1 JOIN(select forecasttime, max(id) id FROM tmptbl2 group by forecasttime order by forecasttime) t2 " \
              "ON t1.id = t2.id AND t1.forecasttime = t2.forecasttime AND t1.forecasttime >= '" + start.strftime(
              "%Y-%m-%d %H:%M:%S") + "' AND t1.forecasttime <= '" + end.strftime(
              "%Y-%m-%d %H:%M:%S") + "';"
        self.cursor().execute(sql_tmptable)
        self.cursor().execute(sql_tmptable2)
        self.cursor().execute(sql)
        rows = self.cursor().fetchall()
        return_list = []
        for f in rows:
            return_list.append([f[2], f[3]])
        self.cursor().execute("drop temporary table tmptbl1;")
        self.cursor().execute("drop temporary table tmptbl2;")
        return return_list

    def check_archive_status(self, filepath) -> bool:
        metadata = self.s3client().head_object(Bucket=self.bucket(),Key=filepath)
        if "x-amz-archive-status" in metadata["ResponseMetadata"]["HTTPHeaders"].keys():
            access = metadata["ResponseMetadata"]["HTTPHeaders"]["x-amz-archive-status"]
            return True
        else:
            return False

    def check_ongoing_restore(self, filepath) -> bool:
        metadata = self.s3client().head_object(Bucket=self.bucket(),Key=filepath)
        if "x-amz-restore" in metadata["ResponseMetadata"]["HTTPHeaders"].keys():
            ongoing = metadata["ResponseMetadata"]["HTTPHeaders"]["x-amz-restore"]
            if ongoing == 'ongoing-request="true"':
                return True
            else:
                return False
        else:
            return False

    def initiate_restore(self, filepath) -> bool:
        ongoing = self.check_ongoing_restore(filepath)
        if not ongoing:
            response = self.s3client().restore_object(Bucket=self.bucket(), Key=filepath, RestoreRequest={"GlacierJobParameters": {"Tier":"Standard"}})
            print("Initiating restore for file: "+filepath)
        else:
            print("Ongoing restore for file: "+filepath)


    def check_initiate_restore(self, db_path, service, time, dry_run=False) -> bool:
        if dry_run:
          return False
        archive_status = self.check_archive_status(db_path)
        if archive_status:
          self.initiate_restore(db_path)
          return True
        return False


    def get_file(self, db_path, service, time, dry_run=False):
        import tempfile
        import os
        fn = db_path.split("/")[-1]
        local_path = tempfile.gettempdir(
        ) + "/" + service + "." + time.strftime("%Y%m%d%H%M") + "." + fn
        if not dry_run:
            if not os.path.exists(local_path):
              self.s3client().download_file(self.bucket(), db_path,
                                            local_path)
        return local_path


    def generate_request_table(self):
        sql = "create table if not exists requests(id INTEGER PRIMARY KEY AUTO_INCREMENT, request_id VARCHAR(36) not null, try INTEGER default 0, status enum('queued', 'running', 'restore', 'error', 'completed') not null, message VARCHAR(1024), start_date DATETIME not null, last_date DATETIME not null, api_key VARCHAR(128), source_ip VARCHAR(128), input_data VARCHAR(8096));"
        self.cursor().execute(sql)

    def query_request_status(self,request_id):
        self.generate_request_table()
        sql = "select try, status, message from requests where request_id = '"+request_id+"';" 
        self.cursor().execute(sql)
        rows = self.cursor().fetchall()

        if len(rows) == 0:
            return {"request": request_id, "try": 0, "status": "unknown", "message": "request_not_found"}
        else:
            return {"request": request_id, "try": rows[0][0], "status": rows[0][1], "message": rows[0][2]}

    def update_request_status(self, request_id, status, message, jsonstr, istry=False,decrement=False):
        from datetime import datetime
        import json
        self.generate_request_table()
        response = self.query_request_status(request_id)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if response["status"] == "unknown":
            jsondata = json.loads(jsonstr)
            apikey = jsondata["api-key"]
            sourceip = jsondata["source-ip"]
            sql = "INSERT INTO requests (request_id, try, status, message, api_key, source_ip, start_date, last_date, input_data) values('"+request_id+"',1,'"+status+"','"+message+"','"+apikey+"','"+sourceip+"','"+now+"','"+now+"','"+jsonstr+"');"
        else:
            jsondata = json.loads(jsonstr)
            apikey = jsondata["api-key"]
            sourceip = jsondata["source-ip"]
            if istry:
                sql = "UPDATE requests SET try = "+str(response["try"]+1)+", status = '"+status+"', message = '"+message+"', last_date = '"+now+"', source_ip = '"+sourceip+"', api_key = '"+apikey+"'  where request_id = '"+request_id+"';"
            elif decrement:
                sql = "UPDATE requests SET try = "+str(response["try"]-1)+", status = '"+status+"', message = '"+message+"', last_date = '"+now+"', source_ip = '"+sourceip+"', api_key = '"+apikey+"'  where request_id = '"+request_id+"';"
            else:
                sql = "UPDATE requests SET status = '"+status+"', message = '"+message+"', last_date = '"+now+"' where request_id = '"+request_id+"';"

        self.cursor().execute(sql)
        self.__db.commit()


