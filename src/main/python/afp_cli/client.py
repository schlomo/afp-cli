# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, division

import requests
import json
from requests.auth import HTTPBasicAuth


class APICallError(Exception):
    pass


class AWSFederationClientCmd(object):
    """Class for a command line client which uses the afp api"""

    def __init__(self, *args, **kwargs):
        self.username = kwargs.get('username', None)
        self._password = kwargs.get('password', None)
        self.api_url = kwargs.get('api_url', None)
        self.ssl_verify = kwargs.get('ssl_verify', True)

    def call_api(self, url_suffix):
        """Send a request to the aws federation proxy"""
        # TODO: Automatic versioning instead of the static below
        headers = {'User-Agent': 'afp-cli/1.0.6'}
        api_result = requests.get('{0}{1}'.format(self.api_url, url_suffix),
                                  headers=headers,
                                  verify=self.ssl_verify,
                                  auth=HTTPBasicAuth(self.username,
                                                     self._password))
        if api_result.status_code != 200:
            if api_result.status_code == 401:
                # Need to treat 401 specially since it is directly send from webserver and body has different format.
                raise APICallError("API call to AWS (%s/%s) failed: %s %s" % (
                    self.api_url, url_suffix, api_result.status_code, api_result.reason))
            else:
                raise APICallError("API call to AWS (%s/%s) failed: %s" % (
                    self.api_url, url_suffix, api_result.json()['message']))
        return api_result.text

    def get_account_and_role_list(self):
        """Create an aws federation proxy request and return the result"""
        accounts_and_roles = self.call_api("/account")
        return json.loads(accounts_and_roles)

    def get_aws_credentials(self, account, role):
        """Return AWS credentials for a specified user and account"""
        aws_credentials = self.call_api("/account/{0}/{1}".format(account,
                                                                  role))
        aws_credentials = json.loads(aws_credentials)
        return {'AWS_ACCESS_KEY_ID': aws_credentials['AccessKeyId'],
                'AWS_SECRET_ACCESS_KEY': aws_credentials['SecretAccessKey'],
                'AWS_SESSION_TOKEN': aws_credentials['Token'],
                'AWS_SECURITY_TOKEN': aws_credentials['Token'],
                'AWS_EXPIRATION_DATE': aws_credentials['Expiration']}
