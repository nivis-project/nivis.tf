providers.aws = lib.mkProvider {
  source = "registry.opentofu.org/hashicorp/aws";
  config.region = "eu-central-1";
};
