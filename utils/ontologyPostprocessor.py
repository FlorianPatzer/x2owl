import re

class OntologyPostprocessor:
    def __init__(self, inPath, outPath, ns):
        self.inPath = inPath
        self.outPath = outPath
        self.ns = ns

    def run(self):
        fileIn = open(self.inPath, "r")
        outputOntology = list()

        for line in fileIn:
            newLine = re.sub("<" + self.ns +"hasName>", "<" + self.ns + "name>", line)
            outputOntology.append(newLine)

        fileIn.close()

        fileOut = open(self.outPath, "w")

        for line in outputOntology:
            fileOut.write(line)

        fileOut.close()

        return self.outPath

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 4:
        (inPath, outPath, ns)=sys.argv[1:]
        op = OntologyPostprocessor(inPath, outPath, ns)
        op.run()
    else:
        print("Not the correct number of arguments! Please provide a path to the input ontology,"
              " a path to the output ontology and the ontology namespace.")