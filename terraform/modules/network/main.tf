module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "v2.39.0"

  name = "${var.name}-vpc"
  azs = var.azs
  cidr = var.cidr
  public_subnets = var.public_subnets
}
