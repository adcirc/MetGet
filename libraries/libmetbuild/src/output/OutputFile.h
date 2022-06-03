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
#ifndef METGET_SRC_OUTPUTFILE_H_
#define METGET_SRC_OUTPUTFILE_H_

#include <memory>
#include <vector>

#include "Date.h"
#include "Logging.h"
#include "MeteorologicalData.h"
#include "OutputDomain.h"

namespace MetBuild {

class OutputFile {
 public:
  OutputFile(const MetBuild::Date &date_start, const MetBuild::Date &date_end,
             unsigned time_step)
      : m_time_step(time_step),
        m_start_date(date_start),
        m_end_date(date_end) {}

  virtual ~OutputFile() = default;

  virtual int write(
      const MetBuild::Date &date, size_t domain_index,
      const MetBuild::MeteorologicalData<1, MetBuild::MeteorologicalDataType>
          &data) {
    metbuild_throw_exception("Function not implemented.");
    return 1;
  };

  virtual int write(
      const MetBuild::Date &date, size_t domain_index,
      const MetBuild::MeteorologicalData<3, MetBuild::MeteorologicalDataType>
          &data) {
    metbuild_throw_exception("Function not implemented");
    return 1;
  }

  virtual void addDomain(const MetBuild::Grid &w,
                         const std::vector<std::string> &filenames) = 0;

  unsigned timeStep() const { return m_time_step; }

  MetBuild::Date startDate() const { return m_start_date; }

  MetBuild::Date endDate() const { return m_end_date; }

  virtual std::vector<std::string> filenames() const {
    std::vector<std::string> files;
    for(const auto &d : m_domains) {
      auto f = d->filenames();
      for(const auto &ff : f) {
        files.push_back(ff);
      }
    }
    return files;
  }
      

 protected:
  std::vector<std::unique_ptr<MetBuild::OutputDomain>> m_domains;

 private:
  unsigned m_time_step;
  MetBuild::Date m_start_date;
  MetBuild::Date m_end_date;
};
}  // namespace MetBuild

#endif  // METGET_SRC_OUTPUTFILE_H_
