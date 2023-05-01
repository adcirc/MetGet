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

import logging

# Function to genreate a date range
def datespan(startDate, endDate, delta):
    from datetime import datetime, timedelta

    currentDate = startDate
    while currentDate <= endDate:
        yield currentDate
        currentDate += delta


def generate_datatype_key(data_type):
    import pymetbuild

    if data_type == "wind_pressure":
        return pymetbuild.WIND_PRESSURE
    elif data_type == "pressure":
        return pymetbuild.PRESSURE
    elif data_type == "wind":
        return pymetbuild.WIND
    elif data_type == "rain":
        return pymetbuild.RAINFALL
    elif data_type == "humidity":
        return pymetbuild.HUMIDITY
    elif data_type == "temperature":
        return pymetbuild.TEMPERATURE
    elif data_type == "ice":
        return pymetbuild.ICE
    else:
        raise RuntimeError("Invalid data type requested")


def generate_data_source_key(data_source):
    import pymetbuild

    if data_source == "gfs-ncep":
        return pymetbuild.Meteorology.GFS
    elif data_source == "gefs-ncep":
        return pymetbuild.Meteorology.GEFS
    elif data_source == "nam-ncep":
        return pymetbuild.Meteorology.NAM
    elif data_source == "hwrf":
        return pymetbuild.Meteorology.HWRF
    elif data_source == "coamps-tc":
        return pymetbuild.Meteorology.COAMPS
    else:
        raise RuntimeError("Invalid data source")


def generate_met_field(output_format, start, end, time_step, filename, compression):
    import pymetbuild

    if (
        output_format == "ascii"
        or output_format == "owi-ascii"
        or output_format == "adcirc-ascii"
    ):
        return pymetbuild.OwiAscii(start, end, time_step, compression)
    elif output_format == "owi-netcdf" or output_format == "adcirc-netcdf":
        return pymetbuild.OwiNetcdf(start, end, time_step, filename)
    elif output_format == "hec-netcdf":
        return pymetbuild.RasNetcdf(start, end, time_step, filename)
    elif output_format == "delft3d":
        return pymetbuild.DelftOutput(start, end, time_step, filename)
    elif output_format == "raw":
        return None
    else:
        raise RuntimeError("Invalid output format selected: " + output_format)


def generate_met_domain(inputData, met_object, index):
    import pymetbuild

    d = inputData.domain(index)
    output_format = inputData.format()
    if (
        output_format == "ascii"
        or output_format == "owi-ascii"
        or output_format == "adcirc-ascii"
    ):
        if inputData.data_type() == "wind_pressure":
            fn1 = inputData.filename() + "_" + "{:02d}".format(index) + ".pre"
            fn2 = inputData.filename() + "_" + "{:02d}".format(index) + ".wnd"
            fns = [fn1, fn2]
        elif inputData.data_type() == "rain":
            fns = [inputData.filename() + ".precip"]
        elif inputData.data_type() == "humidity":
            fns = [inputData.filename() + ".humid"]
        elif inputData.data_type() == "ice":
            fns = [inputData.filename() + ".ice"]
        else:
            raise RuntimeError("Invalid variable requested")
        if inputData.compression():
            for i, s in enumerate(fns):
                fns[i] = s + ".gz"

        met_object.addDomain(d.grid().grid_object(), fns)
    elif output_format == "owi-netcdf":
        group = d.name()
        met_object.addDomain(d.grid().grid_object(), [group])
    elif output_format == "hec-netcdf":
        if inputData.data_type() == "wind_pressure":
            variables = ["wind_u", "wind_v", "mslp"]
        elif inputData.data_type() == "wind":
            variables = ["wind_u", "wind_v"]
        elif inputData.data_type() == "rain":
            variables = ["rain"]
        elif inputData.data_type() == "humidity":
            variables = ["humidity"]
        elif inputData.data_type() == "ice":
            variables = ["ice"]
        else:
            raise RuntimeError("Invalid variable requested")
        met_object.addDomain(d.grid().grid_object(), variables)
    elif output_format == "delft3d":
        if inputData.data_type() == "wind_pressure":
            variables = ["wind_u", "wind_v", "mslp"]
        elif inputData.data_type() == "wind":
            variables = ["wind_u", "wind_v"]
        elif inputData.data_type() == "rain":
            variables = ["rain"]
        elif inputData.data_type() == "humidity":
            variables = ["humidity"]
        elif inputData.data_type() == "ice":
            variables = ["ice"]
        else:
            raise RuntimeError("Invalid variable requested")
        met_object.addDomain(d.grid().grid_object(), variables)
    else:
        raise RuntimeError("Invalid output format selected: " + output_format)

