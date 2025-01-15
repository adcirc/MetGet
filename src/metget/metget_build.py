###################################################################################################
# MIT License
#
# Copyright (c) 2023 The Water Institute
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
#
# Author: Zach Cobell
# Contact: zcobell@thewaterinstitute.org
# Organization: The Water Institute
#
###################################################################################################

import argparse
import contextlib
import json
import time
from datetime import datetime, timezone
from typing import Tuple, Union

from .metget_data import AVAILABLE_MODELS


class MetGetBuildRest:
    def __init__(
        self, metget_api_server: str, metget_api_key: str, metget_api_version: int
    ):
        """
        Constructor

        Args:
            metget_api_server (str): MetGet API server
            metget_api_key (str): MetGet API key
            metget_api_version (int): MetGet API version
        """
        self.__metget_api_server = metget_api_server
        self.__metget_api_key = metget_api_key
        self.__metget_api_version = metget_api_version

    @staticmethod
    def parse_domain_data(domain_list: list, level: int, tau: int) -> dict:
        """
        Parses the domain data from the given list and returns a dictionary

        Args:
            domain_list (list): List of domain data
            level (int): Level of the domain
            tau (int): Forecast skipping time

        Returns:
            dict: Dictionary containing the domain data
        """

        storm = None
        ensemble_member = None
        basin = None
        advisory = None
        year = None

        model = domain_list[0]
        if "hwrf" in model or "coamps" in model or "hafs" in model:
            if len(model.split("-")) < 2:
                msg = "Must include storm name with HWRF/COAMPS/HAFS request as 'hwrf-storm' or 'coamps-storm'"
                raise RuntimeError(msg)
            storm = model.split("-")[1]
            model = model.split("-")[0]
        elif "gefs" in model:
            if len(model.split("-")) < 2:
                msg = "Must include ensemble member with GEFS request as 'gefs-ensemble_member'"
                raise RuntimeError(msg)
            ensemble_member = model.split("-")[1]
            model = "gefs"
        elif "ctcx" in model:
            if len(model.split("-")) < 3:
                msg = "Must include storm name and ensemble member with CTCX request as 'ctcx-storm-ensemble_member'"
                raise RuntimeError(msg)
            ensemble_member = model.split("-")[2]
            storm = model.split("-")[1]
            model = "ctcx"
        elif "nhc" in model:
            if len(model.split("-")) < 4:
                msg = (
                    "Must include basin, storm name, and advisory with NHC request as "
                    "'nhc-basin-storm-advisory' or 'nhc-basin-storm-year-advisory'"
                )
                raise RuntimeError(msg)
            keys = model.split("-")
            if len(keys) == 5:
                year = int(keys[1])
                basin = keys[2]
                storm = keys[3]
                advisory = keys[4]
                with contextlib.suppress(ValueError):
                    advisory = f"{int(advisory):03d}"
            else:
                year = datetime.now(timezone.utc).year
                basin = keys[1]
                storm = keys[2]
                advisory = keys[3]
                with contextlib.suppress(ValueError):
                    advisory = f"{int(advisory):03d}"
            model = "nhc"
        else:
            if len(model.split("-")) > 1:
                raise RuntimeError(
                    "Model '"
                    + model
                    + "' does not support additional '-' separated arguments"
                )

        res = float(domain_list[1])
        x0 = float(domain_list[2])
        y0 = float(domain_list[3])
        x1 = float(domain_list[4])
        y1 = float(domain_list[5])

        if model not in AVAILABLE_MODELS:
            raise RuntimeError("Specified model '" + model + "' is not available")

        xmax = max(x0, x1)
        xmin = min(x0, x1)
        ymax = max(y0, y1)
        ymin = min(y0, y1)
        res = abs(res)
        if res <= 0:
            msg = "Specified model resolution is invalid"
            raise RuntimeError(msg)

        if model == "hwrf" or model == "hafsa" or model == "hafsb" or model == "coamps":
            return {
                "name": AVAILABLE_MODELS[model] + "-" + storm,
                "service": AVAILABLE_MODELS[model],
                "storm": storm,
                "x_init": xmin,
                "y_init": ymin,
                "x_end": xmax,
                "y_end": ymax,
                "di": res,
                "dj": res,
                "tau": tau,
                "level": level,
            }
        elif model == "ctcx":
            return {
                "name": AVAILABLE_MODELS[model] + "-" + storm + "-" + ensemble_member,
                "service": AVAILABLE_MODELS[model],
                "storm": storm,
                "tau": tau,
                "ensemble_member": ensemble_member,
                "x_init": xmin,
                "y_init": ymin,
                "x_end": xmax,
                "y_end": ymax,
                "di": res,
                "dj": res,
                "level": level,
            }
        elif model == "gefs":
            return {
                "name": model,
                "service": AVAILABLE_MODELS[model],
                "ensemble_member": ensemble_member,
                "x_init": xmin,
                "y_init": ymin,
                "x_end": xmax,
                "y_end": ymax,
                "di": res,
                "dj": res,
                "level": level,
            }
        elif model == "nhc":
            return {
                "name": model,
                "service": AVAILABLE_MODELS[model],
                "basin": basin,
                "storm": storm,
                "storm_year": year,
                "advisory": advisory,
                "x_init": xmin,
                "y_init": ymin,
                "x_end": xmax,
                "y_end": ymax,
                "di": res,
                "dj": res,
                "level": level,
            }
        else:
            return {
                "name": model,
                "service": AVAILABLE_MODELS[model],
                "x_init": xmin,
                "y_init": ymin,
                "x_end": xmax,
                "y_end": ymax,
                "di": res,
                "dj": res,
                "level": level,
            }

    @staticmethod
    def parse_command_line_domains(domain_list: list, initialization_skip: int):
        """
        Generates the domains from the given list of domains

        Args:
            domain_list (list): List of domains
            initialization_skip (int): Initialization skip time

        Returns:
            list: List of domains as dictionaries
        """
        domains = []
        for idx, d in enumerate(domain_list):
            j = MetGetBuildRest.parse_domain_data(d, idx, initialization_skip)
            domains.append(j)
        return domains

    @staticmethod
    def generate_request_json(**kwargs) -> dict:
        """
        Generates the request JSON for the given arguments

        Returns:
            dict: Request JSON
        """
        import getpass
        import socket

        request_data = {
            "version": "0.0.1",
            "creator": kwargs.get(
                "username", getpass.getuser() + "." + socket.gethostname()
            ),
            "background_pressure": kwargs.get("background_pressure", 1013.0),
            "backfill": kwargs.get("backfill", False),
            "nowcast": kwargs.get("nowcast", False),
            "multiple_forecasts": kwargs.get("multiple_forecasts", False),
            "start_date": str(kwargs.get("start_date")),
            "end_date": str(kwargs.get("end_date")),
            "format": kwargs.get("format", "owi-ascii"),
            "data_type": kwargs.get("data_type", "wind_pressure"),
            "time_step": kwargs.get("time_step", 3600),
            "domains": kwargs.get("domains"),
            "compression": kwargs.get("compression", False),
            "epsg": kwargs.get("epsg", 4326),
            "filename": kwargs.get("filename", "metget_data"),
        }

        # Check if the data_type is 'all_variables' and if so, check that only
        # the coamps model is requested
        if request_data["data_type"] == "all_variables":
            for domain in request_data["domains"]:
                if "coamps-tc" not in domain["service"]:
                    msg = "The 'all_variables' data_type is only available for the coamps model"
                    raise RuntimeError(msg)

        if kwargs.get("strict", False):
            request_data["strict"] = True
        else:
            request_data["strict"] = False

        if kwargs.get("dry_run", False):
            request_data["dry_run"] = True
        else:
            request_data["dry_run"] = False

        if kwargs.get("save_json_request", False):
            with open("request.json", "w") as f:
                f.write(json.dumps(request_data, indent=2))

        return request_data

    def make_metget_request(self, request_json: dict) -> Tuple[str, int]:
        """
        Makes a request to the MetGet API and returns the data id and status code

        Args:
            request_json (dict): Request JSON

        Returns:
            Tuple[str, int]: Data id and status code
        """
        import requests

        headers = {"x-api-key": self.__metget_api_key}
        r = requests.post(
            self.__metget_api_server + "/build", headers=headers, json=request_json
        )
        if r.status_code != 200:
            if r.text:
                with open("metget.debug", "a") as f:
                    f.write(r.text)
            raise RuntimeError(
                "Request to MetGet was returned status code = " + str(r.status_code)
            )
        return_data = json.loads(r.text)
        data_id = return_data["body"]["request_id"]
        status_code = return_data["statusCode"]
        if status_code != 200:
            with open("metget.debug", "a") as f:
                f.write(
                    "[WARNING]: MetGet returned status code " + str(status_code) + "\n"
                )
                f.write(str(return_data["body"]["error_text"]))
        return data_id, status_code

    def download_metget_data(
        self,
        data_id: str,
        sleep_time: int,
        max_wait: int,
        output_directory: Union[str, None],
        return_only_url: bool=False
    ) -> None:
        """
        Downloads the data from the MetGet API

        Args:
            data_id (str): Data id
            sleep_time (int): Time to sleep between status checks
            max_wait (int): Maximum time to wait for data to appear
            output_directory (Union[str, None]): Output directory
            return_only_url (bool): If true the url of the files and the filelist will be returned instead of them being saved (Default=False)

        Returns:
            None
        """
        import os
        from datetime import datetime, timedelta, timezone

        import requests

        from .spinnerlogger import SpinnerLogger

        # ...Wait time
        end_time = datetime.now(timezone.utc) + timedelta(hours=max_wait)

        # ...Timing information
        request_start_time = datetime.now(timezone.utc)

        # ...Wait for request data to appear
        tries = 0
        data_ready = False
        status = None

        spinner = SpinnerLogger()
        print(f"Waiting for request id {data_id:s}", flush=True)
        spinner.start()

        return_data = None
        data_url = None

        # ...If an output_directory is given, check if it exists
        if output_directory is not None and not os.path.exists(output_directory):
            msg = f"Output directory does not exist: {output_directory:s}"
            raise RuntimeError(msg)

        while datetime.now(timezone.utc) <= end_time:
            tries += 1
            try:
                data_url, status = self.check_metget_status(data_id)
                spinner.set_text(SpinnerLogger.standard_log(tries, status))
                if status == "completed":
                    spinner.succeed()
                    # ...Parse the return to get data
                    data_ready = True
                    flist_url = data_url + "/filelist.json"
                    u = requests.get(flist_url)
                    if u.status_code == 200:
                        js = "filelist.json"
                        if output_directory is not None:
                            js = os.path.join(output_directory, js)
                        return_data = json.loads(u.text)
                        # Only save filelist file when data are saved
                        if not return_only_url:
                            with open(js, "w") as jsonfile:
                                jsonfile.write(
                                    json.dumps(return_data, indent=2, sort_keys=True)
                                )
                        break
                elif status == "error":
                    spinner.fail("Request could not be completed")
                    return
                else:
                    time.sleep(sleep_time)
                    continue
            except KeyboardInterrupt:
                spinner.fail("Process was ended by the user")
                raise

        # ...Download files
        if data_ready:
            file_list = return_data["output_files"]
            url_list = []
            for f in file_list:
                if output_directory is not None:
                    ff = os.path.join(output_directory, f)
                else:
                    ff = f

                time_stamp = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S UTC"
                )
                spinner.start(f"[{time_stamp:s}]: Getting file: {f:s}")
                url = data_url + "/" + f
                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    if return_only_url:
                        url_list.append(url)
                    else:
                        with open(ff, "wb") as wind_file:
                            for chunk in r.iter_content(chunk_size=8192):
                                wind_file.write(chunk)
                spinner.succeed()

            request_end_time = datetime.now(timezone.utc)
            request_duration = request_end_time - request_start_time
            hours, remainder = divmod(request_duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)

            time_stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            spinner.succeed(
                f"[{time_stamp:s}]: Elapsed time: {int(hours):d}h{int(minutes):02d}m{int(seconds):02d}s"
            )
            
            if return_only_url:
                return url_list, return_data
            
        else:
            if status == "restore":
                print(
                    "[WARNING]: Data for request "
                    + data_id
                    + " did not become ready before the max-wait time expired. "
                    "You can rerun and ask for this request by id"
                )
            elif status == "running":
                print(
                    "[WARNING]: Data for request "
                    + data_id
                    + " is still being constructed when the max-wait time expired. Please check on it later"
                )
            elif status == "queued":
                print(
                    "[WARNING]: Data for request "
                    + data_id
                    + " is still queued. If this does not change soon, please contact an administrator"
                )
            else:
                print("[ERROR]: Data has not become available due to an unknown error")
            return

    def check_metget_status(
        self,
        data_id: str,
    ) -> Tuple[str, str]:
        """
        Checks the status of a MetGet request

        Args:
            data_id (str): Data id

        Returns:
            Tuple[str, str]: Data url and status
        """
        if self.__metget_api_version == 2:
            response = self.__check_metget_status_v2(data_id)
        else:
            msg = f"Invalid MetGet API version. Must be 2. Got {self.__metget_api_version:d}"
            raise RuntimeError(msg)

        json_response = json.loads(response)
        status = json_response["body"]["status"]
        data_url = json_response["body"]["destination"]
        return data_url, status

    def __check_metget_status_v2(self, data_id: str) -> str:
        """
        Checks the status of a MetGet request using the v2 API

        Args:
            data_id (str): Data id

        Returns:
            str: response text
        """
        import requests

        headers = {"x-api-key": self.__metget_api_key}
        request_params = {"request-id": data_id}
        response = requests.get(
            self.__metget_api_server + "/check", headers=headers, params=request_params
        )
        return response.text


