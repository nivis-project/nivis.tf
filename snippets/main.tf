provider "aws" {
  region = "eu-central-1"
}

resource "aws_s3_bucket" "demo" {
  force_destroy = true
}
