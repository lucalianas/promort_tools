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


class ROIsExtractor(object):
    def __init__(self, host, user, passwd, session_id, logger):
        self.promort_client = ProMortClient(host, user, passwd, session_id)
        self.logger = logger

    def _get_ome_server_base_url(self):
        response = self.promort_client.get(
            api_url='api/utils/omeseadragon_base_urls/',
            payload=None
        )
        if response.status_code == requests.codes.OK:
            return response.json()['base_url']

    def _get_slide_details(self, slide_id, slide_type, ome_server):
        if slide_type == 'MIRAX':
            url = urljoin(ome_server, f'mirax/deepzoom/get/{slide_id}_metadata.json')
        else:
            url = urljoin(ome_server, f'deepzoom/get/{slide_id}_metadata.json')
        response = requests.get(url)
        if response.status_code == requests.codes.OK:
            return response.json()

    def _get_slide_data(self, slide_label):
        response = self.promort_client.get(
            api_url=f'api/slides/{slide_label}/',
            payload=None
        )
        if response.status_code == requests.codes.OK:
            slide_data = response.json()
        ome_server_base_url = self._get_ome_server_base_url()
        if slide_data['image_type'] == 'MIRAX':
            slide_details = self._get_slide_details(slide_data['id'], slide_data['image_type'], ome_server_base_url)
        else:
            slide_details = self._get_slide_details(slide_data['omero_id'], slide_data['image_type'], ome_server_base_url)
        slide_data.update({
            'height': slide_details['tile_sources']['Image']['Size']['Height'],
            'width':slide_details['tile_sources']['Image']['Size']['Width'] })
        return slide_data

    def _load_rois_list(self, slide_label, roi_type):
        response = self.promort_client.get(
            api_url=f'api/slides/{slide_label}/rois/',
            payload={'roi_type': roi_type}
        )
        if response.status_code == requests.codes.OK:
            return response.json()

    def _extract_points(self, roi_json):
        points = json.loads(roi_json)['segments']
        return [(p['point']['x'], p['point']['y']) for p in points]

    def _get_roi_details(self, roi_id, roi_type):
        response = self.promort_client.get(
            api_url=f'api/{roi_type}s/{roi_id}/',
            payload=None
        )
        if response.status_code == requests.codes.OK:
            roi_data = response.json()
            points = self._extract_points(roi_data['roi_json'])
            if roi_type == 'slice':
                positive = (roi_data.get('positive_cores_count') > 0)
            elif roi_type == 'core':
                positive = roi_data.get('positive')
            elif roi_type == 'focus_region':
                positive = (roi_data.get('tissue_status') == 'TUMOR')
        return points, positive

    def _serialize_points_list(self, roi_id, roi_type, points, out_path):
        fname = f'{roi_type}_{roi_id}.json'
        with open(os.path.join(out_path, fname), 'w') as f:
            f.write(json.dumps(points))
        return fname

    def run(self, args):
        try:
            self.promort_client.login()
        except ProMortAuthenticationError:
            self.logger.critical('Authentication error')
            sys.exit('Authentication error')
        slide_data = self._get_slide_data(args.slide_label)
        rois_list = self._load_rois_list(args.slide_label, args.roi_type)
        roi_details = []
        for roi in rois_list:
            points, positive = self._get_roi_details(roi['roi_id'], roi['roi_type'])
            fname = self._serialize_points_list(roi['roi_id'], roi['roi_type'], points, args.out_folder)
            roi_details.append({
                'roi_id': roi['roi_id'],
                'roi_type': roi['roi_type'],
                'annotation_step': roi['annotation_step'],
                'shape_file': os.path.join(args.out_folder, fname),
                'positive': positive
            })
        slide_data['rois'] = roi_details
        if args.out_file is None:
            sys.stdout.write(json.dumps(slide_data))
        else:
            try:
                with open(args.out_file, 'w') as f:
                    f.write(json.dumps(slide_data))
            except FileNotFoundError:
                self.logger.critical("Can't write to {0}".format(args.out_file))


help_doc = """
TBD
"""


def implementation(host, user, passwd, session_id, logger, args):
    rois_extractor = ROIsExtractor(host, user, passwd, session_id, logger)
    rois_extractor.run(args)


def make_parser(parser):
    parser.add_argument("--slide-label", type=str, required=True, help="slide label")
    parser.add_argument(
        "--roi-type",
        choices=["slice", "core", "focus_region"],
        required=True,
        help="ROI type to be extracted for selected slide"
    )
    parser.add_argument(
        "--out-folder",
        type=str,
        required=True,
        help="output folder for ROIs JSON files"
    )
    parser.add_argument(
        "--out-file",
        type=str,
        default=None,
        help="output file, if not provided will prompt to stdout"
    )


def register(registration_list):
    registration_list.append(("rois_extractor", help_doc, make_parser, implementation))
