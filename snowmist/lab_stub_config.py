import requests
from vmware.vapi.lib import connect
from vmware.vapi.security.user_password import create_user_password_security_context
from vmware.vapi.stdlib.client.factories import StubConfigurationFactory

def get_stub_config(hostname, user, password):
    if not hostname or not user or not password:
        raise ValueError
    url = "https://{}/".format(hostname)
    session = requests.Session()
    session.verify = False
    requests.packages.urllib3.disable_warnings()
    connector = connect.get_requests_connector(
        session=session, msg_protocol='rest', url=url)
    security_context = create_user_password_security_context(
        user, password)
    connector.set_security_context(security_context)
    stub_config = StubConfigurationFactory.new_runtime_configuration(
        connector, response_extractor=True)
    return stub_config
