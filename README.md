# SnowMist

SnowMist is an internal tool to build nested NSX-T lab infrastructure running on NSX-T infrastructure. SnowMist is designed to bootstrap fundamental lab environment for testing purpose.

SnowMist will do:
1. Register a compute manager (vCenter)
1. Create IP Pools
1. Create Transport Zones with nested flag enabled
1. Prepare Transport Nodes
1. Create a edge cluster and Join NSX Edge(s)
1. Create Uplink segments (Uplink1 and Uplink2)
1. Create T0 Gateway and connect to uplink segments
1. Create T0 Gateway Default Route and HA VIP
1. Create DHCP Server
1. Create T1 Gateways (Tenant1 and Tenant2)
1. Create Overlay segments 
    1. Red 192.168.101.0/24
    1. Blue 192.168.102.0/24
    1. Green 192.168.103.0/24
    1. Yellow 192.168.104.0/24

## Network Topology
Based on VMware Validated Design (VVD), SnowMist requires following subnets for lab network infrastructure depending on given lab name.
| Type of Subnet | Lab1 | Lab2 | Lab3 |
| - | - | - | - |
| Management | 10.6.11.0/24 | 10.6.21.0/24 | 10.6.31.0/24 |
| Host (TEP subnet for hosts) | 10.6.12.0/24 | 10.6.22.0/24 | 10.6.32.0/24 |
| Edge (TEP subnet for Edges) | 10.6.13.0/24 | 10.6.23.0/24 | 10.6.33.0/24 |
| Uplink1 | 10.6.14.0/24 | 10.6.24.0/24 | 10.6.34.0/24 |
| Uplink2 | 10.6.15.0/24 | 10.6.25.0/24 | 10.6.35.0/24 |

### IP Addresses
[provider_network.py](snowmist/provider_network.py)

SnowMist always assumes first ip address is gateway. For example gateway ip address for lab1 management network is 10.6.11.1.

IP Pools for both Host and Edge TEP start at 11 and end at 240. Host TEP IP Pool is 10.6.12.11-10.6.12.240.

[ip_pool.py](snowmist/ip_pool.py)

IP Addresses used by T0 Gateway Uplink start from 11. Uplink1 will have VIP with 10.

[networking.py](snowmist/networking.py)

### NIC Connectivity
| Edge | Network |
| ------- | --------------------------- |
| eth0 | Management |
| fp-eth0 | Edge (TEP subnet for Edges) |
| fp-eth1 | Uplink1 |
| fp-eth2 | Uplink2 |

| ESXi Host | Network |
| - | - |
| vmnic0 | Management |
| vmnic1 | Host (TEP subnet for hosts) |

# Runtime Requirements
  - Python 3.6+

# Quick Start
  - [Install and Configure vSphere](#install-and-configure-vsphere)
  - [Install and Configure NSX-T](#install-and-configure-nsx-t)
  - Download NSX-T Python SDK from vmware.com
  - [Install Prerequisites](#install-prerequisites)
  - [Run](#run)

## **Install and Configure vSphere**
1. Create a datacenter and cluster(s)
1. Add ESXi host(s) to the cluster(s)

## **Install and Configure NSX-T**
1. Deploy NSX Manager(s) and NSX Edge(s)
1. Apply licenses
1. Join NSX Edge(s) to NSX Manager(s)

## **Install Prerequisites**
From a bash, install NSX-T Python SDK with pip command.
```bash
# Install NSX-T Python SDK downloaded from vmware.com
pip install vapi_runtime-2.19.0-py2.py3-none-any.whl \
    vapi_common-2.19.0-py2.py3-none-any.whl \
    vapi_common_client-2.19.0-py2.py3-none-any.whl \
    nsx_python_sdk-3.1.1.0.0-py2.py3-none-any.whl \
    nsx_policy_python_sdk-3.1.1.0.0-py2.py3-none-any.whl \
    nsx_global_policy_python_sdk-3.1.1.0.0-py2.py3-none-any.whl

# Clone this repository
git clone https://github.com/teruyam/snowmist.git
cd snowmist
```

## **Run**
```bash
python3 -m snowmist --lab-name lab2 \
    --lab-nsx-username admin \
    --lab-nsx-password VMware123!VMware123! \
    --lab-nsx-hostname nsxm1.lab2.vmware.com \
    --lab-vc-username  administrator@vsphere.local \
    --lab-vc-password VMware123! \
    --lab-vc-hostname vc.lab2.vmware.com 
```