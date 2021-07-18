# Copyright 2021 Google LLC
#
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
"""GCE instance service account permissions for logging.

The service account used by GCE instance should have the logging.logWriter
permission, otherwise, if you install the logging agent, it won't be able
to send the logs to Cloud Logging.
"""

import operator as op

from gcp_doctor import lint, models
from gcp_doctor.queries import gce, iam

ROLE = 'roles/logging.logWriter'


def prefetch_rule(context: models.Context):
  # Make sure that we have the IAM policy in cache.
  project_ids = {i.project_id for i in gce.get_instances(context).values()}
  for pid in project_ids:
    iam.get_project_policy(pid)


def run_rule(context: models.Context, report: lint.LintReportRuleInterface):
  instances = gce.get_instances(context)
  instances_count = 0
  for i in sorted(instances.values(), key=op.attrgetter('project_id', 'name')):
    # GKE nodes are checked by another test.
    if i.is_gke_node():
      continue
    instances_count += 1
    iam_policy = iam.get_project_policy(i.project_id)
    sa = i.service_account
    if not sa:
      report.add_failed(i, 'no service account')
    elif not iam_policy.has_role_permissions(f'serviceAccount:{sa}', ROLE):
      report.add_failed(i, f'service account: {sa}\nmissing role: {ROLE}')
    else:
      report.add_ok(i)
  if not instances_count:
    report.add_skipped(None, 'no instances found')
