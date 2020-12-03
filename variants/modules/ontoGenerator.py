import owlready2
import re
import types
from variants.modules.processorOWL import Preprocessor, Postprocessor

class OntoGenerator():
    def __init__(self, repository, ontologyFile):
        owlready2.onto_path.append(repository)
        self.onto = owlready2.get_ontology(ontologyFile)
        self.onto.load(only_local=True, reload=True)
        self.objectIndividualMapping = {}

    def createOwlElements(self, subtree, config, owlId):
        value = subtree.get("value")

        # if preprocessing function is defined for this value, apply the function and replace the original value
        if config.get('owl_preprocessing_function') is not None:
            value = Preprocessor.process(value, config.get('owl_preprocessing_function'))

        # if the value is used as iri (i.e. when the value is an individual's name) and should have a suffix, add the suffix
        if config.get('owl_iri_suffix') is not None and config.get('owl_class') is not None:
            value = value + config.get('owl_iri_suffix')

        self.createDataProperty(config.get('owl_dataProperty'), config.get('owl_dataProperty_parent'))

        self.createClass(config.get('owl_class'), config.get('owl_class_parent'))

        # if obj is described with owl class, create an individual
        if config.get('owl_class') is not None:
            counterSuffix = 1
            individual = self.createIndividual(config.get('owl_class'), value)
            while (individual is None):
                individual = self.createIndividual(config.get('owl_class'), value + "_suffix" + str(counterSuffix))
                counterSuffix += 1
            value = individual.name
            self.objectIndividualMapping[subtree.get('object')] = individual.name

        # if object is an individual and has to be referenced by another individual
        if config.get('owl_objectProperty') is not None:
            tmpIndividualName = self.objectIndividualMapping.get(config.get('owl_objectProperty_domain_object'))
            if tmpIndividualName is None:
                tmpIndividualName = owlId
            self.addObjectPropertyReference(tmpIndividualName, config.get('owl_objectProperty'), value)

        #
        if config.get('owl_dataProperty') is not None:
            tmpIndividualName = self.objectIndividualMapping.get(config.get('owl_dataProperty_domain_object'))
            if tmpIndividualName is None:
                tmpIndividualName = owlId

            if config.get('data_type'):
                if value is not None:
                    if config.get('data_type') == "int":
                        value = int(value)
                    elif config.get('data_type') == "bool":
                        value = bool(value)
                    else:
                        value = str(value)
            self.addDataPropertyReference(tmpIndividualName, config.get('owl_dataProperty'), value)

        if subtree.get("objects"):
            for child in subtree.get("objects"):
                childConfig = None

                for cConfig in config.get("objects"):
                    if cConfig.get("object") == child.get("object"):
                        childConfig = cConfig
                if not childConfig:
                    raise KeyError("No config found for object %s" % child.get("object"))

                self.createOwlElements(child, childConfig, owlId)

        if config.get('owl_postprocessing_functions') is not None:
            postprocessor = Postprocessor(config.get('owl_postprocessing_functions'), owlId)
            postprocessor.process(self, self.objectIndividualMapping.get(subtree.get('object')))
            del postprocessor
            #for processResult in postprocessor.process(self, self.objectIndividualMapping.get(subtree.get('object'))):
            #    pass

    def findObjectValue(self, objectTree, targetObject):
        if objectTree.get("object") == targetObject:
            return objectTree.get("value")

        if objectTree.get("objects"):
            for child in objectTree.get("objects"):
                res = self.findObjectValue(child, targetObject)
                if res:
                    return res
        return None

    def generateByObjectHierarchy(self, loadedYaml, wood):
        owlId = None
        if loadedYaml.get("owl_unique_identifier_type") == "object":
            for tree in wood:
                owlId = self.findObjectValue(tree, loadedYaml.get("owl_unique_identifier_object"))
                if owlId:
                    break
        elif loadedYaml.get("owl_unique_identifier_type") == "string":
            owlId = loadedYaml.get("owl_unique_identifier_object")
            idConfig = {"object": owlId, "owl_class": loadedYaml.get("owl_unique_identifier_class"), "owl_class_parent":  loadedYaml.get("owl_unique_identifier_class_parent")}
            idTree = {"object": owlId, "value": owlId}
            self.createOwlElements(idTree, idConfig, owlId)

        if owlId:
            for tree in wood:
                childConfig = None
                for cConfig in loadedYaml.get("commands"):
                    if cConfig.get("object") == tree.get("object"):
                        childConfig = cConfig
                if not childConfig:
                    raise KeyError("No config found for object %s" % tree.get("object"))

                self.createOwlElements(tree, childConfig, owlId)

    def createDataProperty(self, iri, parentIri):
        iri = self.normalizeIri(iri)
        parentIri = self.normalizeIri(parentIri)
        if iri is None or parentIri is None or self.onto[iri] is not None or self.onto[parentIri] is None:
            a = self.onto[iri]
            b = self.onto[parentIri]
            return None

        return types.new_class(iri, (self.onto[parentIri],))

    def normalizeIri(self, iri):
        if iri:
            iri = re.sub(r"\.|\s|\(|\)|/|\+", "_", iri)
            #iri = re.sub(r"\.", "-", iri)
        return iri

    def createClass(self, className, parentClassName):
        if className is None or parentClassName is None or self.onto[className] is not None or self.onto[parentClassName] is None:
            return None

        return types.new_class(className, (self.onto[parentClassName] ,))

    def createIndividual(self, className, iri):
        iri = self.normalizeIri(iri)

        if className is None or iri is None or self.onto[iri] is not None:
            return None
        #print("Created individual %s"%iri)

        return self.onto[className](iri)

    def addObjectPropertyReference(self, domainIri, propertyIri, rangeIri):
        domainIri = self.normalizeIri(domainIri)
        propertyIri = self.normalizeIri(propertyIri)
        rangeIri = self.normalizeIri(rangeIri)
        #print("Trying to add object property (%s, %s, %s, %s, %s, %s)"% (domainIri, self.onto[domainIri], propertyIri, self.onto[propertyIri], rangeIri, self.onto[rangeIri]))
        if domainIri is None or propertyIri is None or rangeIri is None or self.onto[domainIri] is None or self.onto[propertyIri] is None or self.onto[rangeIri] is None:
            return False

        #print("Adding object property (%s, %s, %s)"% (domainIri, propertyIri, rangeIri))
        tmpList = list()
        individual = self.onto[domainIri]
        range = getattr(individual, propertyIri)
        if type(range) == str:
            tmpList.append(range)
        else:
            if range:
                tmpList = list(range)
        tmpList.append(self.onto[rangeIri])
        setattr(individual, propertyIri, tmpList)
        return True

    def getObjectPropertyRelations(self, domainIri, propertyIri):
        domainIri = self.normalizeIri(domainIri)
        propertyIri = self.normalizeIri(propertyIri)
        if domainIri is None or propertyIri is None:
            return False

        return list(getattr(self.onto[domainIri], propertyIri, None))

    def addDataPropertyReference(self, domainIri, propertyIri, value):
        domainIri = self.normalizeIri(domainIri)
        propertyIri = self.normalizeIri(propertyIri)
        if value is None:
            return False

        tmpList = []
        individual = self.onto[domainIri]
        range = getattr(individual, propertyIri)
        if type(range) == str:
            tmpList.append(range)
        else:
            if range:
                tmpList = range
        tmpList.append(value)
        setattr(self.onto[domainIri], propertyIri, tmpList)
        return True

    def getClass(self, className):
        return self.onto[className]

    def getClasses(self):
        return self.onto.classes()

    def getIndividuals(self):
        return self.onto.individuals()

    def getIndividual(self, iri):
        iri = self.normalizeIri(iri)
        return self.onto[iri]

    def save(self, file, format):
        self.onto.save(file=file, format=format)
