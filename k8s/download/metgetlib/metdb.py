#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2020 ADCIRC Development Group
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


class Metdb:
    def __init__(self):
        """
        Initializer for the metdb class. The Metdb class will
        generate a database of files and store the indexing in an
        sqlite3 database
        """
        import os

        self.__dbhost = os.environ["METGET_DATABASE_SERVICE_HOST"]
        self.__dbpassword = os.environ["METGET_DATABASE_PASSWORD"]
        self.__dbusername = os.environ["METGET_DATABASE_USER"]
        self.__dbname = os.environ["METGET_DATABASE"]
        self.__gefs_cache = None
        self.__persistent_connection = self.connect()
        self.__persistent_cursor = self.__persistent_connection.cursor()

    def persistent_connection(self):
        return self.__persistent_connection

    def persistent_cursor(self):
        return self.__persistent_cursor

    def connect(self):
        import sys
        import pymysql
        import logging

        logger = logging.getLogger(__name__)

        try:
            return pymysql.connect(
                host=self.__dbhost,
                user=self.__dbusername,
                passwd=self.__dbpassword,
                db=self.__dbname,
                connect_timeout=5,
            )
        except:
            logger.error("Could not connect to MySQL database")
            sys.exit(1)

    def get_nhc_md5(self, mettype, year, basin, storm, advisory=0):
        if mettype == "nhc_btk":
            return self.get_nhc_btk_md5(year, basin, storm)
        elif mettype == "nhc_fcst":
            return self.get_nhc_fcst_md5(year, basin, storm, advisory)
        else:
            raise

    def get_nhc_btk_md5(self, year, basin, storm):
        sql = (
            "SELECT md5 FROM nhc_btk WHERE storm_year = "
            + str(year)
            + " AND BASIN = '"
            + basin
            + "' AND STORM = "
            + str(storm)
            + ";"
        )
        self.persistent_cursor().execute(sql)
        dat = self.persistent_cursor().fetchone()
        if dat:
            md5 = dat[0]
        else:
            md5 = 0
        return md5

    def get_nhc_fcst_md5(self, year, basin, storm, advisory):
        sql = (
            "SELECT md5 FROM nhc_fcst WHERE storm_year = "
            + str(year)
            + " AND BASIN = '"
            + basin
            + "' AND STORM = '"
            + str(storm)
            + "'"
        )

        if advisory:
            sql += " AND ADVISORY = " + advisory

        sql += ";"

        self.persistent_cursor().execute(sql)

        if advisory:
            dat = self.persistent_cursor().fetchone()
            if dat:
                md5 = dat[0]
            else:
                md5 = 0
            return md5
        else:
            mdf5_list = []
            dat = self.persistent_cursor().fetchall()
            for d in dat:
                mdf5_list.append(d[0])
            return mdf5_list

    def has(self, datatype, pair) -> bool:
        if datatype == "hwrf":
            return self.__has_hwrf(pair)
        elif datatype == "coamps":
            return self.__has_coamps(pair)
        elif datatype == "nhc_fcst":
            return self.__has_nhc_fcst(pair)
        elif datatype == "nhc_btk":
            return self.__has_nhc_btk(pair)
        elif datatype == "gefs_ncep":
            return self.__has_gefs(pair)
        else:
            return self.__has_generic(datatype, pair)

    def __has_hwrf(self, pair) -> bool:
        sql = self.__generate_sql_hwrf("None", pair)
        self.persistent_cursor().execute(sql["has"])
        nrows = self.persistent_cursor().fetchone()[0]
        return nrows > 0

    def __has_coamps(self, pair) -> bool:
        sql = self.__generate_sql_coamps("None", pair)
        self.persistent_cursor().execute(sql["has"])
        nrows = self.persistent_cursor().fetchone()[0]
        return nrows > 0

    def __has_nhc_fcst(self, pair) -> bool:
        sql = self.__generate_sql_nhc_fcst("None", pair)
        self.persistent_cursor().execute(sql["has"])
        nrows = self.persistent_cursor().fetchone()[0]
        return nrows > 0

    def __has_nhc_btk(self, pair) -> bool:
        sql = self.__generate_sql_nhc_btk(pair)
        self.persistent_cursor().execute(sql["has"])
        nrows = self.persistent_cursor().fetchone()[0]
        return nrows > 0

    def __has_gefs(self, pair) -> bool:
        sql = self.__generate_sql_gefs_ncep("None", pair)
        self.persistent_cursor().execute(sql["has"])
        nrows = self.persistent_cursor().fetchone()[0]
        return nrows > 0

    def __has_generic(self, datatype, pair) -> bool:
        sql = self.__generate_sql_generic(datatype, "None", pair)
        self.persistent_cursor().execute(sql["has"])
        nrows = self.persistent_cursor().fetchone()[0]
        return nrows > 0

    def add(self, pair, datatype, filepath):
        """
        Adds a file listing to the database
        :param pair: dict containing cycledate and forecastdate
        :param datatype: The table that this file will be added to (i.e. gfsfcst)
        :param filepath: Relative file location
        :return:
        """
        if datatype == "hwrf":
            sql = self.__generate_sql_hwrf(filepath, pair)
        elif datatype == "coamps":
            sql = self.__generate_sql_coamps(filepath, pair)
        elif datatype == "nhc_fcst":
            sql = self.__generate_sql_nhc_fcst(filepath, pair)
        elif datatype == "nhc_btk":
            sql = self.__generate_sql_nhc_btk(filepath, pair)
        elif datatype == "gefs_ncep":
            sql = self.__generate_sql_gefs_ncep(filepath, pair)
        else:
            sql = self.__generate_sql_generic(datatype, filepath, pair)

        self.persistent_cursor().execute(sql["has"])
        nrows = self.persistent_cursor().fetchone()[0]
        if nrows == 0:
            self.persistent_cursor().execute(sql["insert"])
        elif nrows > 0 and datatype == "nhc_btk":
            self.persistent_cursor().execute(sql["update"])

        self.persistent_connection().commit()

    def status(self, jsonfile):
        """
        Writes a json file which contains the latest state of the meteorological database
        :param jsonfile: output json file
        """
        import json
        import socket
        from datetime import datetime

        jsondata = {"metget": {}}
        jsondata["metget"]["hwrf"] = self.hwrf_status()
        jsondata["metget"]["gfs-ncep"] = self.generic_status("gfs_ncep", 384)
        jsondata["metget"]["nam-ncep"] = self.generic_status("nam_ncep", 84)
        jsondata["metget"]["nhc"] = {}
        (
            jsondata["metget"]["nhc"]["forecast"],
            jsondata["metget"]["nhc"]["best_track"],
        ) = self.nhc_status()
        jsondata["metget"]["state"] = {
            "last_fetch": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "host": socket.gethostname(),
        }

        with open(jsonfile, "w") as statfile:
            json.dump(jsondata, statfile, indent=1)

    def generic_status(self, table, desired_len):
        """
        Generates json status object from the avaialable NCEP-GFS data
        :return: json status object
        """
        from datetime import datetime

        db = self.connect()

        sql = "SELECT DISTINCT FORECASTCYCLE FROM " + table + " ORDER BY FORECASTCYCLE"
        rows = self.persistent_cursor().execute(sql).fetchall()

        if len(rows) < 1:
            return {
                "min_forecast_date": None,
                "max_forecast_date": None,
                "first_available_cycle": None,
                "last_available_cycle": None,
                "latest_complete_forecast": None,
                "latest_complete_forecast_start": None,
                "latest_complete_forecast_end": None,
                "latest_complete_forecast_length": None,
            }

        cyc_min = rows[0][0]
        if len(rows) > 1:
            cyc_max = rows[-1][0]
        else:
            cyc_max = cyc_min
        latest_complete = None
        latest_start = None
        latest_end = None
        latest_length = None
        cycle_list = []
        for r in reversed(rows):
            sql = (
                "SELECT MIN(DATE) AS FIRST, MAX(DATE) AS LAST FROM "
                + table
                + " WHERE FORECASTCYCLE = datetime('"
                + r[0]
                + "')"
            )
            rr = self.persistent_cursor().execute(sql).fetchall()
            start = datetime.strptime(rr[0][0], "%Y-%m-%d %H:%M:%S")
            end = datetime.strptime(rr[0][1], "%Y-%m-%d %H:%M:%S")
            avail_len = (end - start).total_seconds() / 3600
            if avail_len >= desired_len:
                latest_complete = r[0]
                cycle_list.append(r[0])
                latest_start = start.strftime("%Y-%m-%d %H:%M:%S")
                latest_end = end.strftime("%Y-%m-%d %H:%M:%S")
                latest_length = avail_len
                break

        sql = "SELECT MIN(DATE) AS FIRST, MAX(DATE) AS LAST FROM " + table
        rows = self.persistent_cursor().execute(sql).fetchall()
        fcst_min = rows[0][0]
        fcst_max = rows[0][1]

        return {
            "min_forecast_date": fcst_min,
            "max_forecast_date": fcst_max,
            "first_available_cycle": cyc_min,
            "last_available_cycle": cyc_max,
            "latest_complete_forecast": latest_complete,
            "latest_complete_forecast_start": latest_start,
            "latest_complete_forecast_end": latest_end,
            "latest_complete_forecast_length": latest_length,
            "cycle_list": cycle_list,
        }

    def hwrf_status(self):
        """
        Generates the json status object from the database for the available HWRF data
        :return: json status object
        """
        import sqlite3
        from datetime import datetime

        db = sqlite3.connect(self.__db)

        # Use SQL to generate a distinct list of storms and then
        # iterate over them to determine the available forecast data
        sql = "SELECT DISTINCT stormname FROM hwrf"
        stormlist = []
        rows = self.persistent_cursor().execute(sql).fetchall()
        for row in rows:
            stormlist.append({"storm": row[0]})

        hwrf_stat = []

        # For each storm, determine the availability of data
        for s in stormlist:
            sql = (
                "SELECT DATE FROM hwrf WHERE stormname = '"
                + s["storm"]
                + "' ORDER BY DATE"
            )
            rows = self.persistent_cursor().execute(sql).fetchall()
            fcst_min = rows[0][0]
            fcst_max = rows[-1][0]
            sql = (
                "SELECT DISTINCT FORECASTCYCLE FROM hwrf WHERE stormname = '"
                + s["storm"]
                + "' ORDER BY FORECASTCYCLE"
            )
            rows = self.persistent_cursor().execute(sql).fetchall()
            cyc_min = rows[0][0]
            cyc_max = rows[-1][0]

            latest_complete = None
            latest_start = None
            latest_end = None
            latest_length = None
            time_since_forecast = 0
            cycle_list = []

            # Backwards loop to see the most recent complete forecast cycle
            for f in reversed(rows):
                sql = (
                    "SELECT MIN(DATE) AS FIRST, MAX(DATE) AS LAST FROM hwrf WHERE stormname = '"
                    + s["storm"]
                    + "' AND FORECASTCYCLE = datetime('"
                    + f[0]
                    + "') ORDER BY DATE"
                )
                r = self.persistent_cursor().execute(sql).fetchall()
                start = datetime.strptime(r[0][0], "%Y-%m-%d %H:%M:%S")
                end = datetime.strptime(r[0][1], "%Y-%m-%d %H:%M:%S")
                avail_len = (end - start).total_seconds() / 3600
                if avail_len >= 126:
                    cycle_list.append(f[0])
                    latest_start = start.strftime("%Y-%m-%d %H:%M:%S")
                    latest_end = end.strftime("%Y-%m-%d %H:%M:%S")
                    latest_length = avail_len
                    latest_complete = f[0]
                    time_since_forecast = datetime.now() - datetime.strptime(
                        f[0], "%Y-%m-%d %H:%M:%S"
                    )
                    time_since_forecast = time_since_forecast.total_seconds() / 86400
                    break

            # Assemble a storm object. We're only going to write data available in the last 10 days
            if time_since_forecast < 10:
                hwrf_stat.append(
                    {
                        "storm": s["storm"],
                        "min_forecast_date": fcst_min,
                        "max_forecast_date": fcst_max,
                        "first_available_cycle": cyc_min,
                        "last_available_cycle": cyc_max,
                        "latest_complete_forecast": latest_complete,
                        "latest_complete_forecast_start": latest_start,
                        "latest_complete_forecast_end": latest_end,
                        "latest_complete_forecast_length": latest_length,
                        "cycle_list": cycle_list,
                    }
                )

        return hwrf_stat

    def nhc_status(self):
        import sqlite3
        from .nhcdownloader import basin2string

        nhc_btk_stat = []
        nhc_fcst_stat = []
        latest_forecast_advisory = 0

        sql = "SELECT DISTINCT year, basin, storm FROM nhc_fcst ORDER BY year, basin, storm, advisory;"
        for f in self.persistent_cursor().execute(sql):
            forecast_advisory_list = []
            yr = f[0]
            bs = f[1]
            st = f[2]
            sql = (
                "SELECT advisory, advisory_start, advisory_end, advisory_duration_hr FROM nhc_fcst WHERE year = "
                + str(yr)
                + " and basin = '"
                + bs
                + "' and storm = "
                + str(st)
                + " ORDER BY advisory;"
            )
            crsr2 = db.execute(sql)
            for ff in crsr2:
                adv_data = {
                    "advisory": ff[0],
                    "start": ff[1],
                    "end": ff[2],
                    "duration": ff[3],
                }
                forecast_advisory_list.append(adv_data)
                latest_forecast_advisory = ff[0]

            nhc_fcst_stat.append(
                {
                    "year": yr,
                    "basin_abbrev": bs,
                    "basin_string": basin2string(bs),
                    "storm": st,
                    "latest_forecast_advisory": latest_forecast_advisory,
                    "available_forecast_advisories": forecast_advisory_list,
                }
            )

        sql = (
            "SELECT DISTINCT year, basin, storm, advisory_start, advisory_end, advisory_duration_hr, accessed "
            "FROM nhc_btk ORDER BY year, basin, storm;"
        )
        for f in self.persistent_cursor().execute(sql):
            nhc_btk_stat.append(
                {
                    "year": f[0],
                    "basin": f[1],
                    "basin_string": basin2string(f[1]),
                    "storm": f[2],
                    "start": f[3],
                    "end": f[4],
                    "duration": f[5],
                    "last_update": f[6],
                }
            )

        return nhc_fcst_stat, nhc_btk_stat

    @staticmethod
    def __generate_sql_generic(datatype, filepath, pair) -> dict:
        import math

        cdate = str(pair["cycledate"])
        fdate = str(pair["forecastdate"])
        tau = int(
            math.floor(
                (pair["forecastdate"] - pair["cycledate"]).total_seconds() / 3600.0
            )
        )
        url = pair["grb"]

        sqlhas = (
            "SELECT Count(*) FROM {:s} WHERE "
            "FORECASTCYCLE = '{:s}' AND FORECASTTIME = '{:s}' "
            "AND FILEPATH = '{:s}';".format(datatype, cdate, fdate, filepath)
        )

        sqlinsert = (
            "INSERT INTO {:s} (FORECASTCYCLE,FORECASTTIME,TAU,FILEPATH,URL,ACCESSED) "
            "VALUES('{:s}','{:s}',{:d},'{:s}','{:s}', now());".format(
                datatype, cdate, fdate, tau, filepath, url
            )
        )
        return {"has": sqlhas, "insert": sqlinsert, "update": None}

    @staticmethod
    def __generate_sql_gefs_ncep(filepath, pair):
        import math

        cdate = str(pair["cycledate"])
        fdate = str(pair["forecastdate"])
        member = str(pair["ensemble_member"])
        url = pair["grb"]
        tau = int(
            math.floor(
                (pair["forecastdate"] - pair["cycledate"]).total_seconds() / 3600.0
            )
        )

        sqlhas = (
            "SELECT Count(*) FROM gefs_fcst WHERE FORECASTCYCLE = '{:s}' "
            "AND FORECASTTIME = '{:s}' AND ENSEMBLE_MEMBER = '{:s}';".format(
                cdate, fdate, member
            )
        )

        sqlinsert = (
            "INSERT INTO gefs_fcst "
            "(FORECASTCYCLE,FORECASTTIME,ENSEMBLE_MEMBER,TAU,FILEPATH,URL,ACCESSED)"
            "VALUES('{:s}','{:s}','{:s}','{:d}','{:s}','{:s}',now());".format(
                cdate, fdate, member, tau, filepath, url
            )
        )

        return {"has": sqlhas, "insert": sqlinsert, "update": None}

    @staticmethod
    def __generate_nhc_vars_from_pair(pair):
        year = pair["year"]
        storm = pair["storm"]
        basin = pair["basin"]

        if "md5" in pair:
            md5 = pair["md5"]
        else:
            md5 = "None"

        if "advisory_start" in pair:
            start = str(pair["advisory_start"])
        else:
            start = "None"

        if "advisory_end" in pair:
            end = str(pair["advisory_end"])
        else:
            end = "None"

        if "advisory_duration_hr" in pair:
            duration = str(pair["advisory_duration_hr"])
        else:
            duration = "None"

        return year, storm, basin, md5, start, end, duration

    @staticmethod
    def __generate_sql_nhc_btk(filepath, pair):
        import json

        (
            year,
            storm,
            basin,
            md5,
            start,
            end,
            duration,
        ) = Metdb.__generate_nhc_vars_from_pair(pair)

        if "geojson" in pair.keys():
            geojson = json.dumps(pair["geojson"])
        else:
            geojson = "none"

        sqlhas = (
            "SELECT Count(*) FROM nhc_btk WHERE storm_year = "
            + str(year)
            + " AND BASIN = '"
            + basin
            + "' AND STORM = "
            + str(storm)
            + ";"
        )
        sqlinsert = (
            "INSERT INTO nhc_btk (STORM_YEAR,BASIN,STORM,ADVISORY_START,ADVISORY_END,"
            "ADVISORY_DURATION_HR,FILEPATH,MD5,ACCESSED,GEOJSON) VALUES("
            + str(year)
            + ",'"
            + basin
            + "',"
            + str(storm)
            + ", '"
            + start
            + "', '"
            + end
            + "', "
            + duration
            + ",'"
            + filepath
            + "', '"
            + md5
            + "', now()"
            + ", '"
            + geojson
            + "');"
        )
        sqlupdate = (
            "UPDATE nhc_btk SET ACCESSED = now(), MD5 = '"
            + md5
            + "', ADVISORY_START = '"
            + start
            + "', ADVISORY_END = '"
            + end
            + "', ADVISORY_DURATION_HR = "
            + duration
            + ", GEOJSON = '"
            + geojson
            + "' WHERE storm_year = "
            + str(year)
            + " AND BASIN = '"
            + basin
            + "' AND STORM = "
            + str(storm)
            + ";"
        )
        return {"has": sqlhas, "insert": sqlinsert, "update": sqlupdate}

    @staticmethod
    def __generate_sql_nhc_fcst(filepath, pair):
        import json

        (
            year,
            storm,
            basin,
            md5,
            start,
            end,
            duration,
        ) = Metdb.__generate_nhc_vars_from_pair(pair)
        advisory = pair["advisory"]

        if "geojson" in pair.keys():
            geojson = json.dumps(pair["geojson"])
        else:
            geojson = "none"

        sqlhas = (
            "SELECT Count(*) FROM nhc_fcst WHERE storm_year = "
            + str(year)
            + " AND ADVISORY = '"
            + advisory
            + "' AND BASIN = '"
            + basin
            + "' AND STORM = "
            + str(storm)
            + ";"
        )
        sqlinsert = (
            "INSERT INTO nhc_fcst (STORM_YEAR,BASIN,STORM,ADVISORY,ADVISORY_START,ADVISORY_END,"
            "ADVISORY_DURATION_HR,FILEPATH,MD5,ACCESSED,GEOJSON) VALUES("
            + str(year)
            + ",'"
            + basin
            + "',"
            + str(storm)
            + ",'"
            + advisory
            + "', '"
            + start
            + "', '"
            + end
            + "', "
            + duration
            + ",'"
            + filepath
            + "', '"
            + md5
            + "', now()"
            + ", '"
            + geojson
            + "');"
        )
        sqlupdate = ""
        return {"has": sqlhas, "insert": sqlinsert, "update": sqlupdate}

    @staticmethod
    def __generate_sql_hwrf(filepath, pair):
        import math

        cdate = str(pair["cycledate"])
        fdate = str(pair["forecastdate"])
        url = pair["grb"]
        name = pair["name"]
        tau = int(
            math.floor(
                (pair["forecastdate"] - pair["cycledate"]).total_seconds() / 3600.0
            )
        )

        sqlhas = (
            "SELECT Count(*) FROM hwrf WHERE FORECASTCYCLE = '{:s}' AND "
            "FORECASTTIME = '{:s}' AND STORMNAME = '{:s}' AND FILEPATH = '{:s}';".format(
                cdate, fdate, name, filepath, url
            )
        )

        sqlinsert = (
            "INSERT INTO hwrf (FORECASTCYCLE,FORECASTTIME,STORMNAME,TAU,FILEPATH,URL,ACCESSED) "
            "VALUES('{:s}', '{:s}', '{:s}', {:d}, '{:s}', '{:s}', now());".format(
                cdate, fdate, name, tau, filepath, url
            )
        )

        return {"has": sqlhas, "insert": sqlinsert, "update": None}

    @staticmethod
    def __generate_sql_coamps(filepath, pair):
        import math

        cdate = str(pair["cycledate"])
        fdate = str(pair["forecastdate"])
        name = pair["name"]
        tau = int(
            math.floor(
                (pair["forecastdate"] - pair["cycledate"]).total_seconds() / 3600.0
            )
        )

        sqlhas = "SELECT Count(*) FROM coamps_tc where stormname = '{}' and forecastcycle = '{}' and forecasttime = '{}';".format(
            name,
            cdate,
            fdate,
        )
        sqlinsert = "INSERT INTO coamps_tc(stormname, forecastcycle, forecasttime, filepath, accessed, tau) VALUES('{}', '{}', '{}', '{}', now(), '{}');".format(
            name, cdate, fdate, filepath, tau
        )
        return {"has": sqlhas, "insert": sqlinsert, "update": None}
