SUBNET_TYPE_MANAGEMENT = "Management"
SUBNET_TYPE_HOST = "Transport Host"
SUBNET_TYPE_EDGE = "Transport Edge"
SUBNET_TYPE_UPLINK1 = "Uplink1"
SUBNET_TYPE_UPLINK2 = "Uplink2"
SUBNET_TYPES = [SUBNET_TYPE_MANAGEMENT, SUBNET_TYPE_HOST, SUBNET_TYPE_EDGE, SUBNET_TYPE_UPLINK1, SUBNET_TYPE_UPLINK2]

def get_subnet_text(lab_name, subnet_type):
    source = {
        SUBNET_TYPE_MANAGEMENT: {"lab1": "10.6.11.0/24", "lab2": "10.6.21.0/24", "lab3": "10.6.31.0/24"},
        SUBNET_TYPE_HOST: {"lab1": "10.6.12.0/24", "lab2": "10.6.22.0/24", "lab3": "10.6.32.0/24"},
        SUBNET_TYPE_EDGE: {"lab1": "10.6.13.0/24", "lab2": "10.6.23.0/24", "lab3": "10.6.33.0/24"},
        SUBNET_TYPE_UPLINK1: {"lab1": "10.6.14.0/24", "lab2": "10.6.24.0/24", "lab3": "10.6.34.0/24"},
        SUBNET_TYPE_UPLINK2: {"lab1": "10.6.15.0/24", "lab2": "10.6.25.0/24", "lab3": "10.6.35.0/24"},
    }
    item = source.get(subnet_type)
    if not item:
        return None
    return item.get(lab_name)
