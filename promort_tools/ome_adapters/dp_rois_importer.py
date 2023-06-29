#  Copyright (c) 2023, CRS4
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of
#  this software and associated documentation files (the "Software"), to deal in
#  the Software without restriction, including without limitation the rights to
#  use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
#  the Software, and to permit persons to whom the Software is furnished to do so,
#  subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
#  FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#  COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
#  IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#  CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import json, os, sys, ezomero
from ezomero.rois import Polygon


class ROIsImporter(object):
    def __init__(self, ome_client, logger):
        self.ome_client = ome_client
        self.logger = logger

    def disconnect(self):
        self.ome_client.close()

    def _roi_to_ome(self, ome_slide_id, roi):
        with open(roi["shape_file"])  as f:
            polygon = Polygon(
                points=json.load(f),
                label=roi["roi_label"]
            )
        ome_roi_id = ezomero.post_roi(
            self.ome_client,
            ome_slide_id,
            shapes=[polygon,],
            stroke_color=(0,0,0,0),
            stroke_width=20,
            name=roi["roi_label"]
        )
        return ome_roi_id

    def run(self, args):
        try:
            with open(args.rois_details_file) as f:
                rois_details = json.loads(f.read())
        except FileNotFoundError:
            self.logger.critical(f"File {args.rois_details_file} not found")
            sys.exit()
        if rois_details["image_type"] != "OMERO_IMG":
            self.logger.critical("This tools works only with images handled by OMERO")
            sys.exit()
        for roi in rois_details["rois"]:
            ome_roi_id = self._roi_to_ome(roi["omero_id"], roi)


help_doc = """
TBD
"""


def implementation(ome_client, logger, args):
    rois_extractor = ROIsImporter(ome_client, logger)
    rois_extractor.run(args)
    rois_extractor.disconnect()


def make_parser(parser):
    parser.add_argument(
        "--rois-details-file",
        type=str,
        required=True,
        help="JSON file containing ROI details, produced using the rois_extractor tool",
    )


def register(registration_list):
    registration_list.append(
        ("dp_rois_importer", help_doc, make_parser, implementation)
    )