def metget_build(args: argparse.Namespace) -> None:
    """
    This method is used to build a MetGet request

    Args:
        args: The arguments passed to the command line

    Returns:
        None
    """
    from .metget_data import AVAILABLE_FORMATS, AVAILABLE_VARIABLES
    from .metget_environment import get_metget_environment_variables

    # ...Get the environment variables
    environment = get_metget_environment_variables(args)

    # ...Initialize the metget client
    client = MetGetBuildRest(
        environment["endpoint"], environment["apikey"], environment["api_version"]
    )

    # ...Check for required arguments
    if not args.request:
        if not args.start:
            print("[ERROR]: Must provide '--start'")
            exit(1)
        if not args.end:
            print("[ERROR]: Must provide '--end'")
            exit(1)
        if not args.timestep:
            print("[ERROR]: Must provice '--timestep'")
            exit(1)
        if not args.output:
            print("[ERROR]: Must provide '--output'")
            exit(1)

        output_format = AVAILABLE_FORMATS[args.format]
        if (output_format == "delft3d" or output_format == "hec-netcdf") and len(
            args.domain
        ) > 1:
            print("[ERROR]: " + args.format + " does not support more than one domain.")
            exit(1)

        if args.variable not in AVAILABLE_VARIABLES:
            print(f"ERROR: Invalid variable '{args.variable:s}' selected")
            exit(1)

        if args.format not in AVAILABLE_FORMATS:
            print(f"ERROR: Invalid output format '{args.format:s}' selected")
            exit(1)

        # ...Building the request
        request_data = MetGetBuildRest.generate_request_json(
            analysis=args.analysis,
            multiple_forecasts=args.multiple_forecasts,
            start_date=args.start,
            end_date=args.end,
            format=output_format,
            data_type=args.variable,
            backfill=args.backfill,
            time_step=args.timestep,
            domains=MetGetBuildRest.parse_command_line_domains(
                args.domain, args.initialization_skip
            ),
            compression=args.compression,
            epsg=args.epsg,
            filename=args.output,
            strict=args.strict,
            dry_run=args.dryrun,
            save_json_request=args.save_json_request,
        )

        data_id, status_code = client.make_metget_request(request_data)
        if not args.dryrun and status_code == 200:
            client.download_metget_data(
                data_id,
                args.check_interval,
                args.max_wait,
                args.output_directory,
            )
        else:
            print(status_code)

    else:
        client.download_metget_data(
            args.request,
            args.check_interval,
            args.max_wait,
            args.output_directory,
        )
