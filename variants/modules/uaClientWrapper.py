from builtins import print

from opcua import Client, Node, ua

class UaClientWrapper(object):
    def __init__(self, endpoint, targetNs):
        self.endpoint = endpoint
        self.client = Client(endpoint)
        try:
            self.client.connect()
            self.namespaceArray = self.client.get_namespace_array()
            self.targetNs = self.client.get_namespace_index(targetNs)
            print("Target NS %s"%targetNs)
        except:
            self.disconnect()

    def get_namespace_array(self):
        return self.namespaceArray

    def collect_child_nodes(self, node, tree):
        # iterate over all referenced nodes (31), only hierarchical references (33)
        for child in node.get_children(refs=33):
            if not tree.get("children"):
                tree["children"] = []
            tree["children"].append({"node": child})
            self.collect_child_nodes(child, tree["children"][-1])

    def import_nodes(self, root_node=None):
        for ns in self.client.get_namespace_array():
            self.nsMapping[self.client.get_namespace_index(ns)] = ns

        if root_node is None:
            root = self.client.get_root_node()
        else:
            root = self.client.get_node(root_node)
        tree = {}
        self.collect_child_nodes(root, tree)
        return tree

    def getNamespaceIndices(self, list):
        self.nsMapping = {}
        for ns in list:
            self.nsMapping[ns] = self.client.get_namespace_index(ns)
        return self.nsMapping

    def clearModel(self, rootNode):
        root = self.client.get_node(rootNode)
        self.client.delete_nodes(root.get_children(), True)

    def addObject(self, parentNodeId, bName, objectType, identifier=0):
        parent = self.client.get_node(parentNodeId)

        node = parent.add_object("ns=%i;i=%i" % (self.targetNs, identifier), bName, objectType)
        node.__class__ = Node
        return node

    def escapeName(self, name: str):
        return name.replace(":","|")

    def addNodes(self, rootNode, objects):
        for obj in objects:
            if 'ua_object_type' in obj:
                if obj['value'] != '':
                    name = obj['value']
                else:
                    name = obj['object']
                node = self.addObject(rootNode, self.escapeName(name), "ns=%s;i=%s" % (self.nsMapping[obj['ua_object_type']['ns']], obj['ua_object_type']['i']))
                obj['ua_node_id'] = node.nodeid.to_string()
                if 'objects' in obj:
                    obj['objects'] = self.addNodes(obj['ua_node_id'], obj['objects'])
            elif 'ua_variable_qualified_name' in obj and obj['value'] != '':
                qname = ua.QualifiedName(obj['ua_variable_qualified_name']['browse_name'], self.nsMapping[obj['ua_variable_qualified_name']['ns']])
                root = self.client.get_node(rootNode)
                variable = root.get_child(qname)
                variable.set_value(obj['value'])
        return obj

    def disconnect(self):
        self.client.disconnect()