output "vpc_id" {
  description = "The ID of EvalAI VPC"
  value       = "${module.network.vpc_id}"
}
