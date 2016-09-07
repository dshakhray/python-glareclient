# Copyright (c) 2016 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys

from glareclient.common import progressbar
from glareclient.common import utils

from osc_lib.command import command
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class UploadBlob(command.ShowOne):
    """Upload blob"""

    def get_parser(self, prog_name):
        parser = super(UploadBlob, self).get_parser(prog_name)
        parser.add_argument(
            'id',
            metavar='<ID>',
            help='ID of the artifact to upload blob.',
        )
        parser.add_argument(
            '--type-name',
            default=None,
            metavar='<TYPE_NAME>',
            help='Name of artifact type.',
        )
        parser.add_argument(
            '--blob',
            default=None,
            metavar='<TYPE_NAME>',
            help='Local file that contains blob to be uploaded.',
        )
        parser.add_argument(
            '--blob-property',
            metavar='<BLOB_PROP>',
            default=None,
            help='Name of the blob field.'
        )
        parser.add_argument(
            '--progress',
            default=False,
            help='Show download progress bar.'
        )
        return parser

    def take_action(self, parsed_args):
        LOG.debug('take_action({0})'.format(parsed_args))
        client = self.app.client_manager.artifact

        if not parsed_args.blob_property:
            utils.exit('Not specified --blob-property.')

        blob = utils.get_data_file(parsed_args.blob)
        if parsed_args.progress:
            file_size = utils.get_file_size(blob)
            if file_size is not None:
                blob = progressbar.VerboseFileWrapper(blob, file_size)

        client.artifacts.upload_blob(parsed_args.id,
                                     parsed_args.blob_property,
                                     blob,
                                     type_name=parsed_args.type_name)

        data = client.artifacts.get(parsed_args.id,
                                    type_name=parsed_args.type_name)

        size = data[parsed_args.blob_property].pop('size', None)
        data_to_display = {'blob_property': parsed_args.blob_property,
                           'id': parsed_args.id,
                           'name': data['name'],
                           'version': data['version'],
                           'status': data['status'],
                           'size': utils.make_size_human_readable(size)}
        data_to_display.update(data[parsed_args.blob_property])
        return self.dict2columns(data_to_display)


class DownloadBlob(command.ShowOne):
    """Download blob"""

    def get_parser(self, prog_name):
        parser = super(DownloadBlob, self).get_parser(prog_name)
        parser.add_argument(
            'id',
            metavar='<ID>',
            help='ID of the artifact to download blob.',
        )
        parser.add_argument(
            '--type-name',
            default=None,
            metavar='<TYPE_NAME>',
            help='Name of artifact type.',
        )
        parser.add_argument(
            '--progress',
            default=False,
            help='Show download progress bar.'
        )
        parser.add_argument(
            '--file',
            metavar='<FILE>',
            help='Local file to save downloaded blob to. '
                 'If this is not specified and there is no redirection '
                 'the blob will not be saved.'
        )
        parser.add_argument(
            '--blob-property',
            metavar='<BLOB_PROP>',
            default=None,
            help='Name of the blob field.'
        )
        return parser

    def take_action(self, parsed_args):
        LOG.debug('take_action({0})'.format(parsed_args))
        client = self.app.client_manager.artifact
        data = client.artifacts.download_blob(parsed_args.id,
                                              parsed_args.blob_property,
                                              type_name=parsed_args.type_name)
        if parsed_args.progress:
            data = progressbar.VerboseIteratorWrapper(data, len(data))
        if not (sys.stdout.isatty() and parsed_args.file is None):
            utils.save_blob(data, parsed_args.file)
            return self.dict2columns(())
        else:
            msg = ('No redirection or local file specified for downloaded '
                   'blob. Please specify a local file with --file to save '
                   'downloaded blob or redirect output to another source.')
            utils.exit(msg)
