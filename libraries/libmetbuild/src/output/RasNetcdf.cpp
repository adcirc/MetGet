// MIT License
//
// Copyright (c) 2020 ADCIRC Development Group
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
//
// Author: Zach Cobell
// Contact: zcobell@thewaterinstitute.org
//
#include "RasNetcdf.h"

#include <string_view>
#include <utility>

#include "RasNetcdfDomain.h"
#include "Utilities.h"
#include "netcdf.h"

using namespace MetBuild;
using namespace Utilities;

RasNetcdf::RasNetcdf(const MetBuild::Date& date_start,
                     const MetBuild::Date& date_end, unsigned int time_step,
                     std::string filename)
    : OutputFile(date_start, date_end, time_step),
      m_filename(std::move(filename)),
      m_ncid(0) {
  this->initialize();
}

RasNetcdf::~RasNetcdf() { ncCheck(nc_close(this->m_ncid)); }

void RasNetcdf::addDomain(const Grid& w,
                          const std::vector<std::string>& variables) {
  if (!m_domains.empty()) {
    metbuild_throw_exception(
        "Only one domain may be used for RAS format files");
  }

  this->m_domains.push_back(std::make_unique<RasNetcdfDomain>(
      &w, this->startDate(), this->endDate(), this->timeStep(), this->m_ncid,
      variables));
}

int RasNetcdf::write(
    const Date& date, size_t domain_index,
    const MeteorologicalData<1, MetBuild::MeteorologicalDataType>& data) {
  return this->m_domains[0]->write(
      date, data);  // Always 0, only 1 domain allowed for RAS
}

int RasNetcdf::write(
    const Date& date, size_t domain_index,
    const MeteorologicalData<3, MetBuild::MeteorologicalDataType>& data) {
  return this->m_domains[0]->write(
      date, data);  // Always 0, only 1 domain allowed for RAS
}

void RasNetcdf::initialize() {
  constexpr std::string_view conventions = "CF-1.6,UGRID-0.9";
  constexpr std::string_view title = "MetGet Forcing, HEC-RAS Format";
  constexpr std::string_view institution = "MetGet";
  constexpr std::string_view source = "MetGet";

  auto now = Date::now();
  const std::string history = "Created " + now.toString();

  constexpr std::string_view references = "https://github.com/adcirc/MetGet";
  constexpr std::string_view metadata_conventions =
      "Unidata Dataset Discovery v1.0";
  constexpr std::string_view summary = "Data generated by MetGet for HEC-RAS";
  const std::string date_created = now.toString();

  ncCheck(nc_create(m_filename.c_str(), NC_NETCDF4, &m_ncid));
  ncCheck(nc_put_att_text(m_ncid, NC_GLOBAL, "Conventions", conventions.size(),
                          &conventions[0]));
  ncCheck(nc_put_att_text(m_ncid, NC_GLOBAL, "title", title.size(), &title[0]));
  ncCheck(nc_put_att_text(m_ncid, NC_GLOBAL, "institution", institution.size(),
                          &institution[0]));
  ncCheck(
      nc_put_att_text(m_ncid, NC_GLOBAL, "source", source.size(), &source[0]));
  ncCheck(nc_put_att_text(m_ncid, NC_GLOBAL, "history", history.size(),
                          &history[0]));
  ncCheck(nc_put_att_text(m_ncid, NC_GLOBAL, "references", references.size(),
                          &references[0]));
  ncCheck(nc_put_att_text(m_ncid, NC_GLOBAL, "metadata_conventions",
                          metadata_conventions.size(),
                          &metadata_conventions[0]));
  ncCheck(nc_put_att_text(m_ncid, NC_GLOBAL, "summary", summary.size(),
                          &summary[0]));
  ncCheck(nc_put_att_text(m_ncid, NC_GLOBAL, "date_created",
                          date_created.size(), &date_created[0]));
}
