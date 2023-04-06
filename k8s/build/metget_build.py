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
from datetime import datetime, timedelta
from metbuild.input import Input


def date_span(start_date: datetime, end_date: datetime, delta: timedelta):
    """
    Generator function that yields a series of dates between the start and end

    Args:
        start_date: The start date
        end_date: The end date
        delta: The time step in seconds

    Returns:
        A generator object that yields a series of dates between the start and end
    """
    currentDate = start_date
    while currentDate <= end_date:
        yield currentDate
        currentDate += delta


def generate_datatype_key(data_type: str) -> int:
    """
    Generate the key for the data type from the pymetbuild library

    Args:
        data_type: The data type to generate the key for

    Returns:
        The key for the data type
    """
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


def generate_data_source_key(data_source) -> int:
    """
    Generate the key for the data source from the pymetbuild library

    Args:
        data_source: The data source to generate the key for

    Returns:
        The key for the data source
    """
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


def generate_met_field(
    output_format: str,
    start: datetime,
    end: datetime,
    time_step: int,
    filename: str,
    compression: bool,
):
    """
    Generate the met field object from the pymetbuild library

    Args:
        output_format: The output format to generate the met field object for
        start: The start date
        end: The end date
        time_step: The time step in seconds
        filename: The filename to write to
        compression: Whether or not to compress the output
    """
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


def generate_met_domain(input_data: Input, met_object, index: int):
    """
    Generate the met domain object from the pymetbuild library

    Args:
        input_data: The input data object
        met_object: The met object
        index: The index of the domain to generate

    Returns:
        The met domain object
    """

    d = input_data.domain(index)
    output_format = input_data.format()
    if (
        output_format == "ascii"
        or output_format == "owi-ascii"
        or output_format == "adcirc-ascii"
    ):
        if input_data.data_type() == "wind_pressure":
            fn1 = input_data.filename() + "_" + "{:02d}".format(index) + ".pre"
            fn2 = input_data.filename() + "_" + "{:02d}".format(index) + ".wnd"
            fns = [fn1, fn2]
        elif input_data.data_type() == "rain":
            fns = [input_data.filename() + ".precip"]
        elif input_data.data_type() == "humidity":
            fns = [input_data.filename() + ".humid"]
        elif input_data.data_type() == "ice":
            fns = [input_data.filename() + ".ice"]
        else:
            raise RuntimeError("Invalid variable requested")
        if input_data.compression():
            for i, s in enumerate(fns):
                fns[i] = s + ".gz"

        met_object.addDomain(d.grid().grid_object(), fns)
    elif output_format == "owi-netcdf":
        group = d.name()
        met_object.addDomain(d.grid().grid_object(), [group])
    elif output_format == "hec-netcdf":
        if input_data.data_type() == "wind_pressure":
            variables = ["wind_u", "wind_v", "mslp"]
        elif input_data.data_type() == "wind":
            variables = ["wind_u", "wind_v"]
        elif input_data.data_type() == "rain":
            variables = ["rain"]
        elif input_data.data_type() == "humidity":
            variables = ["humidity"]
        elif input_data.data_type() == "ice":
            variables = ["ice"]
        else:
            raise RuntimeError("Invalid variable requested")
        met_object.addDomain(d.grid().grid_object(), variables)
    elif output_format == "delft3d":
        if input_data.data_type() == "wind_pressure":
            variables = ["wind_u", "wind_v", "mslp"]
        elif input_data.data_type() == "wind":
            variables = ["wind_u", "wind_v"]
        elif input_data.data_type() == "rain":
            variables = ["rain"]
        elif input_data.data_type() == "humidity":
            variables = ["humidity"]
        elif input_data.data_type() == "ice":
            variables = ["ice"]
        else:
            raise RuntimeError("Invalid variable requested")
        met_object.addDomain(d.grid().grid_object(), variables)
    else:
        raise RuntimeError("Invalid output format selected: " + output_format)


