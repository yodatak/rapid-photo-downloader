#!/usr/bin/env python3

# Copyright (C) 2011-2016 Damon Lynch <damonlynch@gmail.com>

# This file is part of Rapid Photo Downloader.
#
# Rapid Photo Downloader is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Rapid Photo Downloader is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Rapid Photo Downloader.  If not,
# see <http://www.gnu.org/licenses/>.

__author__ = 'Damon Lynch'
__copyright__ = "Copyright 2011-2016, Damon Lynch"

import subprocess
import datetime, time
import logging
from typing import Optional

import arrow.arrow
from arrow.arrow import Arrow

import raphodo.exiftool as exiftool
from raphodo.utilities import datetime_roughly_equal

try:
    import pymediainfo
    have_pymediainfo = True
except ImportError:
    have_pymediainfo = False

def version_info() -> Optional[str]:
    """
    returns the version of Exiftool being used

    :return version number, or None if Exiftool cannot be found
    """
    try:
        return subprocess.check_output(['exiftool', '-ver']).strip().decode()
    except OSError:
        logging.error("Could not locate Exiftool")
        return None

def pymedia_version_info() -> Optional[str]:
    if have_pymediainfo:
        return pymediainfo.__version__
    else:
        return None

EXIFTOOL_VERSION = version_info()

# Run Exiftool in a context manager, which will ensure it is terminated
# properly. Then call this class
# with exiftool.ExifTool() as et_process:


