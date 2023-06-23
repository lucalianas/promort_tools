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


import sys
import ezomero


class OMEPathResolver(object):
    def __init__(self, ome_client, logger):
        self.ome_client = ome_client
        self.logger = logger

    def disconnect(self):
        self.ome_client.close()

    def run(self, args):
        slide_id = args.slide_id
        slide_type = args.slide_type
        if slide_type == "OMERO_IMG":
            self.logger.info(f"Loading path for slide {slide_id}")
            fpath = ezomero.get_original_filepaths(self.ome_client, slide_id)[0]
            sys.stdout.write(fpath)
        else:
            self.logger.critical(f"Slide type {slide_type} can't be resolved")
            sys.exit(f"Slide type {slide_type} can't be resolved")


help_doc = """
TBD
"""


def implementation(ome_client, logger, args):
    rois_extractor = OMEPathResolver(ome_client, logger)
    rois_extractor.run(args)
    rois_extractor.disconnect()


def make_parser(parser):
    parser.add_argument(
        "--slide-id", type=int, required=True, help="slide ID in OMERO server"
    )
    parser.add_argument(
        "--slide-type",
        choices=["OMERO_IMG", "MIRAX"],
        default="OMERO_IMG",
        help="Slide type, OMERO_IMG is a slide natively managed by OMERO, MIRAX is a MIRAX file handles as OriginalFile object",
    )


def register(registration_list):
    registration_list.append(("slide_path_resolver", help_doc, make_parser, implementation))
