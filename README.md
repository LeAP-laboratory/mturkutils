All scripts assume that your AWS credentials are in ~/.aws/credentials or ~/.aws/config

    [default]
    aws_access_key_id = <your access key>
    aws_secret_access_key = <your secret key>

or /etc/boto.cfg or ~/.boto files:

    [Credentials]
    aws_access_key_id = <your access key>
    aws_secret_access_key = <your secret key>

See [boto configuration](http://boto3.readthedocs.org/en/latest/guide/configuration.html) for how to set up credential files.

## External Dependencies
 * [unicodecsv](https://pypi.python.org/pypi/unicodecsv)
 * [PyYAML](https://pypi.python.org/pypi/PyYAML)
