import argparse
import os
import logging
from snowmist import compute_manager_thumbprint, lab_stub_config, ip_pool, transport_zone_controller, compute_manager, transport_node_controller, networking

LOGGER = logging.getLogger(__name__)

LAB_NAME_KEY = "SNOWMIST_LAB_NAME"
LAB_NSX_USERNAME_KEY = "SNOWMIST_LAB_NSX_USERNAME"
LAB_NSX_PASSWORD_KEY = "SNOWMIST_LAB_NSX_PASSWORD"
LAB_NSX_HOSTNAME_KEY = "SNOWMIST_LAB_NSX_HOSTNAME"
LAB_NSX_HOSTNAME_LAB_NAME_TEMPLATE_KEY = "SNOWMIST_LAB_NSX_HOSTNAME_LAB_NAME_TEMPLATE"
LAB_VC_USERNAME_KEY = "SNOWMIST_LAB_VC_USERNAME"
LAB_VC_PASSWORD_KEY = "SNOWMIST_LAB_VC_PASSWORD"
LAB_VC_HOSTNAME_KEY = "SNOWMIST_LAB_VC_HOSTNAME"
LAB_VC_HOSTNAME_LAB_NAME_TEMPLATE_KEY = "SNOWMIST_LAB_VC_HOSTNAME_LAB_NAME_TEMPLATE"

def run():
    return App()

class App(object):
    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')
        parser = argparse.ArgumentParser()
        parser.add_argument("--lab-name", type=str)
        parser.add_argument("--lab-nsx-username", type=str)
        parser.add_argument("--lab-nsx-password", type=str)
        parser.add_argument("--lab-nsx-hostname", type=str)
        parser.add_argument("--lab-nsx-hostname-lab-name-template", type=str)
        parser.add_argument("--lab-vc-username", type=str)
        parser.add_argument("--lab-vc-password", type=str)
        parser.add_argument("--lab-vc-hostname", type=str)
        parser.add_argument("--lab-vc-hostname-lab-name-template", type=str)
        args = parser.parse_args()
        lab_name = args.lab_name
        if not lab_name:
            lab_name = os.environ[LAB_NAME_KEY]
        lab_nsx_username = args.lab_nsx_username
        if not lab_nsx_username:
            lab_nsx_username = os.environ[LAB_NSX_USERNAME_KEY]
        lab_nsx_password = args.lab_nsx_password
        if not lab_nsx_password:
            lab_nsx_password = os.environ[LAB_NSX_PASSWORD_KEY]
        lab_nsx_hostname = args.lab_nsx_hostname
        if not lab_nsx_hostname:
            lab_nsx_hostname = os.environ.get(LAB_NSX_HOSTNAME_KEY)
        # If nsx hostname is not specified, use template.
        if not lab_nsx_hostname:
            lab_nsx_hostname_lab_name_temmplate = args.lab_nsx_hostname_lab_name_template
            if not lab_nsx_hostname_lab_name_temmplate:
                lab_nsx_hostname_lab_name_temmplate = os.environ.get(LAB_NSX_HOSTNAME_LAB_NAME_TEMPLATE_KEY)
            if lab_nsx_hostname_lab_name_temmplate:
                lab_nsx_hostname = lab_nsx_hostname_lab_name_temmplate.format(lab_name)
        if not lab_nsx_hostname:
            raise ValueError
        lab_vc_username = args.lab_vc_username
        if not lab_vc_username:
            lab_vc_username = os.environ[LAB_VC_USERNAME_KEY]
        lab_vc_password = args.lab_vc_password
        if not lab_vc_password:
            lab_vc_password = os.environ[LAB_VC_PASSWORD_KEY]
        lab_vc_hostname = args.lab_vc_hostname
        if not lab_vc_hostname:
            lab_vc_hostname = os.environ.get(LAB_VC_HOSTNAME_KEY)
        # If vc hostname is not specified, use template.
        if not lab_vc_hostname:
            lab_vc_hostname_lab_name_temmplate = args.lab_vc_hostname_lab_name_template
            if not lab_vc_hostname_lab_name_temmplate:
                lab_vc_hostname_lab_name_temmplate = os.environ.get(LAB_VC_HOSTNAME_LAB_NAME_TEMPLATE_KEY)
            if lab_vc_hostname_lab_name_temmplate:
                lab_vc_hostname = lab_vc_hostname_lab_name_temmplate.format(lab_name)
        if not lab_vc_hostname:
            raise ValueError

        config = lab_stub_config.get_stub_config(lab_nsx_hostname, lab_nsx_username, lab_nsx_password)
        compute_manager.create_compute_manager(config, lab_vc_hostname, lab_vc_username, lab_vc_password)
        ip_pool.create(config, lab_name)
        tzc = transport_zone_controller.TransportZoneContoller(config, lab_name)
        tnc = transport_node_controller.TransportNodeController(config, lab_name, tzc)
        networking.create(config, lab_name, default_transport_node_controller=tnc, default_transport_zone_controller=tzc)

        super().__init__()
        