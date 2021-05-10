from com.vmware import nsx_client
from com.vmware.nsx import model_client

NSX_DEFAULT_UPLINK_HOST_SWITCH_PROFILE = "nsx-default-uplink-hostswitch-profile"
NSX_EDGE_SINGLE_NIC_UPLINK_PROFILE = "nsx-edge-single-nic-uplink-profile"
NSX_DEFAULT_NIOC_HOSTSWITCH_PROFILE = "nsx-default-nioc-hostswitch-profile"

def get_uplink_profile_id(config, uplink_display_name):
    if not config or not uplink_display_name:
        raise ValueError
    profiles = nsx_client.HostSwitchProfiles(config).list(
        hostswitch_profile_type=nsx_client.HostSwitchProfiles.LIST_HOSTSWITCH_PROFILE_TYPE_UPLINKHOSTSWITCHPROFILE,
        include_system_owned=True).results
    bp: model_client.BaseHostSwitchProfile
    for bp in profiles:
        sp: model_client.UplinkHostSwitchProfile = bp.convert_to(model_client.UplinkHostSwitchProfile)
        if sp.display_name == uplink_display_name:
            return sp.id
    return None

def get_nioc_profile_id(config, nioc_display_name=NSX_DEFAULT_NIOC_HOSTSWITCH_PROFILE):
    if not config or not nioc_display_name:
        raise ValueError
    profiles = nsx_client.HostSwitchProfiles(config).list(
        hostswitch_profile_type=nsx_client.HostSwitchProfiles.LIST_HOSTSWITCH_PROFILE_TYPE_NIOCPROFILE,
        include_system_owned=True).results
    bp: model_client.BaseHostSwitchProfile
    for bp in profiles:
        sp: model_client.UplinkHostSwitchProfile = bp.convert_to(model_client.NiocProfile)
        if sp.display_name == nioc_display_name:
            return sp.id
    return None

def get_lldp_profile_id(config, sent_enabled=False):
    if not config:
        raise ValueError
    profiles = nsx_client.HostSwitchProfiles(config).list(
        hostswitch_profile_type=nsx_client.HostSwitchProfiles.LIST_HOSTSWITCH_PROFILE_TYPE_LLDPHOSTSWITCHPROFILE,
        include_system_owned=True).results
    bp: model_client.BaseHostSwitchProfile
    for bp in profiles:
        sp: model_client.LldpHostSwitchProfile = bp.convert_to(model_client.LldpHostSwitchProfile)
        if sp.send_enabled == sent_enabled:
            return sp.id
    return None
