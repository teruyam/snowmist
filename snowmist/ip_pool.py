import ipaddress
from com.vmware.nsx_policy.infra import tier_0s_client,tier_1s_client
from com.vmware import nsx_policy_client
from com.vmware.nsx_policy import infra_client
from com.vmware.nsx_policy import model_client
from com.vmware.nsx_policy.infra import ip_pools_client
from snowmist import provider_network

EDGE_TEP_IP_POOL_ID = "Edge-TEP-IP-Pool"
EDGE_TEP_IP_POOL_DISPLAY_NAME = "Edge TEP IP Pool"
EDGE_TEP_IP_POOL_SUBNET_ID = "Edge-TEP-IP-Pool-Subnet"
HOST_TEP_IP_POOL_ID = "Host-TEP-IP-Pool"
HOST_TEP_IP_POOL_DISPLAY_NAME = "Host TEP IP Pool"
HOST_TEP_IP_POOL_SUBNET_ID = "Host-TEP-IP-Pool-Subnet"

def create(config, lab_name):
    if not config or not lab_name:
        raise ValueError
    source = {
        provider_network.SUBNET_TYPE_HOST: {"pool_id": HOST_TEP_IP_POOL_ID, "pool_display_name": HOST_TEP_IP_POOL_DISPLAY_NAME, "subnet_id": HOST_TEP_IP_POOL_SUBNET_ID},
        provider_network.SUBNET_TYPE_EDGE: {"pool_id": EDGE_TEP_IP_POOL_ID, "pool_display_name": EDGE_TEP_IP_POOL_DISPLAY_NAME, "subnet_id": EDGE_TEP_IP_POOL_SUBNET_ID},
    }
    for k,v in source.items():
        subnet_text = provider_network.get_subnet_text(lab_name, k)
        pool_id = v.get("pool_id")
        pool_display_name = v.get("pool_display_name")
        subnet_id = v.get("subnet_id")
        if not subnet_text or not pool_id or not pool_display_name or not subnet_id:
            raise ValueError
        create_ip_pool_from_subnet(config=config, lab_name=lab_name, cidr=subnet_text, 
            ip_pool_id=pool_id, ip_pool_display_name=pool_display_name, ip_subnet_id=subnet_id)

def create_ip_pool_from_subnet(config, lab_name, cidr, ip_pool_id, ip_pool_display_name, ip_subnet_id):
    if not config or not cidr or not ip_pool_id or not ip_pool_display_name or not ip_subnet_id:
        raise ValueError
    subnet = ipaddress.IPv4Network(cidr)
    start_ip_address = str(subnet.network_address + 11)
    end_ip_address = str(subnet.network_address + 240)
    gateway_ip_address = str(subnet.network_address + 1)
    create_ip_pool(config=config, ip_pool_id=ip_pool_id, ip_pool_display_name=ip_pool_display_name, 
        ip_subnet_id=ip_subnet_id, cidr=cidr, start=start_ip_address, 
        end=end_ip_address, gateway_ip=gateway_ip_address)

def create_ip_pool(config, ip_pool_id, ip_pool_display_name, ip_subnet_id, cidr, start, end, gateway_ip):
    if not config or not ip_pool_id or not ip_pool_display_name or not ip_subnet_id or not start or not end or not gateway_ip:
        raise ValueError
    edge_ip_pool = model_client.IpAddressPool(display_name=ip_pool_display_name, id=ip_pool_id)
    infra_client.IpPools(config).patch(ip_pool_id, edge_ip_pool)
    static_subnet = model_client.IpAddressPoolStaticSubnet(allocation_ranges=[model_client.IpPoolRange(start=start, end=end)], cidr=cidr, gateway_ip=gateway_ip)
    ip_pools_client.IpSubnets(config).patch(ip_pool_id, ip_subnet_id, static_subnet)