class MetaData:
    """
    Get video metadata using Exiftool

    :param filename: the file from which to get metadata
    :param et_process: instance of ExifTool class, which allows
    calling EXifTool without it exiting with each call
    """
    def __init__(self, full_file_name: str, et_process: exiftool.ExifTool):


        self.filename = full_file_name
        self.metadata = dict()
        self.metadata_string_format = dict()
        self.et_process = et_process
        if have_pymediainfo:
            self.media_info =  pymediainfo.MediaInfo.parse(full_file_name)  # type: pymediainfo.MediaInfo
        else:
            self.media_info = None

    def _get(self, key, missing):

        if key in ("VideoStreamType", "FileNumber"):
            # special case: want exiftool's string formatting
            # i.e. no -n tag
            if not self.metadata_string_format:
                self.metadata_string_format = \
                    self.et_process.execute_json_no_formatting(self.filename)
            try:
                return self.metadata_string_format[0][key]
            except:
                return missing

        elif not self.metadata:
            self.metadata = self.et_process.get_metadata(self.filename)

        return self.metadata.get(key, missing)

    def _exiftool_date_time(self, missing: Optional[str]='') -> datetime.datetime:
        d = self._get('DateTimeOriginal', None)
        if d is None:
            d = self._get('CreateDate', None)
        if d is None:
            d = self._get('FileModifyDate', None)
        if d is not None:
            d = d.strip()
            try:
                # returned value may or may not have a time offset
                if len(d) > 19:
                    # remove the : from the timzone component, if it's present
                    if d[-3] == ':' and (d[-6] in ('+', '-')):
                        d = d[:-3] + d[-2:]
                    dt = datetime.datetime.strptime(d, "%Y:%m:%d %H:%M:%S%z")
                else:
                    dt = datetime.datetime.strptime(d, "%Y:%m:%d %H:%M:%S")

            except ValueError:
                logging.warning("Error parsing date time metadata %s for video %s", d,
                                self.filename)
                return missing
            except Exception:
                logging.error("Unknown error parsing date time metadata %s for video %s", d,
                                self.filename)
                return missing


            return dt
        else:
            return missing

    def date_time(self, missing: Optional[str]='') -> datetime.datetime:
        """
        Returns in python datetime format the date and time the image was
        recorded.

        Trys to get value from key "DateTimeOriginal"
        If that fails, tries "CreateDate", and then finally
        FileModifyDate

        Returns missing either metadata value is not present.
        """

        if have_pymediainfo:
            try:
                d = self.media_info.to_data()['tracks'][0]['encoded_date']  # type: str
            except KeyError:
                logging.warning('Failed to extract date time from %s using pymediainfo: trying '
                              'ExifTool', self.filename)
                return self._exiftool_date_time(missing)
            else:
                # format of date string is something like:
                # UTC 2016-05-09 03:28:03
                try:
                    if d.startswith('UTC'):
                        u = d[4:]
                        a = arrow.get(u, "YYYY-MM-DD HH:mm:ss")  # type: Arrow
                        dt_mi = a.to('local')
                        dt = dt_mi.datetime  # type: datetime.datetime

                        # Compare the value returned by mediainfo against that
                        # returned by ExifTool, if and only if there is a time zone
                        # setting in the video file that ExifTool can extract
                        tz = self._get('TimeZone', None)
                        if tz is None:
                            logging.debug("Using pymediainfo datetime, because ExifTool did not "
                                          "detect a time zone in %s", self.filename)
                        if tz is not None:
                            dt_et = self._exiftool_date_time(missing=None)
                            if dt_et is not None:
                                hour = tz // 60 * -1
                                minute = tz % 60 * -1
                                adjusted_dt_mi = dt_mi.replace(hours=hour, minutes=minute).naive
                                if datetime_roughly_equal(adjusted_dt_mi, dt_et):
                                    logging.debug("Favoring ExifTool datetime metadata over "
                                                  "mediainfo for %s, because it includes a "
                                                  "timezone", self.filename)
                                    dt = dt_et
                                else:
                                    logging.debug("Although ExifTool located a time zone"
                                        "in %s's metadata, using the mediainfo result, "
                                        "because the two results are different. Mediainfo: %s / "
                                        "%s  (before / after). ExifTool: %s. Time zone: %s",
                                        self.filename, dt, adjusted_dt_mi, dt_et, tz)

                    else:
                        dt = datetime.datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    logging.warning("Error parsing date time metadata %s for video %s. Will try "
                                    "ExifTool.", d, self.filename)
                    return self._exiftool_date_time(missing)
                except arrow.parser.ParserError:
                    logging.warning("Error parsing date time metadata using Arrow %s for video "
                                    "%s. Will try ExifTool.", d, self.filename)
                    return self._exiftool_date_time(missing)
                except Exception as e:
                    logging.error("Unknown error parsing date time metadata %s for video %s. %s. "
                                  "Will try ExifTool.", d, self.filename, e)
                    return self._exiftool_date_time(missing)
                except:
                    logging.error("Unknown error parsing date time metadata %s for video %s. "
                                  "Will try ExifTool.", d, self.filename)
                    return self._exiftool_date_time(missing)
                else:
                    return dt

        else:
            return self._exiftool_date_time(missing)


    def timestamp(self, missing='') -> float:
        """
        Returns a float value representing the time stamp, if it exists
        """
        dt = self.date_time(missing=None)
        if dt is not None:
            try:
                ts = dt.timestamp()
            except:
                ts = missing
        else:
            ts = missing
        return float(ts)

    def file_number(self, missing=''):
        v = self._get("FileNumber", None)
        if v is not None:
            return str(v)
        else:
            return missing

    def width(self, missing=''):
        v = self._get('ImageWidth', None)
        if v is not None:
            return str(v)
        else:
            return missing

    def height(self, missing=''):
        v = self._get('ImageHeight', None)
        if v is not None:
            return str(v)
        else:
            return missing

    def length(self, missing=''):
        """
        return the duration (length) of the video, rounded to the nearest second, in string format
        """
        v = self._get("Duration", None)
        if v is not None:
            try:
                v = float(v)
                v = "%0.f" % v
            except:
                return missing
            return v
        else:
            return missing

    def frames_per_second(self, missing=''):
        v = self._get("FrameRate", None)
        if v is None:
            v = self._get("VideoFrameRate", None)

        if v is None:
            return missing
        try:
            v = '%.0f' % v
        except:
            return missing
        return v

    def codec(self, missing=''):
        v = self._get("VideoStreamType", None)
        if v is None:
            v = self._get("VideoCodec", None)
        if v is not None:
            return v
        return missing

    def fourcc(self, missing=''):
        return self._get("CompressorID", missing)

    def rotation(self, missing=0) -> int:
        v = self._get("Rotation", None)
        if v is not None:
            return v
        return missing


class DummyMetaData():
    """
    Class which gives metadata values for an imaginary video.

    Useful for displaying in preference examples etc. when no video is ready to
    be downloaded.
    """
    def __init__(self, filename, et_process):
        pass

    def date_time(self, missing=''):
        return datetime.datetime.now()

    def codec(self, stream=0, missing=''):
        return 'H.264 AVC'

    def length(self, missing=''):
        return '57'

    def width(self, stream=0, missing=''):
        return '1920'

    def height(self, stream=0, missing=''):
        return '1080'

    def frames_per_second(self, stream=0, missing=''):
        return '24'

    def fourcc(self, stream=0, missing=''):
        return 'AVC1'

if __name__ == '__main__':
    import sys

    with exiftool.ExifTool() as et_process:
        if (len(sys.argv) != 2):
            print('Usage: ' + sys.argv[0] + ' path/to/video/containing/metadata')
        else:
            file = sys.argv[1]

            print("ExifTool", EXIFTOOL_VERSION)
            m = MetaData(file, et_process)
            dt = m.date_time()
            print(dt)
            print("%sx%s" % (m.width(), m.height()))
            print("Length:", m.length())
            print("FPS: ", m.frames_per_second())
            print("Codec:", m.codec())