def merge_nhc_tracks(besttrack_file: str, forecast_file: str, output_file: str) -> str:
    """
    Merge the best track and forecast files into a single file

    Args:
        besttrack_file: The best track file
        forecast_file: The forecast file
        output_file: The output file

    Returns:
        The output file

    """

    from datetime import datetime, timedelta

    btk_lines = []
    fcst_lines = []

    with open(besttrack_file) as btk:
        for line in btk:
            btk_lines.append(
                {
                    "line": line.rstrip(),
                    "date": datetime.strptime(line.split(",")[2], " %Y%m%d%H"),
                }
            )

    with open(forecast_file) as fcst:
        for line in fcst:
            fcst_basetime = datetime.strptime(line.split(",")[2], " %Y%m%d%H")
            fcst_time = int(line.split(",")[5])
            fcst_lines.append(
                {
                    "line": line.rstrip(),
                    "date": fcst_basetime + timedelta(hours=fcst_time),
                }
            )

    start_date = btk_lines[0]["date"]
    start_date_str = datetime.strftime(start_date, "%Y%m%d%H")

    with open(output_file, "w") as merge:
        for line in btk_lines:
            if line["date"] < fcst_lines[0]["date"]:
                dt = int((line["date"] - start_date).total_seconds() / 3600.0)
                dt_str = "{:4d}".format(dt)
                sub1 = line["line"][:8]
                sub2 = line["line"][18:29]
                sub3 = line["line"][33:]
                line_new = sub1 + start_date_str + sub2 + dt_str + sub3
                merge.write(line_new + "\n")

        for line in fcst_lines:
            dt = int((line["date"] - start_date).total_seconds() / 3600.0)
            dt_str = "{:4d}".format(dt)
            sub1 = line["line"][:8]
            sub2 = line["line"][18:29]
            sub3 = line["line"][33:]
            line_new = sub1 + start_date_str + sub2 + dt_str + sub3
            merge.write(line_new + "\n")

    return output_file


