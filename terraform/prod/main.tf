provider "aws" {
  region = "us-east-1"
  # region = data.terraform_remote_state.base.outputs.region
  allowed_account_ids = var.allowed_account_ids
}

terraform {
  backend "s3" {
    bucket = "evalai-terraform"
    key    = "evalai-prod/terraform.tfstate"
    region = "us-east-1"
    encrypt = true
  }
}

module "network" {
  source = "../modules/network"

  name = var.name
  cidr = var.cidr
  azs = var.azs
  public_subnets = var.public_subnets
}

module "alb" {
  source = "terraform-aws-modules/alb/aws"
}
