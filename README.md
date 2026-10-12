# Databricks Asset Bundles starter

A minimal, working template for a Databricks data platform:

- **Asset Bundles** with `dev → staging → prod` promotion through GitHub Actions
- **PySpark unit tests** that run locally and in CI, no cluster needed
- **Terraform** for workspace entitlements and Unity Catalog grants
- **[docs/WHY.md](docs/WHY.md)**: the reasoning behind each choice

## Layout

```
databricks.yml                 bundle + the three targets
resources/daily_revenue.job.yml  the job (serverless, runs the wheel)
src/dab_starter/
  transforms.py                pure DataFrame logic (unit tested)
  main.py                      entry point: reads/writes tables
tests/                         pytest + local SparkSession
terraform/                     who can access the workspace and the data
  envs/{dev,staging,prod}.tfvars
.github/workflows/ci-cd.yml    test → deploy staging → (approve) → deploy prod
```

The example job reads `samples.tpch.orders` (in every workspace), removes bad rows, and writes
`<catalog>.<schema>.daily_revenue`.

## Getting started

1. **Fill in placeholders**: workspace hosts in `databricks.yml` and `terraform/envs/*.tfvars`,
   and the deployer service principal's application ID.
2. **Apply Terraform** once per workspace (a platform admin does this, not CI):
   ```sh
   cd terraform
   terraform init
   terraform apply -var-file=envs/prod.tfvars
   ```
3. **GitHub setup**: create environments `staging` and `prod`. Add secrets `DATABRICKS_CLIENT_ID` and
   `DATABRICKS_CLIENT_SECRET` (an OAuth secret for the deployer service principal) to each.
   Turn on **Required reviewers** for `prod`.
4. **Develop locally** (needs Java 17 for Spark):
   ```sh
   uv run pytest
   databricks auth login --host https://<dev-workspace-host>
   databricks bundle deploy            # target dev is the default
   databricks bundle run daily_revenue
   ```

## Flow

| Event | What happens |
|---|---|
| Pull request | unit tests, `terraform fmt`/`validate` |
| Merge to `main` | tests → deploy to **staging** → run the job as a smoke test |
| Approval in GitHub | the same commit is deployed to **prod** |
