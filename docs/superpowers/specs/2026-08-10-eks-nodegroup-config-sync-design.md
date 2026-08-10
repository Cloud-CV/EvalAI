# EKS nodegroup config sync

Date: 2026-08-10

## Problem

A challenge's `worker_instance_type`, `worker_ami_type` and `worker_disk_size`
reach AWS exactly once, in `create_eks_nodegroup`, and that task runs on a
snapshot of the challenge serialized at the moment `approved_by_admin` flipped
to `True`. The serialized blob is threaded unchanged through
`setup_eks_cluster` → `create_eks_cluster_subnets` → `create_eks_cluster` →
`create_eks_nodegroup`; no task re-reads the database.

Two consequences:

1. Editing any of those three fields after approval changes only the database.
   AWS keeps running the old hardware, with nothing to surface the mismatch.
2. Even before the nodegroup exists, an edit made after approval is ignored,
   because the snapshot was taken at approval time.

AWS offers no in-place fix: `UpdateNodegroupConfig` accepts only scaling
config, labels, taints and update config. `instanceTypes`, `amiType` and
`diskSize` are fixed for the life of a managed nodegroup. The console's Edit
button does not expose them either. The only way to change them is to delete
the nodegroup and create a new one.

Observed case: challenge 2319 runs `g5.4xlarge` nodes. Neither the Django admin
nor the AWS console can change that.

## Goals

- Editing a worker configuration field on a Challenge makes AWS match, with no
  shell access and no manual AWS work.
- A misconfiguration cannot leave a challenge without worker capacity.
- An operator can retry a failed sync without having to fake a field change.

## Non-goals

- Changing how the initial cluster and nodegroup are created.
- Draining or rescheduling submissions before replacing a nodegroup.
- Reconciling drift that predates this change; existing nodegroups are only
  touched when someone edits a field or runs the admin action.

## Design

### Field groups

Two tuples in `settings/common.py` name the fields that matter:

- `EKS_NODEGROUP_IMMUTABLE_FIELDS` — `worker_instance_type`,
  `worker_ami_type`, `worker_disk_size`. Changing one requires a recreate.
- `EKS_NODEGROUP_SCALING_FIELDS` — `min_worker_instance`,
  `max_worker_instance`, `desired_worker_instance`. These map to
  `scalingConfig`, which `UpdateNodegroupConfig` can change in place.

`Challenge.__init__` snapshots all six as `_original_<field>`, extending the
pattern already used for `approved_by_admin` and `sqs_retention_period`.

### Trigger

A `post_save` receiver, `sync_eks_nodegroup_config_for_challenge`, delegates to
`eks_nodegroup_config_change_callback` in `aws_utils`. The callback:

1. Returns early when `settings.DEBUG or settings.TEST`. The hook fires on
   every Challenge save, so without this the test suite would dispatch Celery
   tasks at a broker that is not running.
2. Returns early for challenges that are not code-upload
   (`is_docker_based` false, or `remote_evaluation` true).
3. Diffs the two field groups with `is_model_field_changed`.
4. Refreshes every `_original_` snapshot, so a second save of the same value is
   not a second recreate.
5. Dispatches `recreate_eks_nodegroup` when an immutable field changed,
   otherwise `update_eks_nodegroup_scaling` when only scaling changed.

When both groups changed, only the recreate is dispatched: `create_nodegroup`
already sends the new `scalingConfig`, so an update as well would be a
redundant AWS call.

### Validation gate

`validate_eks_nodegroup_config` runs before anything is deleted and returns a
list of human-readable problems:

- `worker_instance_type` is set, and offered in the challenge's region
  (`describe_instance_type_offerings`).
- `worker_ami_type` is one of `EKS_SUPPORTED_AMI_TYPES`.
- The AMI type ships NVIDIA drivers (`EKS_GPU_AMI_TYPES`) unless
  `cpu_only_jobs` is set. A GPU challenge on a standard AMI schedules pods that
  can never see a GPU.
- AL2 AMI types are rejected on Kubernetes >= `EKS_AL2_REMOVED_IN_VERSION`
  (1.33), where they no longer exist. The cluster version comes from
  `describe_cluster`.
- `worker_disk_size` is a positive integer.

A non-empty result aborts the recreate with a logged error and leaves the
existing nodegroup untouched.

### Recreate

`recreate_eks_nodegroup(challenge_pk)` takes a primary key rather than a
serialized challenge, so it always reads current database state. This is the
same staleness that caused the original problem.

1. Resolve challenge, cluster name and nodegroup name via
   `_get_challenge_nodegroup`. No `ChallengeEvaluationCluster` means no-op.
2. Validate; abort on any error.
3. Log a warning that submissions on the nodegroup's nodes will be terminated.
4. `delete_nodegroup`, then wait on `nodegroup_deleted`.
   `ResourceNotFoundException` falls through to create; any other error aborts
   before create, since creating over a half-deleted nodegroup would fail.
5. `create_nodegroup_for_challenge`, extracted from `create_eks_nodegroup` so
   both paths always send the same argument set.
6. On create failure, log that the challenge now has no worker capacity.

The nodegroup name is derived from title, pk and environment by
`get_nodegroup_name_for_challenge`, so a recreate reuses the same name and
`ChallengeEvaluationCluster.nodegroup_name` — which the autoscale Lambda
targets — stays valid.

The recreate path does not send
`construct_and_send_eks_cluster_creation_mail`; that stays on initial creation
only, so hosts do not get a second "cluster created" email per edit.

### Scaling update

`update_eks_nodegroup_scaling(challenge_pk)` calls `update_nodegroup_config`
with the challenge's three scaling values. The autoscale Lambda rewrites
`minSize` and `desiredSize` from the pending submission count on its next run.
`maxSize` is the durable one: the Lambda caps scale-up at the challenge's
`max_worker_instance`, read through the autoscale meta endpoint.

### Admin action

`recreate_selected_eks_nodegroups` on `ChallengeAdmin` enqueues
`recreate_eks_nodegroup` for each selected code-upload challenge and reports
how many were queued and skipped. This is the retry path when a validation
failure has left the database and AWS out of step — re-saving the same value is
a no-op, because the snapshot was already refreshed.

## Accepted risk

Recreation is immediate and unconditional. Deleting a nodegroup terminates any
node currently running a submission, and nothing checks the node count first.
An admin editing `worker_instance_type` on a busy challenge will kill its
running evaluations. This was chosen deliberately over an idle-only or
deferred-until-idle policy; the mitigation is a warning log before the delete
and the narrow trigger conditions.

## Testing

`tests/unit/challenges/test_aws_utils.py` adds 24 tests:

- `TestValidateEKSNodegroupConfig` — each rejection reason, plus the AL2 and
  CPU-only cases that must still pass.
- `TestRecreateEKSNodegroup` — delete-then-create ordering, abort before delete
  on invalid config, missing nodegroup still creates, delete error aborts
  before create, failed create reports lost capacity, missing cluster no-op.
- `TestUpdateEKSNodegroupScaling` — scaling config sent, client error reported.
- `TestEKSNodegroupConfigChangeCallback` — no dispatch when nothing changed,
  recreate on immutable change, scale on scaling change, recreate wins when
  both change, non-code-upload ignored, DEBUG and TEST guards.
