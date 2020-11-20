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

from metget.noaadownloader import NoaaDownloader


class NcepNamdownloader(NoaaDownloader):
    def __init__(self, dblocation, begin, end):
        address = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/nam/prod/"
        NoaaDownloader.__init__(self, "nam_ncep", "NAM-NCEP", address,
                                dblocation, begin, end)
        self.__downloadlocation = dblocation + "/" + self.mettype()
        self.__lastdate = self.begindate()

    def download(self):
        from metget.spyder import Spyder
        from datetime import datetime
        from metget.metdb import Metdb
        num_download = 0
        s = Spyder(self.address())
        db = Metdb(self.dblocation())

        links = []
        day_links = s.filelist()
        nerror = 0
        lastdate = self.begindate()
        for l in day_links:
            if "nam." in l:
                dstr = l[0:-1].rsplit('/', 1)[-1].rsplit('.', 1)[-1]
                yr = int(dstr[0:4])
                mo = int(dstr[4:6])
                dy = int(dstr[6:8])
                t = datetime(yr, mo, dy, 0, 0, 0)
                lastdate = t
                if self.enddate() >= t >= self.begindate():
                    s2 = Spyder(l)
                    hr_links = s2.filelist()
                    for ll in hr_links:
                        if "awphys" in ll:
                            if "idx" not in ll:
                                links.append(ll)

        pairs = self.generateGrbInvPairs(links)
        for p in pairs:
            fpath, n, err = self.getgrib(self.__downloadlocation, p, p["cycledate"])
            nerror += err
            if fpath:
                db.add(p, self.mettype(), fpath)
                num_download += n

        if nerror == 0:
            self.__lastdate = lastdate

        return num_download

    @staticmethod
    def generateGrbInvPairs(glist):
        from datetime import datetime, timedelta
        pairs = []
        for i in range(0, len(glist)):
            lst = glist[i].rsplit("/")
            v1 = lst[-1].rsplit(".")[-3]
            v2 = lst[-1].rsplit(".")[-4]
            v3 = lst[-2].rsplit(".", 1)[-1]

            yr = int(v3[0:4])
            mo = int(v3[4:6])
            dy = int(v3[6:8])
            cycle = int(v2[1:3])
            fcst = int(v1[-2:])

            cdate = datetime(yr, mo, dy, cycle, 0, 0)
            fdate = cdate + timedelta(hours=fcst)

            pairs.append({
                "grb": glist[i],
                "inv": glist[i] + ".idx",
                "cycledate": cdate,
                "forecastdate": fdate
            })
        return pairs
