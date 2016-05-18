# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The `app instances disable-debug` command."""

from googlecloudsdk.api_lib.app import appengine_client
from googlecloudsdk.api_lib.app import flags
from googlecloudsdk.api_lib.app import instances_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


class DisableDebug(base.Command):
  """Disables debug mode for an instance.

  When not in debug mode, SSH will be disabled on the VMs. They will be included
  in the health checking pools.

  Note that any local changes to an instance will be **lost** and the instance
  restarted if debug mode is disabled on the instance.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To disable debug mode for a particular instance, run:

              $ {command} service/version/nwz0

          or

              $ {command} --service=service --version=version nwz0

          To disable debug mode for an instance chosen interactively, run:

              $ {command}
          """,
  }

  @staticmethod
  def Args(parser):
    flags.SERVER_FLAG.AddToParser(parser)
    flags.IGNORE_CERTS_FLAG.AddToParser(parser)
    instance = parser.add_argument(
        'instance', nargs='?',
        help=('The instance to disable debug mode on.'))
    instance.detailed_help = (
        'The instance to disable debug mode on (either an instance name or a '
        'resource path (<service>/<version>/<instance>). If not specified, '
        'select instance interactively. Must uniquely specify (with other '
        'flags) exactly one instance')

    service = parser.add_argument(
        '--service', '-s',
        help='Only match instances belonging to this service.')
    service.detailed_help = (
        'If specified, only match instances belonging to the given service. '
        'This affects both interactive and non-interactive selection.')

    version = parser.add_argument(
        '--version', '-v',
        help='Only match instances belonging to this version.')
    version.detailed_help = (
        'If specified, only match instances belonging to the given version. '
        'This affects both interactive and non-interactive selection.')

  def Run(self, args):
    client = appengine_client.AppengineClient(args.server,
                                              args.ignore_bad_certs)
    # --user-output-enabled=false prevents this from printing, as well as from
    # consuming the generator from the other command
    # The command being called here uses a cli.Execute call under-the-hood, so
    # in order to avoid leaking the abstraction we defer to the implementation
    # in `instances list`.
    all_instances = list(self.cli.Execute(
        ['preview', 'app', 'instances', 'list',
         '--user-output-enabled=false',
         '--project', properties.VALUES.core.project.Get()]))
    instance = instances_util.GetMatchingInstance(
        all_instances, service=args.service, version=args.version,
        instance=args.instance)

    console_io.PromptContinue(
        'Disabling debug mode for instance [{0}].\n\n'
        'Any local changes will be LOST and the instance '
        'restarted.'.format(instance),
        cancel_on_no=True)
    client.SetManagedByGoogle(service=instance.service,
                              version=instance.version, instance=instance.id)
    log.status.Print('Disabled debug mode for instance [{0}].'.format(instance))