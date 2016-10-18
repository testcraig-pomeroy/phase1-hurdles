/**
 * Copyright 2016 DARPA.
 *
 * This is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this software; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 *
 */


namespace cpp hurdle2_rpc
namespace py hurdle2_rpc


enum BinContents {
    NOISE,
    FM,
    QPSK,
    GMSK
}


service Hurdle2Scoring {

  /**
   * Submits a result to the Hurdle 2 scoring engine. Returns true if 
   * the submission passes a simple sanity check (number of bins)
   */

    bool submitAnswer(1:map<i32,BinContents> solution)


}
