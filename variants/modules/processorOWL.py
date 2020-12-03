import re


class Utils:

    def ipV4ToString(address):
        if address == 4278190081:
            return "special_network"
        elif  address == 4278190082:
            return "self_network"
        a = address >> 24
        b = (address >> 16) & 0b11111111
        c = (address >> 8) & 0b11111111
        d = address & 0b11111111
        return "%s.%s.%s.%s" % (a,b,c,d)

class Preprocessor(object):

    @classmethod
    def process(cls, value, methodName):
        try:
            print("Trying to preprocess value %s with method %s" % (value,methodName))
            return getattr(cls, methodName)(value)
        except AttributeError:
            print("Unable to preprocess value %s with method %s" % (value,methodName))
            return value

    @classmethod
    def pfAddressIpV4ToInteger(cls, address):
        if "any" in address:
            return 0
        elif "/" in address:
            address, b = address.split("/")
            return cls.ipV4ToInteger(address)
        elif re.search("[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", address):
            return cls.ipV4ToInteger(address)
        else:
            return None

    @classmethod
    def pfAddressIpV4NetmaskToInteger(cls, address):
        if "any" in address:
            return 0
        elif "/" in address:
            a, b = address.split("/")
            return int(b)
        elif re.search("[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", address):
            return 32
        else:
            return None


    @classmethod
    def ipV4ToInteger(cls, address):
        a,b,c,d = address.split(".")
        intAddress = int(a)
        intAddress <<= 8
        intAddress += int(b)
        intAddress <<= 8
        intAddress += int(c)
        intAddress <<= 8
        intAddress += int(d)
        return intAddress

    @classmethod
    def ipV4HexNetmaskToInteger(cls, netmask):
        counter = 32
        intNetmask = int(netmask, 16)
        while True:
            if (intNetmask & 1) == 1:
                break
            counter -= 1
            intNetmask = intNetmask >> 1
        return counter

    @classmethod
    def quickToBoolean(cls, quick):
        return quick == 'quick'

    @classmethod
    def ipV4NetmaskToInteger(cls, netmask):
        counter = 32
        intNetmask = cls.ipV4ToInteger(netmask)
        while True:
            if (intNetmask & 1) == 1:
                break
            counter -= 1
            intNetmask = intNetmask >> 1
        return counter


