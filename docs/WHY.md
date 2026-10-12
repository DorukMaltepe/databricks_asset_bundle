# Why it's built this way

Short notes on each decision, so you can tell which ones to keep and which to change.

## Asset Bundles instead of clicking in the UI or calling the Jobs API

A job's definition is stored in git next to its code, so a change to it gets reviewed like any other
code change. `databricks bundle deploy` compares what is deployed with what is in git, so deleting a
job from YAML deletes it from the workspace. One definition with per-target overrides
(`catalog`, `permissions`) means staging and prod can't slowly drift apart.

## Three targets, three different jobs

- **dev** uses `mode: development`. Each engineer deploys a private copy, prefixed `[dev <name>]`,
  with schedules paused, writing to their own `dev_<user>` schema. Nobody overwrites anyone else.
- **staging** is deployed by CI on every merge, and CI also *runs* the job there. A deploy can
  succeed while the job is still broken, for example a missing table or a missing grant. Running
  the job catches that before prod.
- **prod** uses `mode: production`, which makes the CLI refuse some unsafe setups (for example,
  user-specific paths). Only CI deploys it, after a person approves in GitHub.

Prod gets the **same commit** that passed staging. Promotion is "approve this run," not
"merge to another branch." Keeping one branch removes merge-conflict releases and the question
of which branch prod is actually running.

## Service principal + OAuth for CI

CI authenticates as a service principal with OAuth M2M (client ID + secret), not with a
person's personal access token. Deployed jobs then belong to that service principal, so they keep
running when someone leaves the company. The credentials are stored per GitHub Environment, so a PR
build never sees them, and prod secrets are only released after approval.

## Logic split from I/O (`transforms.py` vs `main.py`)

Transformations take a DataFrame and return a DataFrame. They never read or write tables
themselves, so the tests can run them on a local `SparkSession` in seconds, with no workspace,
cluster or credentials. `main.py` does all the reading and writing and is kept small enough that
the staging run is enough to test it.

## A wheel instead of notebooks

A wheel has a version and a list of dependencies. It is built the same way locally and in CI
(`uv build`), and it can be imported in tests. Notebooks are great for exploring data but hard to
review and to test. The bundle builds the wheel and uploads it on every deploy.

## Serverless jobs

There is no cluster size, runtime version or node type to choose and keep in sync for each
environment. If you need a particular runtime or instance type, change the `environments` block
to a `job_clusters` block. Nothing else has to change.

## Terraform for permissions, bundles for jobs

The two tools manage different things on different schedules:

| | Terraform | Bundle |
|---|---|---|
| Manages | who can access the workspace and which data they can read or write | jobs/pipelines and who can see them |
| Changes | rarely, needs an admin | on every merge |
| Run by | a platform admin | CI's service principal |

Keeping them separate means the deploy credential doesn't need admin rights. It has write
access to its own catalog and nothing else.

`databricks_grants` is **authoritative**: any grant on the catalog that isn't in the code is
removed when you run `apply`. That's the point. Permissions someone added in the UI disappear
instead of piling up. Groups are referenced by name, not created here, because Unity Catalog
grants need *account-level* groups, which are usually synced from your identity provider.

Engineers can write in `dev` and only read in `staging` and `prod`. Changes reach prod
through CI, not through someone's laptop.

## What's deliberately left out

- Delta Live Tables / Lakeflow pipelines, ML, dashboards: add them as more files in `resources/`.
- Integration tests that run against a real workspace: the staging run plays that role for now.
- A Terraform backend: choose S3, Azure Storage or GCS, and give each environment its own state.
