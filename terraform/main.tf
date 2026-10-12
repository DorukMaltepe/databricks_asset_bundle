terraform {
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.70"
    }
  }
  # Use one remote state per environment, e.g.
  # terraform init -backend-config=envs/prod.backend.hcl
  # backend "s3" {}
}

provider "databricks" {
  host = var.workspace_host
}

variable "workspace_host" {
  type = string
}

variable "catalog" {
  type        = string
  description = "Unity Catalog catalog for this environment."
}

variable "engineers_group" {
  type        = string
  default     = "data-engineers"
  description = "Account-level group (usually synced from your IdP)."
}

variable "deployer_sp_application_id" {
  type        = string
  description = "Application ID of the service principal GitHub Actions deploys as."
}

variable "engineers_can_write" {
  type        = bool
  description = "true only in dev: engineers write in dev, read in staging/prod."
}

locals {
  read  = ["USE_CATALOG", "USE_SCHEMA", "SELECT"]
  write = concat(local.read, ["CREATE_SCHEMA", "CREATE_TABLE", "MODIFY"])
}

data "databricks_group" "engineers" {
  display_name = var.engineers_group
}

resource "databricks_entitlements" "engineers" {
  group_id              = data.databricks_group.engineers.id
  workspace_access      = true
  databricks_sql_access = true
}

# Authoritative: any grant on this catalog not listed here is removed on apply.
resource "databricks_grants" "catalog" {
  catalog = var.catalog

  grant {
    principal  = var.engineers_group
    privileges = var.engineers_can_write ? local.write : local.read
  }

  grant {
    principal  = var.deployer_sp_application_id
    privileges = local.write
  }
}
