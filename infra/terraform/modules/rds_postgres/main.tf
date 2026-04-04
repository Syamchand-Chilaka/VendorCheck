variable "project" {
  type        = string
  description = "Project name prefix for resource naming"
}

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"
}

variable "db_name" {
  type    = string
  default = "vendorcheck"
}

variable "db_username" {
  type    = string
  default = "vendorcheck"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "allocated_storage" {
  type    = number
  default = 20
}

variable "vpc_security_group_ids" {
  type        = list(string)
  description = "Security group IDs for the RDS instance"
  default     = []
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnet IDs for the DB subnet group (optional for default VPC)"
  default     = []
}

resource "aws_db_subnet_group" "main" {
  count      = length(var.subnet_ids) > 0 ? 1 : 0
  name       = "${var.project}-${var.environment}"
  subnet_ids = var.subnet_ids

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

resource "aws_db_instance" "main" {
  identifier = "${var.project}-${var.environment}"

  engine         = "postgres"
  engine_version = "16.4"
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.allocated_storage * 2
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = length(var.subnet_ids) > 0 ? aws_db_subnet_group.main[0].name : null
  vpc_security_group_ids = var.vpc_security_group_ids
  publicly_accessible    = var.environment == "dev" ? true : false

  multi_az            = false
  skip_final_snapshot = var.environment == "dev" ? true : false
  deletion_protection = var.environment == "dev" ? false : true

  backup_retention_period = var.environment == "dev" ? 1 : 7

  parameter_group_name = aws_db_parameter_group.main.name

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

resource "aws_db_parameter_group" "main" {
  name   = "${var.project}-${var.environment}-pg16"
  family = "postgres16"

  # Enable RLS-related settings
  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}