class Postprocessor:
    class IriConstants:
        OBJ_PROP_IS_IN_NETWORK = "isInNetwork"
        DATA_PROP_IP_V4_ADDRESS = "ipV4Address"
        DATA_PROP_PREFIX_BITS = "prefixBits"
        CLASS_NETWORK = "Network"
        OBJ_PROP_FIREWALL_CONFIG = "firewallConfig"
        CLASS_PF_CONFIG = "PfConfiguration"
        OBJ_PROP_PF_FIRST_RULE = "pfFirstRule"
        OBJ_PROP_PF_NEXT_RULE = "pfNextRule"
        OBJ_PROP_SERVICE_LIST = "serviceList"
        CLASS_SERVICE_LIST = "ServiceList"
        OBJ_PROP_SERVICE = "service"
        Data_PROP_PF_INTERFACE = "pfInterface"
        CLASS_DNS_INTERFACE = "DnsInterface"
        OWL_IRI_SUFFIX_ETHERNET_INTERFACE = 'EthernetInterface'
        OWL_IRI_SUFFIX_IPV4_INTERFACE = 'IpV4Interface'
        OBJ_PROP_USES_INTERFACE = 'usesInterface'
        OBJ_PROP_ASSIGNED_TO_NETWORK = 'assignedToNetwork'

    def __init__(self, methods, rootNodeIri):
        self.methods = methods
        self.pfFirstRule = None
        self.pfPreviousRule = None
        self.rootNodeIri = rootNodeIri

    #Generator running method by method and returning its result
    def process(self, onto, arg):
        for method in self.methods:
            try:
                print("Running function %s"% method)
                getattr(self, method)(onto, arg)
                #yield getattr(self, method)(onto, arg)
            except AttributeError as e:
                raise e
                print("Unable to postprocess value %s with method %s - error: %s" % (arg,method,e))
                #yield arg

    def addIpV4Network(self, onto, individual):
        interfaceIndividual = onto.getIndividual(individual)
        if interfaceIndividual is None:
            raise AttributeError("Unable to retrieve individual %s" % individual)
        if not interfaceIndividual.ipV4Address or not interfaceIndividual.prefixBits:
            return

        ipV4Address = int(interfaceIndividual.ipV4Address[0])
        ipV4Netmask = int(interfaceIndividual.prefixBits[0])

        ipV4AddressString = "%s/%i" % (Utils.ipV4ToString(ipV4Address), ipV4Netmask)
        # shifted IP/netmask
        ipV4Address = ipV4Address >> (32 - ipV4Netmask)


        networkIndividual = onto.getIndividual(ipV4AddressString)
        if networkIndividual is None:
            networkIndividual = onto.createIndividual(Postprocessor.IriConstants.CLASS_NETWORK, ipV4AddressString)

            #onto.addDataPropertyReference(ipV4AddressString, Postprocessor.IriConstants.DATA_PROP_IP_V4_ADDRESS, ipV4Address)
            onto.addDataPropertyReference(networkIndividual.name, Postprocessor.IriConstants.DATA_PROP_IP_V4_ADDRESS,ipV4Address)

            #onto.addDataPropertyReference(ipV4AddressString, Postprocessor.IriConstants.DATA_PROP_PREFIX_BITS, ipV4Netmask)
            onto.addDataPropertyReference(networkIndividual.name, Postprocessor.IriConstants.DATA_PROP_PREFIX_BITS,ipV4Netmask)
            if networkIndividual is None:
                raise ValueError("Unable to create individual %s" % ipV4AddressString)

        #onto.addObjectPropertyReference(interfaceIndividual.name, Postprocessor.IriConstants.OBJ_PROP_ASSIGNED_TO_NETWORK, ipV4AddressString)
        onto.addObjectPropertyReference(interfaceIndividual.name, Postprocessor.IriConstants.OBJ_PROP_ASSIGNED_TO_NETWORK, networkIndividual.name)


    def addIpV4Networks(self, onto, individual):
        interfaceIndividual = onto.getIndividual(individual)
        if interfaceIndividual is None:
            raise AttributeError("Unable to retrieve individual %s" % individual)
        if not interfaceIndividual.ipV4Address or not interfaceIndividual.prefixBits:
            return

        ipV4Address = int(interfaceIndividual.ipV4Address[0])
        ipV4Netmask = int(interfaceIndividual.prefixBits[0])

        #IP/32 network
        ipV4AddressString = "%s/%i" % (Utils.ipV4ToString(ipV4Address), 32)

        networkIndividual = onto.getIndividual(str(ipV4AddressString))
        if networkIndividual is None:
            networkIndividual = onto.createIndividual(Postprocessor.IriConstants.CLASS_NETWORK, ipV4AddressString)
            #onto.addDataPropertyReference(ipV4AddressString, Postprocessor.IriConstants.DATA_PROP_IP_V4_ADDRESS, ipV4Address)
            onto.addDataPropertyReference(networkIndividual.name, Postprocessor.IriConstants.DATA_PROP_IP_V4_ADDRESS, ipV4Address)
            #onto.addDataPropertyReference(ipV4AddressString, Postprocessor.IriConstants.DATA_PROP_PREFIX_BITS, 32)
            onto.addDataPropertyReference(networkIndividual.name, Postprocessor.IriConstants.DATA_PROP_PREFIX_BITS, 32)
            if networkIndividual is None:
                raise ValueError("Unable to create individual %s" % ipV4AddressString)

        #onto.addObjectPropertyReference(interfaceIndividual.name, Postprocessor.IriConstants.OBJ_PROP_IS_IN_NETWORK, ipV4AddressString)
        onto.addObjectPropertyReference(interfaceIndividual.name, Postprocessor.IriConstants.OBJ_PROP_IS_IN_NETWORK,
                                        networkIndividual.name)

        ethernetIndividual = onto.getIndividual(interfaceIndividual.hasName[0] + Postprocessor.IriConstants.OWL_IRI_SUFFIX_ETHERNET_INTERFACE)
        if ethernetIndividual:
            onto.addObjectPropertyReference(interfaceIndividual.name, Postprocessor.IriConstants.OBJ_PROP_USES_INTERFACE, ethernetIndividual.name)

        ipV4AddressString = "%s/%i" % (Utils.ipV4ToString(ipV4Address), ipV4Netmask)
        #shifted IP/netmask
        ipV4Address = ipV4Address >> (32 - ipV4Netmask)

        networkIndividual = onto.getIndividual(ipV4AddressString)
        if networkIndividual is None:
            networkIndividual = onto.createIndividual(Postprocessor.IriConstants.CLASS_NETWORK, ipV4AddressString)
            #onto.addDataPropertyReference(ipV4AddressString, Postprocessor.IriConstants.DATA_PROP_IP_V4_ADDRESS, ipV4Address)
            onto.addDataPropertyReference(networkIndividual.name, Postprocessor.IriConstants.DATA_PROP_IP_V4_ADDRESS,
                                          ipV4Address)
            #onto.addDataPropertyReference(ipV4AddressString, Postprocessor.IriConstants.DATA_PROP_PREFIX_BITS, ipV4Netmask)
            onto.addDataPropertyReference(networkIndividual.name, Postprocessor.IriConstants.DATA_PROP_PREFIX_BITS, ipV4Netmask)
            if networkIndividual is None:
                raise ValueError("Unable to create individual %s" % ipV4AddressString)

        #onto.addObjectPropertyReference(interfaceIndividual.name, Postprocessor.IriConstants.OBJ_PROP_ASSIGNED_TO_NETWORK, ipV4AddressString)
        onto.addObjectPropertyReference(interfaceIndividual.name, Postprocessor.IriConstants.OBJ_PROP_ASSIGNED_TO_NETWORK, networkIndividual.name)

    def addIpV4NetworksIndividualName(self, onto, individual):
        interfaceIndividual = onto.getIndividual(individual)
        if interfaceIndividual is None:
            raise AttributeError("Unable to retrieve individual %s" % individual)

        ethernetIndividual = onto.getIndividual(re.sub(Postprocessor.IriConstants.OWL_IRI_SUFFIX_IPV4_INTERFACE,
                                                       Postprocessor.IriConstants.OWL_IRI_SUFFIX_ETHERNET_INTERFACE,
                                                       interfaceIndividual.name))
        if ethernetIndividual:
            onto.addObjectPropertyReference(interfaceIndividual.name,
                                            Postprocessor.IriConstants.OBJ_PROP_USES_INTERFACE, ethernetIndividual.name)

        if not interfaceIndividual.ipV4Address or not interfaceIndividual.prefixBits:
            return

        ipV4Address = int(interfaceIndividual.ipV4Address[0])
        ipV4Netmask = int(interfaceIndividual.prefixBits[0])

        #IP/32 network
        ipV4AddressString = "%s/%i" % (Utils.ipV4ToString(ipV4Address), 32)

        networkIndividual = onto.getIndividual(str(ipV4AddressString))
        if networkIndividual is None:
            networkIndividual = onto.createIndividual(Postprocessor.IriConstants.CLASS_NETWORK, ipV4AddressString)
            if networkIndividual is None:
                raise ValueError("Unable to create individual %s" % ipV4AddressString)

        #onto.addObjectPropertyReference(interfaceIndividual.name, Postprocessor.IriConstants.OBJ_PROP_IS_IN_NETWORK, ipV4AddressString)
        onto.addObjectPropertyReference(interfaceIndividual.name, Postprocessor.IriConstants.OBJ_PROP_IS_IN_NETWORK,
                                        networkIndividual.name)
        #onto.addDataPropertyReference(ipV4AddressString, Postprocessor.IriConstants.DATA_PROP_IP_V4_ADDRESS, ipV4Address)
        onto.addDataPropertyReference(networkIndividual.name, Postprocessor.IriConstants.DATA_PROP_IP_V4_ADDRESS,
                                      ipV4Address)
        #onto.addDataPropertyReference(ipV4AddressString, Postprocessor.IriConstants.DATA_PROP_PREFIX_BITS, 32)
        onto.addDataPropertyReference(networkIndividual.name, Postprocessor.IriConstants.DATA_PROP_PREFIX_BITS, 32)


        ipV4AddressString = "%s/%i" % (Utils.ipV4ToString(ipV4Address), ipV4Netmask)
        #shifted IP/netmask
        ipV4Address = ipV4Address >> (32 - ipV4Netmask)

        networkIndividual = onto.getIndividual(ipV4AddressString)
        if networkIndividual is None:
            networkIndividual = onto.createIndividual(Postprocessor.IriConstants.CLASS_NETWORK, ipV4AddressString)
            if networkIndividual is None:
                raise ValueError("Unable to create individual %s" % ipV4AddressString)

        #onto.addObjectPropertyReference(interfaceIndividual.name, Postprocessor.IriConstants.OBJ_PROP_ASSIGNED_TO_NETWORK, ipV4AddressString)
        onto.addObjectPropertyReference(interfaceIndividual.name,
                                        Postprocessor.IriConstants.OBJ_PROP_ASSIGNED_TO_NETWORK, networkIndividual.name)
        #onto.addDataPropertyReference(ipV4AddressString, Postprocessor.IriConstants.DATA_PROP_IP_V4_ADDRESS, ipV4Address)
        onto.addDataPropertyReference(networkIndividual.name, Postprocessor.IriConstants.DATA_PROP_IP_V4_ADDRESS,
                                      ipV4Address)
        #onto.addDataPropertyReference(ipV4AddressString, Postprocessor.IriConstants.DATA_PROP_PREFIX_BITS, ipV4Netmask)
        onto.addDataPropertyReference(networkIndividual.name, Postprocessor.IriConstants.DATA_PROP_PREFIX_BITS, ipV4Netmask)

    def setPfFirstRule(self, onto, individual):
        #get pfFirstRule if already exists
        relations = onto.getObjectPropertyRelations(self.rootNodeIri, Postprocessor.IriConstants.OBJ_PROP_FIREWALL_CONFIG)
        if not relations:
            pfConfigIndividual = onto.createIndividual(Postprocessor.IriConstants.CLASS_PF_CONFIG, "pf_configuration")
            onto.addObjectPropertyReference(onto.getIndividual(self.rootNodeIri).name, Postprocessor.IriConstants.OBJ_PROP_FIREWALL_CONFIG, pfConfigIndividual.name)
        else:
            pfConfigIndividual = relations[0]

        pfFirstRuleList = onto.getObjectPropertyRelations(pfConfigIndividual.name, Postprocessor.IriConstants.OBJ_PROP_PF_FIRST_RULE)

        if not pfFirstRuleList:
            pfFirstRule = onto.getIndividual(individual)
            onto.addObjectPropertyReference(pfConfigIndividual.name, Postprocessor.IriConstants.OBJ_PROP_PF_FIRST_RULE, pfFirstRule.name)

    def setAndLinkPfPreviousRule(self, onto, individual):
        relations = onto.getObjectPropertyRelations(self.rootNodeIri, Postprocessor.IriConstants.OBJ_PROP_FIREWALL_CONFIG)
        if not relations:
            return
        pfFirstRuleList = onto.getObjectPropertyRelations(relations[0].name, Postprocessor.IriConstants.OBJ_PROP_PF_FIRST_RULE)

        if not pfFirstRuleList:
            return

        pfFirstRule = pfFirstRuleList[0]
        pfPreviousRule = pfFirstRule
        while(1):
            tmpList = onto.getObjectPropertyRelations(pfPreviousRule.name, Postprocessor.IriConstants.OBJ_PROP_PF_NEXT_RULE)
            if not tmpList:
                break
            pfPreviousRule = tmpList[0]

        if pfPreviousRule.name != individual:
            onto.addObjectPropertyReference(pfPreviousRule.name, Postprocessor.IriConstants.OBJ_PROP_PF_NEXT_RULE, individual)

    def addToServiceList(self, onto, individual):
        # get hasServiceList if already exists
        relations = onto.getObjectPropertyRelations(self.rootNodeIri, Postprocessor.IriConstants.OBJ_PROP_SERVICE_LIST)
        if not relations:
            serviceListIndividual = onto.createIndividual(Postprocessor.IriConstants.CLASS_SERVICE_LIST, "etc_service_list")
            if serviceListIndividual is None:
                pass
            onto.addObjectPropertyReference(onto.getIndividual(self.rootNodeIri).name, Postprocessor.IriConstants.OBJ_PROP_SERVICE_LIST,
                                            serviceListIndividual.name)
        else:
            serviceListIndividual = relations[0]

        serviceIndividual = onto.getIndividual(individual)
        onto.addObjectPropertyReference(serviceListIndividual.name, Postprocessor.IriConstants.OBJ_PROP_SERVICE, serviceIndividual.name)

    def addDnsClass(self, onto, individual):
        interfaceIndividual = onto.getIndividual(individual)
        dnsInterfaceClass = onto.getClass(Postprocessor.IriConstants.CLASS_DNS_INTERFACE)
        if dnsInterfaceClass:
            interfaceIndividual.is_a.append(dnsInterfaceClass)