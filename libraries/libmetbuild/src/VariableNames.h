////////////////////////////////////////////////////////////////////////////////////
// MIT License
//
// Copyright (c) 2023 The Water Institute
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
//
// Author: Zachary Cobell
// Contact: zcobell@thewaterinstitute.org
// Organization: The Water Institute
//
////////////////////////////////////////////////////////////////////////////////////
#ifndef METGET_SRC_VARIABLENAMES_H_
#define METGET_SRC_VARIABLENAMES_H_

#include <string>
#include <utility>

#include "Logging.h"
#include "data_sources/GriddedDataTypes.h"

namespace MetBuild {

class VariableNames {
 public:
  VariableNames() = default;

  VariableNames(std::string longitude, std::string latitude,
                std::string pressure, std::string u10, std::string v10,
                std::string precipitation, std::string humidity,
                std::string temperature, std::string ice)
      : m_longitude(std::move(longitude)),
        m_latitude(std::move(latitude)),
        m_pressure(std::move(pressure)),
        m_u10(std::move(u10)),
        m_v10(std::move(v10)),
        m_precipitation(std::move(precipitation)),
        m_humidity(std::move(humidity)),
        m_temperature(std::move(temperature)),
        m_ice(std::move(ice)){};

  std::string longitude() const { return m_longitude; }
  std::string latitude() const { return m_latitude; }
  std::string pressure() const { return m_pressure; }
  std::string u10() const { return m_u10; }
  std::string v10() const { return m_v10; }
  std::string temperature() const { return m_temperature; }
  std::string humidity() const { return m_humidity; }
  std::string ice() const { return m_ice; }
  std::string precipitation() const { return m_precipitation; }

  std::string find_variable(
      const MetBuild::GriddedDataTypes::VARIABLES &variable) const {
    switch (variable) {
      case GriddedDataTypes::VARIABLES::VAR_U10:
        return u10();
      case GriddedDataTypes::VARIABLES::VAR_V10:
        return v10();
      case GriddedDataTypes::VARIABLES::VAR_PRESSURE:
        return pressure();
      case GriddedDataTypes::VARIABLES::VAR_TEMPERATURE:
        return temperature();
      case GriddedDataTypes::VARIABLES::VAR_HUMIDITY:
        return humidity();
      case GriddedDataTypes::VARIABLES::VAR_ICE:
        return ice();
      case GriddedDataTypes::VARIABLES::VAR_RAINFALL:
        return precipitation();
      default:
        Logging::throwError("Invalid variable type specified");
        return "none";
    }
  }

  void write() const {
    std::cout << "   Longitude: " << m_longitude << std::endl;	
    std::cout << "    Latitude: " << m_latitude << std::endl;
    std::cout << "         u10: " << m_u10 << std::endl;
    std::cout << "         v10: " << m_v10 << std::endl;
    std::cout << "      precip: " << m_precipitation << std::endl;
    std::cout << "    humidity: " << m_humidity << std::endl;
    std::cout << " temperature: " << m_temperature << std::endl;
    std::cout << "         ice: " << m_ice << std::endl;
  }

 private:
  std::string m_longitude;
  std::string m_latitude;
  std::string m_pressure;
  std::string m_u10;
  std::string m_v10;
  std::string m_precipitation;
  std::string m_humidity;
  std::string m_temperature;
  std::string m_ice;
};

}  // namespace MetBuild

#endif  // METGET_SRC_VARIABLENAMES_H_
