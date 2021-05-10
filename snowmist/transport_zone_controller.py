from com.vmware import nsx_client
from com.vmware.nsx import model_client

OVERLAY_TRANSPORT_ZONE_NAME = "overlay_nested"
VLAN_TRANSPORT_ZONE_NAME = "vlan_nested"
UPLINK1_TRANSPORT_ZONE_NAME = "uplink1_nested"
UPLINK2_TRANSPORT_ZONE_NAME = "uplink2_nested"
HOST_SWITCH_NAME = "n-vds1"
EDGE_UPLINK1_SWITCH_NAME = "uplink1"
EDGE_UPLINK2_SWITCH_NAME = "uplink2"

class TransportZoneContoller(object):
    def __init__(self, config, lab_name):
        if not config:
            raise ValueError
        if not lab_name:
            raise ValueError
        self.config = config
        self.lab_name = lab_name
        self.overlay_tz: model_client.TransportZone = None
        self.vlan_tz: model_client.TransportZone = None
        self.uplink1_tz: model_client.TransportZone = None
        self.uplink2_tz: model_client.TransportZone = None
        self.prepare_transport_zones()
        self.apply()
        super().__init__()

    def prepare_transport_zones(self):
        tz_client = nsx_client.TransportZones(self.config)

        # Find existing transport zones
        t: model_client.TransportZone
        for t in tz_client.list().results:
            if not t.nested_nsx:
                continue
            if t.host_switch_name == HOST_SWITCH_NAME:
                if t.transport_type == model_client.TransportZone.TRANSPORT_TYPE_OVERLAY:
                    self.overlay_tz = t
                    continue
                if t.transport_type == model_client.TransportZone.TRANSPORT_TYPE_VLAN:
                    self.vlan_tz = t
                    continue
            if t.host_switch_name == EDGE_UPLINK1_SWITCH_NAME:
                self.uplink1_tz = t
                continue
            if t.host_switch_name == EDGE_UPLINK2_SWITCH_NAME:
                self.uplink2_tz = t
                continue

    def apply(self):
        tz_client = nsx_client.TransportZones(self.config)

        # Find existing transport zones
        t: model_client.TransportZone
        for t in tz_client.list().results:
            if not t.nested_nsx:
                continue
            if t.host_switch_name == HOST_SWITCH_NAME:
                if t.transport_type == model_client.TransportZone.TRANSPORT_TYPE_OVERLAY:
                    self.overlay_tz = t
                    continue
                if t.transport_type == model_client.TransportZone.TRANSPORT_TYPE_VLAN:
                    self.vlan_tz = t
                    continue
            if t.host_switch_name == EDGE_UPLINK1_SWITCH_NAME:
                self.uplink1_tz = t
                continue
            if t.host_switch_name == EDGE_UPLINK2_SWITCH_NAME:
                self.uplink2_tz = t
                continue

        # Create transport zones if not exist
        if not self.overlay_tz:
            description = "This is overlay transport zone with nested_nsx enabled."
            req = model_client.TransportZone(display_name=OVERLAY_TRANSPORT_ZONE_NAME, nested_nsx=True, 
                host_switch_name=HOST_SWITCH_NAME, transport_type=model_client.TransportZone.TRANSPORT_TYPE_OVERLAY, 
                description=description)
            self.overlay_tz = tz_client.create(req)
        if not self.vlan_tz:
            description = "This is vlan transport zone with nested_nsx enabled."
            req = model_client.TransportZone(display_name=VLAN_TRANSPORT_ZONE_NAME, nested_nsx=True, 
                host_switch_name=HOST_SWITCH_NAME, transport_type=model_client.TransportZone.TRANSPORT_TYPE_VLAN, 
                description=description)
            self.vlan_tz = tz_client.create(req)
        if not self.uplink1_tz:
            description = "This is uplink1 transport zone with nested_nsx enabled."
            req = model_client.TransportZone(display_name=UPLINK1_TRANSPORT_ZONE_NAME, nested_nsx=True, 
                host_switch_name=EDGE_UPLINK1_SWITCH_NAME, transport_type=model_client.TransportZone.TRANSPORT_TYPE_VLAN, 
                description=description)
            self.uplink1_tz = tz_client.create(req)
        if not self.uplink2_tz:
            description = "This is uplink2 transport zone with nested_nsx enabled."
            req = model_client.TransportZone(display_name=UPLINK2_TRANSPORT_ZONE_NAME, nested_nsx=True, 
                host_switch_name=EDGE_UPLINK2_SWITCH_NAME, transport_type=model_client.TransportZone.TRANSPORT_TYPE_VLAN, 
                description=description)
            self.uplink2_tz = tz_client.create(req)

def get_bfd_health_monitoring_profile_id(config):
    profiles = nsx_client.TransportzoneProfiles(config).list(include_system_owned=True).results
    v: model_client.VapiStruct
    for v in profiles:
        profile = v.convert_to(model_client.BfdHealthMonitoringProfile)
        return profile.id
    return None