{
  inputs.nivis.url = "github:nivis-project/nivis";
  outputs = { self, nivis }:
    let lib = nivis.lib; in {
      nivis.plan = ledger: lib.toIR {
        providers.aws = lib.mkProvider {
          source = "registry.opentofu.org/hashicorp/aws";
          config.region = "eu-central-1";
        };
        resources = [
          (lib.mkResource {
            provider = "aws"; type = "aws_s3_bucket"; name = "demo";
            config.force_destroy = true;
          })
        ];
        inherit ledger;
      };
    };
}
