import ipaddress
from com.vmware.nsx_policy.infra import tier_0s_client,tier_1s_client
from com.vmware import nsx_policy_client
from com.vmware.nsx_policy import infra_client
from com.vmware.nsx_policy.infra import tier_0s_client
from com.vmware.nsx_policy.infra.tier_0s import locale_services_client
from com.vmware.nsx_policy import model_client
from com.vmware.nsx_policy.infra import ip_pools_client
from com.vmware.nsx_policy.infra import sites_client
from com.vmware.nsx_policy.infra.sites import enforcement_points_client
from com.vmware.nsx_policy.infra.sites.enforcement_points import edge_clusters_client
from snowmist import transport_zone_controller, transport_node_controller, provider_network

DEFAULT_SITE_NAME = "default"
DEFAULT_ENFORCEMENT_POINT_NAME = "default"
DEFAULT_LOCALE_SERVICE_NAME = "default"
UPLINK1_NAME = "Uplink1"
UPLINK2_NAME = "Uplink2"

def create(config, lab_name, default_transport_zone_controller, default_transport_node_controller):
    site: model_client.Site = infra_client.Sites(config).get(DEFAULT_SITE_NAME)
    ep: model_client.EnforcementPoint = sites_client.EnforcementPoints(config).get(site.id, DEFAULT_ENFORCEMENT_POINT_NAME)

    # Create uplink segments
    uplink1_tz: model_client.PolicyTransportZone = enforcement_points_client.TransportZones(config).get(site.id, ep.id, default_transport_zone_controller.uplink1_tz.id)
    uplink1_segment_req = model_client.Segment(display_name=UPLINK1_NAME, vlan_ids=["0"], transport_zone_path=uplink1_tz.path)
    infra_client.Segments(config).patch(UPLINK1_NAME, uplink1_segment_req)
    uplink1_segment = infra_client.Segments(config).get(UPLINK1_NAME)
    uplink2_tz: model_client.PolicyTransportZone = enforcement_points_client.TransportZones(config).get(site.id, ep.id, default_transport_zone_controller.uplink2_tz.id)
    uplink2_segment_req = model_client.Segment(display_name=UPLINK2_NAME, vlan_ids=["0"], transport_zone_path=uplink2_tz.path)
    infra_client.Segments(config).patch(UPLINK2_NAME, uplink2_segment_req)
    uplink2_segment = infra_client.Segments(config).get(UPLINK2_NAME)
    
    # Create T0 Gateway
    tier0_gateway_name = "Gateway"
    tier0_gateway_req = model_client.Tier0(id=tier0_gateway_name, ha_mode=model_client.Tier0.HA_MODE_STANDBY)
    infra_client.Tier0s(config).patch(tier0_gateway_name, tier0_gateway_req)

    # Create locale service for T0
    edge_cluster: model_client.PolicyEdgeCluster = enforcement_points_client.EdgeClusters(config).get(site.id, ep.id, default_transport_node_controller.edge_cluster.id)
    tier0_locale_service_req: model_client.LocaleServices = model_client.LocaleServices(id=DEFAULT_LOCALE_SERVICE_NAME, edge_cluster_path=edge_cluster.path)
    tier_0s_client.LocaleServices(config).patch(tier0_gateway_req.id, DEFAULT_LOCALE_SERVICE_NAME, tier0_locale_service_req)

    # Create uplink interface on T0
    edge_cluster_nodes: list(model_client.PolicyEdgeNode) = edge_clusters_client.EdgeNodes(config).list(site.id, ep.id, edge_cluster.id).results    

    uplink_pairs = [
        (provider_network.SUBNET_TYPE_UPLINK1, uplink1_segment),
        (provider_network.SUBNET_TYPE_UPLINK2, uplink2_segment),
    ]
    ha_vip_configs:list(model_client.Tier0HaVipConfig) = []
    for uplink_pair in uplink_pairs:
        provider_network_subnet_type = uplink_pair[0]
        uplink_segment: model_client.Segment = uplink_pair[1]

        subnet_text = provider_network.get_subnet_text(lab_name, provider_network_subnet_type)
        uplink_base_ip_interface = ipaddress.IPv4Interface(subnet_text)
        uplink_interface_reqs = []
        for i in range(len(edge_cluster_nodes)):
            edge_node: model_client.PolicyEdgeNode = edge_cluster_nodes[i]
            # index starts at 1
            node_index = i + 1
            uplink_ip_interface = uplink_base_ip_interface + 10 + node_index
            uplink_interface_req: model_client.Tier0Interface = model_client.Tier0Interface(
                id="{}-{}".format(edge_node.display_name, provider_network_subnet_type.lower()),
                subnets=[model_client.InterfaceSubnet(ip_addresses=[str(uplink_ip_interface.ip)], prefix_len=uplink_base_ip_interface.network.prefixlen)],
                segment_path=uplink_segment.path, edge_path=edge_node.path,
            )
            locale_services_client.Interfaces(config).patch(tier0_gateway_req.id, tier0_locale_service_req.id, uplink_interface_req.id, uplink_interface_req)
            uplink_interface_reqs.append(uplink_interface_req)
            
        # Create default route.
        # Currently, add default route on uplink1 only.
        if provider_network_subnet_type == provider_network.SUBNET_TYPE_UPLINK1:
            next_hop_interface = uplink_base_ip_interface + 1
            default_route_req: model_client.StaticRoutes = model_client.StaticRoutes(id=provider_network_subnet_type.lower(), network="0.0.0.0/0", 
                next_hops=[model_client.RouterNexthop(ip_address=str(next_hop_interface.ip))])
            tier_0s_client.StaticRoutes(config).patch(tier0_gateway_req.id, default_route_req.id, default_route_req)
    
        # Create vip interface on T0
        vip_interface = uplink_base_ip_interface + 10
        external_interface_paths = []
        for lsi in locale_services_client.Interfaces(config).list(tier0_gateway_req.id, tier0_locale_service_req.id).results:
            lsi: model_client.Tier0Interface
            if lsi.segment_path != uplink_segment.path:
                continue
            external_interface_paths.append(lsi.path)
        ha_vip_config: model_client.Tier0HaVipConfig = model_client.Tier0HaVipConfig(
            enabled=True, external_interface_paths=external_interface_paths,
            vip_subnets=[model_client.InterfaceSubnet(ip_addresses=[str(vip_interface.ip)], prefix_len=uplink_base_ip_interface.network.prefixlen)])
        ha_vip_configs.append(ha_vip_config)
    tier0_locale_service_req.ha_vip_configs = ha_vip_configs
    tier_0s_client.LocaleServices(config).patch(tier0_gateway_req.id, tier0_locale_service_req.id, tier0_locale_service_req)

    # Create DHCP
    dhcp_server_config_req = model_client.DhcpServerConfig(id="default", server_address="192.168.250.201/24")
    infra_client.DhcpServerConfigs(config).patch(dhcp_server_config_req.id, dhcp_server_config_req)
    dhcp_server_config: model_client.DhcpServerConfig = infra_client.DhcpServerConfigs(config).get(dhcp_server_config_req.id)
    
    # Create T1
    tier0: model_client.Tier0 = infra_client.Tier0s(config).get(tier0_gateway_name)
    s = {
        "Tenant1":{
            "Red": "192.168.101.0/24",
            "Blue": "192.168.102.0/24",
        },
        "Tenant2":{
            "Green": "192.168.103.0/24",
            "Yellow": "192.168.104.0/24",
        },
    }
    overlay_tz: model_client.PolicyTransportZone = enforcement_points_client.TransportZones(config).get(site.id, ep.id, default_transport_zone_controller.overlay_tz.id)
    for tier1_name,segments in s.items():
        tier1_req = model_client.Tier1(id=tier1_name, tier0_path=tier0.path, dhcp_config_paths=[dhcp_server_config.path], 
        route_advertisement_types=[
            model_client.Tier1.ROUTE_ADVERTISEMENT_TYPES_IPSEC_LOCAL_ENDPOINT,
            model_client.Tier1.ROUTE_ADVERTISEMENT_TYPES_CONNECTED,
            model_client.Tier1.ROUTE_ADVERTISEMENT_TYPES_STATIC_ROUTES,
            model_client.Tier1.ROUTE_ADVERTISEMENT_TYPES_NAT,
            model_client.Tier1.ROUTE_ADVERTISEMENT_TYPES_LB_VIP,
        ])
        infra_client.Tier1s(config).patch(tier1_req.id, tier1_req)
        tier1_locale_service_req = model_client.LocaleServices(id=DEFAULT_LOCALE_SERVICE_NAME, edge_cluster_path=edge_cluster.path)
        tier_1s_client.LocaleServices(config).patch(tier1_req.id, tier1_locale_service_req.id, tier1_locale_service_req)
        
        tier1 = infra_client.Tier1s(config).get(tier1_req.id)
        for segment_name, segment_config in segments.items():
            tenant_subnet = ipaddress.IPv4Network(segment_config)
            tenant_gateway_interface = ipaddress.IPv4Interface("{}/{}".format(tenant_subnet.network_address+1, tenant_subnet.prefixlen))
            tenant_dhcp_start = ipaddress.IPv4Network(segment_config).network_address + 101
            tenant_dhcp_end = ipaddress.IPv4Network(segment_config).network_address + 180
            dhcp_ranges = ["{}-{}".format(str(tenant_dhcp_start), str(tenant_dhcp_end))]
            segment_req = model_client.Segment(id=segment_name, transport_zone_path=overlay_tz.path, connectivity_path=tier1.path,
            subnets=[model_client.SegmentSubnet(dhcp_config=model_client.SegmentDhcpV4Config(dns_servers=["192.168.0.251","192.168.0.252"]), dhcp_ranges=dhcp_ranges,
            gateway_address=str(tenant_gateway_interface), network=str(tenant_subnet))])
            infra_client.Segments(config).patch(segment_req.id, segment_req)

            
