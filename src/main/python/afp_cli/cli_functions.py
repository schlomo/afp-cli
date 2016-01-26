from __future__ import print_function, absolute_import, division

from datetime import datetime
import random
import socket
import sys

from .log import CMDLineExit
from .client import APICallError


def get_valid_seconds(aws_expiration_date, utcnow):
    try:
        credentials_valid_until = datetime.strptime(aws_expiration_date, "%Y-%m-%dT%H:%M:%SZ", )
        return (credentials_valid_until - utcnow).seconds
    except ValueError:
        default_seconds = 3600
        msg = "Failed to parse expiration date '{0}' for AWS credentials, assuming {1} seconds.".format(
            aws_expiration_date, default_seconds)
        print(msg, file=sys.stderr)
        return default_seconds


def get_default_afp_server():
    """Return the FQDN of the host that is called "afp"

    This is done by resolving "afp" into (potentially multiple) IPs.
    One of those IPs is randomly chosen, then a reverse-lookup is performed
    on that IP to get its FQDN.
    """
    try:
        addrinfos = socket.getaddrinfo("afp", 443,
                                       socket.AF_INET, socket.SOCK_STREAM)
    except Exception as exc:
        raise CMDLineExit("Could not resolve hostname 'afp': %s" % exc)
    addrinfo = random.choice(addrinfos)
    afp_server_ip = addrinfo[4][0]

    try:
        return socket.gethostbyaddr(afp_server_ip)[0]
    except Exception as exc:
        raise CMDLineExit("DNS reverse lookup failed for IP %s: %s" % (
            afp_server_ip, exc))


def get_first_role(federation_client, account):
    try:
        accounts_and_roles = federation_client.get_account_and_role_list()
        return sorted(accounts_and_roles[account])[0]
    except APICallError as exc:
        raise CMDLineExit("Failed to get account list from AWS: %s" % exc)
    except KeyError:
        raise CMDLineExit("%s is not a valid AWS account" % account)
    except IndexError:
        raise CMDLineExit("Could not find any role for account %s" % account)


def get_aws_credentials(federation_client, account, role):
    try:
        aws_credentials = federation_client.get_aws_credentials(account, role)
    except APICallError as exc:
        raise CMDLineExit("Failed to get credentials from AWS: %s" % exc)
    else:
        aws_credentials['AWS_VALID_SECONDS'] = get_valid_seconds(aws_credentials['AWS_EXPIRATION_DATE'],
                                                                 datetime.utcnow())
        aws_credentials['AWS_ACCOUNT_NAME'] = account
        aws_credentials['AWS_ASSUMED_ROLE'] = role
        return aws_credentials
