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
#include "InterpolationData.h"

using namespace MetBuild;

InterpolationData::InterpolationData(const Triangulation& triangulation,
                                     const MetBuild::Grid::grid& grid)
    : m_triangulation(triangulation),
      m_weights(generate_interpolation_weight(grid)) {}

const InterpolationWeights& InterpolationData::interpolation() const {
  return m_weights;
}

InterpolationWeights& InterpolationData::interpolation() { return m_weights; }

const Triangulation& InterpolationData::triangulation() const {
  return m_triangulation;
}

InterpolationWeights InterpolationData::generate_interpolation_weight(
    const MetBuild::Grid::grid& grid) {
  const auto ni = grid.size();
  const auto nj = grid[0].size();
  InterpolationWeights weights(nj, ni);
  for (size_t i = 0; i < ni; ++i) {
    for (size_t j = 0; j < nj; ++j) {
      auto p = grid[i][j];
      p.setX((std::fmod(p.x() + 180.0, 360.0)) - 180.0);
      auto iw = m_triangulation.getInterpolationFactors(p.x(), p.y());
      weights.set(j, i, iw);
    }
  }
  return weights;
}