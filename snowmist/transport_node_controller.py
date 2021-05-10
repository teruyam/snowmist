import logging
from com.vmware import nsx_client
from com.vmware.nsx import model_client, fabric_client, pools_client
from snowmist import transport_zone_controller, ip_pool, host_switch_profile, node_version

LOGGER = logging.getLogger(__name__)

TRANSPORT_NODE_PROFILE_NAME = "Default Transport Node Profile"
DEFAULT_EDGE_CLUSTER_NAME = "edges"

class TransportNodeController(object):
    def __init__(self, config, lab_name, transport_zone_controller):
        if not config:
            raise ValueError("invalid config")
        self.config = config
        if not lab_name:
            raise ValueError("invalid lab_name")
        self.lab_name = lab_name
        if not transport_zone_controller:
            raise ValueError("invalid transport zone controller")
        self.transport_zone_controller = transport_zone_controller
        self.edge_cluster: model_client.EdgeCluster
        self.apply()
        super().__init__()

    def apply(self):
        config = self.config
        lab_name = self.lab_name

        tz_controller = transport_zone_controller.TransportZoneContoller(config, lab_name)
        tz: model_client.TransportNodeProfile
        p: model_client.TransportNodeProfile
        for p in nsx_client.TransportNodeProfiles(config).list().results:
            if p.display_name == TRANSPORT_NODE_PROFILE_NAME:
                tz = p
        host_tep_ip_pool: model_client.IpPool
        edge_tep_ip_pool: model_client.IpPool
        i: model_client.IpPool
        for i in pools_client.IpPools(config).list().results:
            if i.display_name == ip_pool.HOST_TEP_IP_POOL_DISPLAY_NAME:
                host_tep_ip_pool = i
            if i.display_name == ip_pool.EDGE_TEP_IP_POOL_DISPLAY_NAME:
                edge_tep_ip_pool = i
        if not host_tep_ip_pool or not edge_tep_ip_pool:
            raise ValueError

        edge_uplink_profile_id = host_switch_profile.get_uplink_profile_id(config, host_switch_profile.NSX_EDGE_SINGLE_NIC_UPLINK_PROFILE)
        if not edge_uplink_profile_id:
            raise ValueError
        
        lldp_profile_id = host_switch_profile.get_lldp_profile_id(config)
        if not lldp_profile_id:
            raise ValueError

        # Configure unprepared edges
        edge_transport_nodes = nsx_client.TransportNodes(config).list(node_types=fabric_client.Nodes.LIST_RESOURCE_TYPE_EDGENODE).results
        edge_transport_node: model_client.TransportNodeProfile
        for edge_transport_node in edge_transport_nodes:
            if edge_transport_node.host_switch_spec and edge_transport_node.transport_zone_endpoints:
                LOGGER.info("edge {} has been already configured".format(edge_transport_node.id))
                continue
            spec = model_client.StandardHostSwitchSpec(
                host_switches=[
                    model_client.StandardHostSwitch(
                        host_switch_name=transport_zone_controller.HOST_SWITCH_NAME,
                        host_switch_profile_ids=[
                            model_client.HostSwitchProfileTypeIdEntry(model_client.HostSwitchProfileTypeIdEntry.KEY_UPLINKHOSTSWITCHPROFILE, edge_uplink_profile_id),
                            model_client.HostSwitchProfileTypeIdEntry(model_client.HostSwitchProfileTypeIdEntry.KEY_LLDPHOSTSWITCHPROFILE, lldp_profile_id)
                        ],
                        pnics=[model_client.Pnic(device_name="fp-eth0", uplink_name="uplink-1")],
                        is_migrate_pnics=False,
                        ip_assignment_spec=model_client.StaticIpPoolSpec(ip_pool_id=edge_tep_ip_pool.id)
                    ),
                    model_client.StandardHostSwitch(
                        host_switch_name=transport_zone_controller.EDGE_UPLINK1_SWITCH_NAME,
                        host_switch_profile_ids=[
                            model_client.HostSwitchProfileTypeIdEntry(model_client.HostSwitchProfileTypeIdEntry.KEY_UPLINKHOSTSWITCHPROFILE, edge_uplink_profile_id),
                            model_client.HostSwitchProfileTypeIdEntry(model_client.HostSwitchProfileTypeIdEntry.KEY_LLDPHOSTSWITCHPROFILE, lldp_profile_id)
                        ],
                        pnics=[model_client.Pnic(device_name="fp-eth1", uplink_name="uplink-1")],
                        is_migrate_pnics=False,
                        ip_assignment_spec=model_client.AssignedByDhcp(),
                    ),
                    model_client.StandardHostSwitch(
                        host_switch_name=transport_zone_controller.EDGE_UPLINK2_SWITCH_NAME,
                        host_switch_profile_ids=[
                            model_client.HostSwitchProfileTypeIdEntry(model_client.HostSwitchProfileTypeIdEntry.KEY_UPLINKHOSTSWITCHPROFILE, edge_uplink_profile_id),
                            model_client.HostSwitchProfileTypeIdEntry(model_client.HostSwitchProfileTypeIdEntry.KEY_LLDPHOSTSWITCHPROFILE, lldp_profile_id)
                        ],
                        pnics=[model_client.Pnic(device_name="fp-eth2", uplink_name="uplink-1")],
                        is_migrate_pnics=False,
                        ip_assignment_spec=model_client.AssignedByDhcp(),
                    )
                ],
            )
            edge_transport_node.host_switch_spec = spec
            bfd_profile_id = transport_zone_controller.get_bfd_health_monitoring_profile_id(config)
            nsx_client.SwitchingProfiles(config).list(switching_profile_type=bfd_profile_id)
            edge_transport_node.transport_zone_endpoints = [
                model_client.TransportZoneEndPoint(
                    transport_zone_id=tz.id,
                    transport_zone_profile_ids=[model_client.TransportZoneProfileTypeIdEntry(
                    profile_id=bfd_profile_id,
                    resource_type=model_client.TransportZoneProfileTypeIdEntry.RESOURCE_TYPE_BFDHEALTHMONITORINGPROFILE)]) for tz 
                                    in [tz_controller.overlay_tz, tz_controller.vlan_tz, tz_controller.uplink1_tz, tz_controller.uplink2_tz]]
            # product_version: str = node_version.get_product_version(lab_name)
            #if product_version.startswith("2."):
            #    LOGGER.info("product version {} is less than 3.0. adding transport zone endpoint.".format(product_version))
            #    bfd_profile_id = transport_zone_controller.get_bfd_health_monitoring_profile_id(config)
            #    nsx_client.SwitchingProfiles(config).list(switching_profile_type=bfd_profile_id)
            #    edge_transport_node.transport_zone_endpoints = [
            #        model_client.TransportZoneEndPoint(
            #            transport_zone_id=tz.id,
            #            transport_zone_profile_ids=[model_client.TransportZoneProfileTypeIdEntry(
            #            profile_id=bfd_profile_id,
            #            resource_type=model_client.TransportZoneProfileTypeIdEntry.RESOURCE_TYPE_BFDHEALTHMONITORINGPROFILE)]) for tz 
            #                            in [tz_controller.overlay_tz, tz_controller.vlan_tz, tz_controller.uplink1_tz, tz_controller.uplink2_tz]]
            LOGGER.info("updating edge {}".format(edge_transport_node.id))
            nsx_client.TransportNodes(config).update(edge_transport_node.id, edge_transport_node)

        # Create edge cluster
        edge_clusters = nsx_client.EdgeClusters(config).list().results
        edge_cluster: model_client.EdgeCluster
        default_edge_cluster: model_client.EdgeCluster = None
        for edge_cluster in edge_clusters:
            if edge_cluster.display_name == DEFAULT_EDGE_CLUSTER_NAME:
                default_edge_cluster: model_client.EdgeCluster = edge_cluster
                break
        profiles = nsx_client.ClusterProfiles(config).list(resource_type=nsx_client.ClusterProfiles.LIST_RESOURCE_TYPE_EDGEHIGHAVAILABILITYPROFILE).results
        nsx_default_edge_high_availability_profile_name = "nsx-default-edge-high-availability-profile"
        nsx_default_edge_high_availability_profile: model_client.EdgeHighAvailabilityProfile = None
        for p in profiles:
            edge_high_availability_profile: model_client.EdgeHighAvailabilityProfile = p.convert_to(model_client.EdgeHighAvailabilityProfile)
            if edge_high_availability_profile.display_name == nsx_default_edge_high_availability_profile_name:
                nsx_default_edge_high_availability_profile = edge_high_availability_profile
                break
        edge_transport_node_ids = []
        for i in edge_transport_nodes:
            i: model_client.TransportNodeProfile
            edge_transport_node_ids.append(i.id)
        # add all edges into single edge cluster
        edge_cluster_req: model_client.EdgeCluster = model_client.EdgeCluster(
            display_name=DEFAULT_EDGE_CLUSTER_NAME,
            cluster_profile_bindings= [model_client.ClusterProfileTypeIdEntry(
                profile_id=nsx_default_edge_high_availability_profile.id,
                resource_type=nsx_client.ClusterProfiles.LIST_RESOURCE_TYPE_EDGEHIGHAVAILABILITYPROFILE,
                )],
            members=[model_client.EdgeClusterMember(transport_node_id=x) for x in edge_transport_node_ids],
        )
        if not default_edge_cluster:
            default_edge_cluster: model_client.EdgeCluster = nsx_client.EdgeClusters(config).create(edge_cluster_req)
        else:
            edge_cluster_req.revision = default_edge_cluster.revision
            default_edge_cluster: model_client.EdgeCluster = nsx_client.EdgeClusters(config).update(default_edge_cluster.id, edge_cluster_req)
        self.edge_cluster = default_edge_cluster

        transport_node_profiles = nsx_client.TransportNodeProfiles(config).list().results
        default_transport_node_profile: model_client.TransportNodeProfile = None
        tns: model_client.TransportNodeProfile
        for tns in transport_node_profiles:
            if tns.display_name == TRANSPORT_NODE_PROFILE_NAME:
                default_transport_node_profile = tns
                break
        if not default_transport_node_profile:
            host_uplink_profile_id = host_switch_profile.get_uplink_profile_id(config, host_switch_profile.NSX_DEFAULT_UPLINK_HOST_SWITCH_PROFILE)
            host_nioc_profile_id = host_switch_profile.get_nioc_profile_id(config)
            p = model_client.TransportNodeProfile(display_name=TRANSPORT_NODE_PROFILE_NAME, 
                    description="Transport Node Profile", 
                    host_switch_spec=model_client.StandardHostSwitchSpec(
                        host_switches=[
                            model_client.StandardHostSwitch(
                                host_switch_name=transport_zone_controller.HOST_SWITCH_NAME,
                                host_switch_profile_ids=[
                                    model_client.HostSwitchProfileTypeIdEntry(model_client.HostSwitchProfileTypeIdEntry.KEY_UPLINKHOSTSWITCHPROFILE, host_uplink_profile_id),
                                    model_client.HostSwitchProfileTypeIdEntry(model_client.HostSwitchProfileTypeIdEntry.KEY_NIOCPROFILE, host_nioc_profile_id),
                                    model_client.HostSwitchProfileTypeIdEntry(model_client.HostSwitchProfileTypeIdEntry.KEY_LLDPHOSTSWITCHPROFILE, lldp_profile_id)
                                ],
                                pnics=[model_client.Pnic(device_name="vmnic1", uplink_name="uplink-1")],
                                is_migrate_pnics=False,
                                ip_assignment_spec=model_client.StaticIpPoolSpec(ip_pool_id=host_tep_ip_pool.id)
                    ),
                ]))    
            # product_version: str = node_version.get_product_version(config, lab_name)
            #if product_version.startswith("2."):
            #    LOGGER.info("product version {} is less than 3.0. adding transport zone endpoint to transport node profile.".format(product_version))
            #    p.transport_zone_endpoints = [model_client.TransportZoneEndPoint(tz.id) for tz in [tz_controller.overlay_tz, tz_controller.vlan_tz]]
            p.transport_zone_endpoints = [model_client.TransportZoneEndPoint(tz.id) for tz in [tz_controller.overlay_tz, tz_controller.vlan_tz]]
            default_transport_node_profile = nsx_client.TransportNodeProfiles(config).create(p)

        compute_collections = fabric_client.ComputeCollections(config).list().results
        transport_node_collections = nsx_client.TransportNodeCollections(config).list().results
        compute_collection:model_client.ComputeCollection
        for compute_collection in compute_collections:
            # a resource group has owner id. only a cluster can be transport node collection.
            if compute_collection.owner_id:
                continue
            existing_transport_node_collection: model_client.TransportNodeCollection = None
            transport_node_collection:model_client.TransportNodeCollection
            for transport_node_collection in transport_node_collections:
                if transport_node_collection.compute_collection_id == compute_collection.external_id:
                    existing_transport_node_collection = transport_node_collection
                    break
            if existing_transport_node_collection:
                LOGGER.info("transport node colleciton {} with compute collection id {} has already exists.".format(existing_transport_node_collection.id, existing_transport_node_collection.compute_collection_id))
                continue
            LOGGER.info("creating transport node collection for compute collection {} with transport node profile {}".format(compute_collection.external_id, default_transport_node_profile.id))
            transport_node_collection_req: model_client.TransportNodeCollection = model_client.TransportNodeCollection(
                compute_collection_id=compute_collection.external_id,
                transport_node_profile_id=default_transport_node_profile.id,            
            )
            nsx_client.TransportNodeCollections(config).create(transport_node_collection_req)

            