def merge_nhc_tracks(besttrack_file, forecast_file, output_file) -> str:
    from datetime import datetime, timedelta

    btk_lines = []
    fcst_lines = []

    with open(besttrack_file) as btk:
        for line in btk:
            btk_lines.append({"line": line.rstrip(), "date": datetime.strptime(line.split(",")[2], " %Y%m%d%H")})
    
    with open(forecast_file) as fcst:
        for line in fcst:
            fcst_basetime = datetime.strptime(line.split(",")[2], " %Y%m%d%H")
            fcst_time = int(line.split(",")[5])
            fcst_lines.append({"line": line.rstrip(), "date": fcst_basetime + timedelta(hours=fcst_time)})

    start_date = btk_lines[0]["date"]
    start_date_str = datetime.strftime(start_date, "%Y%m%d%H")

    with open(output_file, "w") as merge:
        for line in btk_lines:
            if line["date"] < fcst_lines[0]["date"]:
                dt = int((line["date"] - start_date).total_seconds()/3600.0)
                dt_str = "{:4d}".format(dt)
                sub1 = line["line"][:8]
                sub2 = line["line"][18:29]
                sub3 = line["line"][33:]
                line_new = sub1 + start_date_str + sub2 + dt_str + sub3
                merge.write(line_new+"\n")

        for line in fcst_lines:
            dt = int((line["date"] - start_date).total_seconds()/3600.0)
            dt_str = "{:4d}".format(dt)
            sub1 = line["line"][:8]
            sub2 = line["line"][18:29]
            sub3 = line["line"][33:]
            line_new = sub1 + start_date_str + sub2 + dt_str + sub3
            merge.write(line_new+"\n")

    return output_file



