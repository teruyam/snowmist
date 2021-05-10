from com.vmware.nsx import model_client, node_client


def get_product_version(config, lab_name):
    node_version: model_client.NodeVersion = node_client.Version(config).get()
    return node_version.product_version
