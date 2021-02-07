
from botocore.credentials import InstanceMetadataProvider, InstanceMetadataFetcher

provider = InstanceMetadataProvider(iam_role_fetcher=InstanceMetadataFetcher(timeout=1000, num_attempts=2))
creds = provider.load()

AWS_KEY_ID = creds.access_key
AWS_SECRET = creds.secret_key
AWS_SESSION = creds.token
Bucket="S3_bucket_name"



