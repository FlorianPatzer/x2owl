import xml.etree.ElementTree as ET


class OntologyPreprocessor:
    def __init__(self, absOntoPath, relOutputPath):
        self.absOntoPath = absOntoPath
        self.relOutputPath = relOutputPath

    def run(self):
        ET.register_namespace("", "http://www.w3.org/2002/07/owl#")
        with open(self.absOntoPath, 'r') as xmlfile:
            tree = ET.parse(xmlfile)

        root = tree.getroot()

        for child in root.getchildren():
            if child.tag[child.tag.index("}") + 1:] == "SubClassOf":
                for subclassElement in child:
                    tag = subclassElement.tag[subclassElement.tag.index("}") + 1:]
                    if tag in ["DataMaxCardinality", "DataExactCardinality", "DataAllValuesFrom", "ObjectHasSelf",
                               "ObjectMaxCardinality"]:
                        root.remove(child)

        # Replace problematic declarations
        for dataProperty in root.iter('{http://www.w3.org/2002/07/owl#}DataProperty'):
            if dataProperty.get('IRI') == '#name':
                dataProperty.set('IRI', '#hasName')

        with open(self.relOutputPath, 'w') as xmloutfile:
            tree.write(xmloutfile, encoding='unicode')

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        (absOntoPath,relOutputPath) = sys.argv[1:]
    else:
        print("Not the correct number of arguments! Please provide a path to the input ontology"
              " and a path to the output ontology.")

