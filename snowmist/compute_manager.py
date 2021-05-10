import logging
from com.vmware.nsx import model_client, fabric_client
from snowmist import compute_manager_thumbprint, ip_pool, transport_zone_controller

LOGGER = logging.getLogger(__name__)

def format_thumbprint(thumbprint):
  if not thumbprint:
    raise ValueError
  result = ""
  counter = 0
  for c in thumbprint.upper():
    if counter == 2:
      result += ":"
      counter = 0
    result += c
    counter += 1
  return result

def create_compute_manager(config, cm_hostname, cm_username, cm_password):
    if not config or not cm_hostname or not cm_username or not cm_password:
      raise ValueError
    cm: model_client.ComputeManager = None
    c: model_client.ComputeManager = None
    exists = False
    for c in fabric_client.ComputeManagers(config).list().results:
        if c.server == cm_hostname:
            LOGGER.info("Found existing compute manager {}[{}]".format(c.display_name, c.id))
            cm = c
    if not cm:
        cm_thumbprint = format_thumbprint(compute_manager_thumbprint.get_thumbprint(cm_hostname))
        credential = model_client.UsernamePasswordLoginCredential(password=cm_password, username=cm_username, thumbprint=cm_thumbprint)
        model_client.ComputeManager
        req = model_client.ComputeManager(server=cm_hostname, 
            credential=credential.convert_to(model_client.LoginCredential), origin_type="vCenter", display_name=cm_hostname)
        res: model_client.ComputeManager = fabric_client.ComputeManagers(config).create(req)
        LOGGER.info("Successfully created compute manager {} [{}]".format(req.display_name, req.id))