# Main function to process the message and create the output files and post to S3
def process_message(json_message: dict) -> bool:
    import time
    import json
    import pymetbuild
    import datetime
    import os
    import json
    import sys
    import math
    from metbuild.input import Input
    from metbuild.database import Database
    from metbuild.s3file import S3file

    filelist_name = "filelist.json"

    logger = logging.getLogger(__name__)

    db = Database()

    logger.info("Processing message")
    logger.info(json.dumps(json_message["Body"]))
    inputData = Input(json_message["Body"])

    start_date = inputData.start_date()
    start_date_pmb = inputData.start_date_pmb()
    end_date = inputData.end_date()
    end_date_pmb = inputData.end_date_pmb()
    time_step = inputData.time_step()

    s3 = S3file(os.environ["METGET_S3_BUCKET_UPLOAD"])

    met_field = generate_met_field(
        inputData.format(),
        start_date_pmb,
        end_date_pmb,
        time_step,
        inputData.filename(),
        inputData.compression(),
    )

    nowcast = inputData.nowcast()
    multiple_forecasts = inputData.multiple_forecasts()

    data_type_key = generate_datatype_key(inputData.data_type())

    domain_data = []
    ongoing_restore = False
    nhc_data = {}
    db_files = []
    # ...Take a first pass on the data and check for restore status
    for i in range(inputData.num_domains()):
        if met_field:
            generate_met_domain(inputData, met_field, i)
        d = inputData.domain(i)
        ensemble_member = inputData.domain(i).ensemble_member()
        f = db.generate_file_list(
            d.service(),
            inputData.data_type(),
            start_date,
            end_date,
            d.storm(),
            d.basin(),
            d.advisory(),
            d.tau(),
            nowcast,
            multiple_forecasts,
            ensemble_member,
        )

        if d.service() == "nhc":
            nhc_data[i] = f
        else:
            db_files.append(f)
            if len(f) < 2:
                logger.error("No data found for domain " + str(i) + ". Giving up.")
                raise RuntimeError("No data found for domain")

            for item in f:
                if d.service() == "coamps-tc":
                    files = item[1].split(",")
                    for ff in files:
                        ongoing_restore_this = db.check_initiate_restore(
                            ff, d.service(), item[0]
                        )
                        if ongoing_restore_this:
                            ongoing_restore = True
                else:
                    ongoing_restore_this = db.check_initiate_restore(
                        item[1], d.service(), item[0]
                    )
                    if ongoing_restore_this:
                        ongoing_restore = True

    # ...If restore ongoing, this is where we stop
    if ongoing_restore:
        if not json_file:
            db.update_request_status(
                json_message["MessageId"],
                "restore",
                "Job is in archive restore status",
                json_message["Body"],
                False,
            )
        if met_field:
            ff = met_field.filenames()
            for f in ff:
                os.remove(f)
            cleanup_temp_files(domain_data)
        return False
    
    output_file_list = []
    files_used_list = {}

    # ...Begin downloading data from s3
    for i in range(inputData.num_domains()):
        d = inputData.domain(i)
        domain_data.append([])

        if d.service() == "nhc":

            if not nhc_data[i]["best_track"] and not nhc_data[i]["forecast_track"]:
                logger.error("No data found for domain {:d}. Giving up".format(i))
                raise RuntimeError("No data found for domain {:d}. Giving up".format(i))

            if nhc_data[i]["best_track"]:
                local_file_besttrack = db.get_file(nhc_data[i]["best_track"]["filepath"], "nhc")
                if not met_field:
                    new_file = os.path.basename(local_file_besttrack)
                    os.rename(local_file_besttrack, new_file)
                    local_file_besttrack = new_file
                domain_data[i].append({"time": nhc_data[i]["best_track"]["start"], "filepath": local_file_besttrack})

            if nhc_data[i]["forecast_track"]:
                local_file_forecast = db.get_file(nhc_data[i]["forecast_track"]["filepath"], "nhc")
                if not met_field:
                    new_file = os.path.basename(local_file_forecast)
                    os.rename(local_file_forecast, new_file)
                    local_file_forecast = new_file
                domain_data[i].append({"time": nhc_data[i]["forecast_track"]["start"], "filepath": local_file_forecast})

            if nhc_data[i]["best_track"] and nhc_data[i]["forecast_track"]:
                merge_file = "nhc_merge_{:04d}_{:s}_{:s}_{:s}.trk".format(nhc_data[i]["best_track"]["start"].year, d.basin(), d.storm(), d.advisory())
                local_file_merged = merge_nhc_tracks(local_file_besttrack, local_file_forecast, merge_file)
                domain_data[i].append({"time": nhc_data[i]["best_track"]["start"], "filepath": local_file_merged})

        else:
            f = db_files[i]
            if len(f) < 2:
                logger.error("No data found for domain {:d}. Giving up.".format(i))
                raise RuntimeError("No data found for domain {:d}. Giving up.".format(i))

            for item in f:
                if d.service() == "coamps-tc":
                    files = item[1].split(",")
                    local_file_list = []
                    for ff in files:
                        local_file = db.get_file(ff, d.service(), item[0])
                        if not met_field:
                            new_file = os.path.basename(local_file)
                            os.rename(local_file, new_file)
                            local_file = new_file
                        local_file_list.append(local_file)
                    domain_data[i].append({"time": item[0], "filepath": local_file_list})
                else:
                    local_file = db.get_file(item[1], d.service(), item[0])
                    if not met_field:
                        new_file = os.path.basename(local_file)
                        os.rename(local_file, new_file)
                        local_file = new_file
                    domain_data[i].append({"time": item[0], "filepath": local_file})

    def print_file_status(filepath: any, time: datetime) -> None:
        import os
        if type(filepath) == list:
            fnames = ""
            for fff in filepath:
                if fnames == "":
                    fnames += os.path.basename(fff)
                else:
                    fnames += ", "+os.path.basename(fff)
        else:
            fnames=filepath
        logger.info("Processing next file: {:s} ({:s})".format(fnames,time.strftime("%Y-%m-%d %H:%M")))

    def get_next_file_index(time, domain_data):
        for i in range(len(domain_data)):
            if time <= domain_data[i]["time"]:
                return i
        return len(domain_data) - 1

    if not met_field:
        for i in range(inputData.num_domains()):
            for pr in domain_data[i]:
                output_file_list.append(pr["filepath"])
        files_used_list[inputData.domain(i).name()] = output_file_list
    else:
        for i in range(inputData.num_domains()):
            d = inputData.domain(i)

            if d.service() == "nhc":
                logger.error("NHC to gridded data not implemented")
                raise RuntimeError("NHC to gridded data no implemented")

            source_key = generate_data_source_key(d.service())
            met = pymetbuild.Meteorology(
                d.grid().grid_object(),
                source_key,
                data_type_key,
                inputData.backfill(),
                inputData.epsg(),
            )
    
            t0 = domain_data[i][0]["time"]
    
            domain_files_used = []
            next_time = start_date + datetime.timedelta(seconds=time_step)
            index = get_next_file_index(next_time, domain_data[i])
    
            t1 = domain_data[i][index]["time"]
            t0_pmb = Input.date_to_pmb(t0)
            t1_pmb = Input.date_to_pmb(t1)
                    
            ff = domain_data[i][0]["filepath"]
            print_file_status(ff, t0)
            
            met.set_next_file(ff)
            if d.service() == "coamps-tc":
                for ff in domain_data[i][0]["filepath"]:
                    domain_files_used.append(os.path.basename(ff))
            else:
                domain_files_used.append(os.path.basename(domain_data[i][0]["filepath"]))
    
            met.set_next_file(domain_data[i][index]["filepath"])
            ff = domain_data[i][index]["filepath"]
            print_file_status(ff, t1)
            met.process_data()
            if d.service() == "coamps-tc":
                for ff in domain_data[i][index]["filepath"]:
                    domain_files_used.append(os.path.basename(ff))
            else:
                domain_files_used.append(
                    os.path.basename(domain_data[i][index]["filepath"])
                )
    
            for t in datespan(start_date, end_date, datetime.timedelta(seconds=time_step)):
                if t > t1:
                    index = get_next_file_index(t, domain_data[i])
                    t0 = t1
                    t1 = domain_data[i][index]["time"]
                    ff = domain_data[i][index]["filepath"]
                    print_file_status(ff, t1)
                    met.set_next_file(domain_data[i][index]["filepath"])
                    if t0 != t1:
                        if d.service() == "coamps-tc":
                            for ff in domain_data[i][index]["filepath"]:
                                domain_files_used.append(os.path.basename(ff))
                        else:
                            domain_files_used.append(
                                os.path.basename(domain_data[i][index]["filepath"])
                            )
                    met.process_data()

                if t < t0 or t > t1:
                    weight = -1.0
                elif t0 == t1:
                    weight = 0.0
                else:
                    weight = met.generate_time_weight(
                        Input.date_to_pmb(t0), Input.date_to_pmb(t1), Input.date_to_pmb(t)
                    )

                logger.info("Processing time {:s}, weight = {:f}".format(t.strftime("%Y-%m-%d %H:%M"),weight))
    
                if inputData.data_type() == "wind_pressure":
                    values = met.to_wind_grid(weight)
                else:
                    values = met.to_grid(weight)
                met_field.write(Input.date_to_pmb(t), i, values)
    
            files_used_list[inputData.domain(i).name()] = domain_files_used

        output_file_list = met_field.filenames()
        met_field = None  # ...Closes all open files

    output_file_dict = {
        "input": inputData.json(),
        "input_files": files_used_list,
        "output_files": output_file_list,
    }

    # ...Posts the data out to the correct S3 location
    messageId = inputData.uuid()
    for f in output_file_list:
        path = os.path.join(messageId,f)
        s3.upload_file(f, path)
        os.remove(f)

    with open(filelist_name, "w") as of:
        of.write(json.dumps(output_file_dict, indent=2))

    filelist_path = messageId + "/" + filelist_name
    s3.upload_file(filelist_name, filelist_path)
    logger.info("Finished processing message with id")
    os.remove(filelist_name)

    cleanup_temp_files(domain_data)

    return True


def cleanup_temp_files(data):
    import os
    from os.path import exists

    for domain in data:
        for f in domain:
            if type(f["filepath"]) == list:
                for ff in f["filepath"]:
                    if exists(ff):
                        os.remove(ff)
            else:
                if exists(f["filepath"]):
                    os.remove(f["filepath"])


def main():
    from metbuild.database import Database
    import sys
    import os
    import json

    log = logging.getLogger(__name__)
    log.debug("Beginning execution")

    message = os.environ["METGET_REQUEST_JSON"]
    log.info(message)

    json_data = json.loads(message)

    try:
        process_message(json_data)
    except RuntimeError as e:
        log.error("Encountered error during processing: "+str(e))
    except KeyError as e:
        log.error("Encountered malformed json input: "+str(e))

    log.debug("Exiting script with status 0")
    exit(0)


if __name__ == "__main__":
    main()
