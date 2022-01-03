#
# Copyright 2021 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Lint as: python3
"""Serial logs don't contain out-of-memory messages

The messages:
"Out of memory: Kill process" / "sacrifice child" / "Killed process" /
"Memory cgroup out of memory" in serial output usually indicate that
a Linux instance is under memory pressure.
"""
from typing import Optional

from gcpdiag import lint, models
from gcpdiag.lint.gce.utils import LogEntryShort, SerialOutputSearch
from gcpdiag.queries import gce

OOM_MESSAGES = [
    'Out of memory: Kill process',  #
    'sacrifice child',
    'Killed process',
    'Memory cgroup out of memory'
]

logs_by_project = {}


def prepare_rule(context: models.Context):
  logs_by_project[context.project_id] = SerialOutputSearch(
      context, search_strings=OOM_MESSAGES)


def run_rule(context: models.Context, report: lint.LintReportRuleInterface):
  search = logs_by_project[context.project_id]

  instances = gce.get_instances(context).values()
  if len(instances) == 0:
    report.add_skipped(None, 'No instances found')
  else:
    for instance in instances:
      match: Optional[LogEntryShort] = search.get_last_match(
          instance_id=instance.id)
      if match:
        report.add_failed(instance,
                          ('There are messages indicating that OS is running'
                           ' out of memory for {}\n{}: "{}"').format(
                               instance.name, match.timestamp_iso, match.text))
      else:
        report.add_ok(instance)