def process_message(json_message: dict) -> bool:
    """
    Process a message from the queue of available messages

    Args:
        json_message: The message from the queue

    Returns:
        True if the message was processed successfully, False otherwise
    """
    import pymetbuild
    import datetime
    import os
    import json
    from metbuild.input import Input
    from metbuild.database import Database
    from metbuild.s3file import S3file

    filelist_name = "filelist.json"

    logger = logging.getLogger(__name__)

    db = Database()

    logger.info("Processing message")
    logger.info(json.dumps(json_message["Body"]))
    input_data = Input(json_message["Body"])

    start_date = input_data.start_date()
    start_date_pmb = input_data.start_date_pmb()
    end_date = input_data.end_date()
    end_date_pmb = input_data.end_date_pmb()
    time_step = input_data.time_step()

    s3 = S3file(os.environ["METGET_S3_BUCKET_UPLOAD"])

    met_field = generate_met_field(
        input_data.format(),
        start_date_pmb,
        end_date_pmb,
        time_step,
        input_data.filename(),
        input_data.compression(),
    )

    nowcast = input_data.nowcast()
    multiple_forecasts = input_data.multiple_forecasts()

    data_type_key = generate_datatype_key(input_data.data_type())

    domain_data = []
    ongoing_restore = False
    nhc_data = {}
    db_files = []
    # ...Take a first pass on the data and check for restore status
    for i in range(input_data.num_domains()):
        if met_field:
            generate_met_domain(input_data, met_field, i)
        d = input_data.domain(i)
        ensemble_member = input_data.domain(i).ensemble_member()
        f = db.generate_file_list(
            d.service(),
            input_data.data_type(),
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
    for i in range(input_data.num_domains()):
        d = input_data.domain(i)
        domain_data.append([])

        if d.service() == "nhc":

            if not nhc_data[i]["best_track"] and not nhc_data[i]["forecast_track"]:
                logger.error("No data found for domain {:d}. Giving up".format(i))
                raise RuntimeError("No data found for domain {:d}. Giving up".format(i))

            local_file_besttrack = None
            local_file_forecast = None

            if nhc_data[i]["best_track"]:
                local_file_besttrack = db.get_file(
                    nhc_data[i]["best_track"]["filepath"], "nhc"
                )
                if not met_field:
                    new_file = os.path.basename(local_file_besttrack)
                    os.rename(local_file_besttrack, new_file)
                    local_file_besttrack = new_file
                domain_data[i].append(
                    {
                        "time": nhc_data[i]["best_track"]["start"],
                        "filepath": local_file_besttrack,
                    }
                )

            if nhc_data[i]["forecast_track"]:
                local_file_forecast = db.get_file(
                    nhc_data[i]["forecast_track"]["filepath"], "nhc"
                )
                if not met_field:
                    new_file = os.path.basename(local_file_forecast)
                    os.rename(local_file_forecast, new_file)
                    local_file_forecast = new_file
                domain_data[i].append(
                    {
                        "time": nhc_data[i]["forecast_track"]["start"],
                        "filepath": local_file_forecast,
                    }
                )

            if nhc_data[i]["best_track"] and nhc_data[i]["forecast_track"]:
                merge_file = "nhc_merge_{:04d}_{:s}_{:s}_{:s}.trk".format(
                    nhc_data[i]["best_track"]["start"].year,
                    d.basin(),
                    d.storm(),
                    d.advisory(),
                )
                local_file_merged = merge_nhc_tracks(
                    local_file_besttrack, local_file_forecast, merge_file
                )
                domain_data[i].append(
                    {
                        "time": nhc_data[i]["best_track"]["start"],
                        "filepath": local_file_merged,
                    }
                )

        else:
            f = db_files[i]
            if len(f) < 2:
                logger.error("No data found for domain {:d}. Giving up.".format(i))
                raise RuntimeError(
                    "No data found for domain {:d}. Giving up.".format(i)
                )

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
                    domain_data[i].append(
                        {"time": item[0], "filepath": local_file_list}
                    )
                else:
                    local_file = db.get_file(item[1], d.service(), item[0])
                    if not met_field:
                        new_file = os.path.basename(local_file)
                        os.rename(local_file, new_file)
                        local_file = new_file
                    domain_data[i].append({"time": item[0], "filepath": local_file})

    def print_file_status(filepath: any, time: datetime) -> None:
        """
        Print the status of the file being processed to the screen

        Args:
            filepath: The file being processed
            time: The time of the file being processed
        """
        import os

        if type(filepath) == list:
            fnames = ""
            for fff in filepath:
                if fnames == "":
                    fnames += os.path.basename(fff)
                else:
                    fnames += ", " + os.path.basename(fff)
        else:
            fnames = filepath
        logger.info(
            "Processing next file: {:s} ({:s})".format(
                fnames, time.strftime("%Y-%m-%d %H:%M")
            )
        )

    def get_next_file_index(time: datetime, domain_data):
        """
        Get the index of the next file to process in the domain data list

        Args:
            time: The time of the file being processed
            domain_data: The list of files to process
        """
        for ii in range(len(domain_data)):
            if time <= domain_data[ii]["time"]:
                return ii
        return len(domain_data) - 1

    if not met_field:
        for i in range(input_data.num_domains()):
            for pr in domain_data[i]:
                output_file_list.append(pr["filepath"])
        files_used_list[input_data.domain(i).name()] = output_file_list
    else:
        for i in range(input_data.num_domains()):
            d = input_data.domain(i)

            if d.service() == "nhc":
                logger.error("NHC to gridded data not implemented")
                raise RuntimeError("NHC to gridded data no implemented")

            source_key = generate_data_source_key(d.service())
            met = pymetbuild.Meteorology(
                d.grid().grid_object(),
                source_key,
                data_type_key,
                input_data.backfill(),
                input_data.epsg(),
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
                domain_files_used.append(
                    os.path.basename(domain_data[i][0]["filepath"])
                )

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

            for t in date_span(
                start_date, end_date, datetime.timedelta(seconds=time_step)
            ):
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
                        Input.date_to_pmb(t0),
                        Input.date_to_pmb(t1),
                        Input.date_to_pmb(t),
                    )

                logger.info(
                    "Processing time {:s}, weight = {:f}".format(
                        t.strftime("%Y-%m-%d %H:%M"), weight
                    )
                )

                if input_data.data_type() == "wind_pressure":
                    values = met.to_wind_grid(weight)
                else:
                    values = met.to_grid(weight)
                met_field.write(Input.date_to_pmb(t), i, values)

            files_used_list[input_data.domain(i).name()] = domain_files_used

        output_file_list = met_field.filenames()
        met_field = None  # ...Closes all open files

    output_file_dict = {
        "input": input_data.json(),
        "input_files": files_used_list,
        "output_files": output_file_list,
    }

    # ...TODO: This should come from the apigateway
    message_id = input_data.uuid()

    # ...Posts the data out to the correct S3 location
    for f in output_file_list:
        path = os.path.join(message_id, f)
        s3.upload_file(f, path)
        os.remove(f)

    with open(filelist_name, "w") as of:
        of.write(json.dumps(output_file_dict, indent=2))

    filelist_path = message_id + "/" + filelist_name
    s3.upload_file(filelist_name, filelist_path)
    logger.info("Finished processing message with id")
    os.remove(filelist_name)

    cleanup_temp_files(domain_data)

    return True


def cleanup_temp_files(data: list):
    """
    Removes all temporary files created during processing

    Args:
        data (list): List of dictionaries containing the filepaths of the
    """
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
    """
    Main entry point for the script
    """
    from metbuild.database import Database
    import sys
    import os
    import json

    log = logging.getLogger(__name__)
    log.debug("Beginning execution")

    # ...Get the input data from the environment.
    # This variable is set by the argo template
    # and comes from rabbitmq
    message = os.environ["METGET_REQUEST_JSON"]
    log.info(message)

    json_data = json.loads(message)

    try:
        process_message(json_data)
    except RuntimeError as e:
        log.error("Encountered error during processing: " + str(e))
    except KeyError as e:
        log.error("Encountered malformed json input: " + str(e))

    log.debug("Exiting script with status 0")
    exit(0)


if __name__ == "__main__":
    main()
