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

from ..libs.client import ProMortClient
from ..libs.client import ProMortAuthenticationError

import os, sys, requests, json
from urllib.parse import urljoin


class SlideDetailsExtractor(object):
    def __init__(self, host, user, passwd, session_id, logger):
        self.promort_client = ProMortClient(host, user, passwd, session_id)
        self.logger = logger

    def _get_ome_server_base_url(self):
        response = self.promort_client.get(
            api_url="api/utils/omeseadragon_base_urls/", payload=None
        )
        if response.status_code == requests.codes.OK:
            return response.json()["base_url"]

    def _get_slide_details(self, slide_id, slide_type, ome_server):
        if slide_type == "MIRAX":
            url = urljoin(ome_server, f"mirax/deepzoom/get/{slide_id}_metadata.json")
        else:
            url = urljoin(ome_server, f"deepzoom/get/{slide_id}_metadata.json")
        response = requests.get(url)
        if response.status_code == requests.codes.OK:
            return response.json()

    def _get_slide_data(self, slide_label):
        response = self.promort_client.get(
            api_url=f"api/slides/{slide_label}/", payload=None
        )
        if response.status_code == requests.codes.OK:
            slide_data = response.json()
        ome_server_base_url = self._get_ome_server_base_url()
        if slide_data["image_type"] == "MIRAX":
            slide_details = self._get_slide_details(
                slide_data["id"], slide_data["image_type"], ome_server_base_url
            )
        else:
            slide_details = self._get_slide_details(
                slide_data["omero_id"], slide_data["image_type"], ome_server_base_url
            )
        slide_data.update(
            {
                "height": slide_details["tile_sources"]["Image"]["Size"]["Height"],
                "width": slide_details["tile_sources"]["Image"]["Size"]["Width"],
            }
        )
        return slide_data

    def run(self, args):
        try:
            self.promort_client.login()
        except ProMortAuthenticationError:
            self.logger.critical("Authentication error")
            sys.exit("Authentication error")
        slide_data = self._get_slide_data(args.slide_label)
        if slide_data:
            sys.stdout.write(json.dumps(slide_data))
        else:
            self.logger.critial("No slide data available")
            sys.exit("No slide data available")


help_doc = """
TBD
"""


def implementation(host, user, passwd, session_id, logger, args):
    slide_details_extractor = SlideDetailsExtractor(
        host, user, passwd, session_id, logger
    )
    slide_details_extractor.run(args)


def make_parser(parser):
    parser.add_argument("--slide-label", type=str, required=True, help="slide label")


def register(registration_list):
    registration_list.append(("slide_details", help_doc, make_parser, implementation))
