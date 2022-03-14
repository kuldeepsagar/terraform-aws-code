terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      #version = "~> 3.45.0"
    }
  }

  #required_version = ">= 0.13.0"
}

provider "aws" {
  #profile = "kyniac"
  region  = "us-east-2"
}
