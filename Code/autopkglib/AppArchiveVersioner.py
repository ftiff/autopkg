#!/usr/bin/python
#
# Copyright 2016 Francois 'ftiff' Levaux-Tiffreau
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""See docstring for AppDmgVersioner class"""

import string
import zipfile
import re

#pylint: disable=no-name-in-module
#pylint: disable=line-too-long
try:
    from Foundation import NSPropertyListSerialization
    from Foundation import NSPropertyListMutableContainers
except ImportError:
    print "WARNING: Failed 'from Foundation import NSData, NSPropertyListSerialization' in " + __name__
    print "WARNING: Failed 'from Foundation import NSPropertyListMutableContainers' in " + __name__
#pylint: enable=no-name-in-module
#pylint: enable=line-too-long

from autopkglib import Processor, ProcessorError


__all__ = ["AppArchiveVersioner"]


class AppArchiveVersioner(Processor):
    # we dynamically set the docstring from the description (DRY), so:
    #pylint: disable=missing-docstring
    description = "Extracts bundle ID and version of app inside zip."
    input_variables = {
        "zip_path": {
            "required": True,
            "description": "Path to a zip containing an app.",
        },
    }
    output_variables = {
        "app_name": {
            "description": "Name of app found on the disk image."
        },
        "bundleid": {
            "description": "Bundle identifier of the app.",
        },
        "version": {
            "description": "Version of the app.",
        },
    }

    __doc__ = description

    def read_bundle_info(self, plist):
        """Parses Info.plist (as string)"""
        #pylint: disable=no-self-use
        plist_nsdata = buffer(plist)

        #pylint: disable=line-too-long
        info, _, error = (
            NSPropertyListSerialization.propertyListFromData_mutabilityOption_format_errorDescription_(
                plist_nsdata,
                NSPropertyListMutableContainers,
                None,
                None))
        #pylint: enable=line-too-long

        if error:
            raise ProcessorError("Can't read %s: %s" % (plist, error))

        return info

    def main(self):

        zip_path = self.env.get("zip_path")
        if not zip_path:
            raise ProcessorError(
                "Expected an 'zip_path' input variable but none is set!")
        # Get Info.plist from the archive
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:

                # Get Info.plist path in archive
                zip_contents = zip_file.namelist()
                pattern = r'[^/]*.app/Contents/Info.plist'
                info_plist_list = [s for s in zip_contents if re.match(pattern, s)]

                assert len(info_plist_list) == 1, "Archive should contain exactly one Info.plist"

                # Get the name of app
                app_name = string.split(info_plist_list[0], '/')[0]

                # read Info.plist
                info_plist = zip_file.read(info_plist_list[0])
        except BaseException as err:
            raise ProcessorError(err)

        info = self.read_bundle_info(info_plist)
        try:
            self.env["app_name"] = app_name
            self.env["bundleid"] = info["CFBundleIdentifier"]
            self.env["version"] = info["CFBundleShortVersionString"]
            self.output("BundleID: %s" % self.env["bundleid"])
            self.output("Version: %s" % self.env["version"])
        except BaseException as err:
            raise ProcessorError(err)


if __name__ == '__main__':
    PROCESSOR = AppArchiveVersioner()
    PROCESSOR.execute_shell()

