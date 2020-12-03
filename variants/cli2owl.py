import subprocess
import yaml
import re
from variants.modules.ontoGenerator import OntoGenerator
from variants.modules.commandOutputParser import CommandOutputParser

class Cli2Owl:
    def __init__(self, loadedYaml):
        self.loadedYaml = loadedYaml

    def parseAndBuildWood(self):
        wood = []

        # Iterate over command outputs either provided in a file or by a cli command also performed here
        for config in self.loadedYaml.get("commands"):
            # Configuration needs to configure commands
            if config.get("command") is None:
                raise Exception("Configuration error: ", config, " has no command", )
            else:
                if self.loadedYaml.get("commands_from_file"):
                    commandFile = open(self.loadedYaml.get("commands_file"), "r")
                    commandOutput = ""
                    commandFound = False
                    for line in commandFile:
                        if commandFound:
                            break
                        if re.search("---" + re.escape(config["command"]) + "---", line):
                            for innerline in commandFile:
                                if innerline == "------\n":
                                    break
                                commandOutput += innerline
                                commandFound = True
                    commandFile.close()
                else:
                    commandArray = str(config["command"]).split(sep=" ")
                    commandOutput = subprocess.run(commandArray, stdout=subprocess.PIPE, encoding="utf-8")
                    commandOutput = str(commandOutput.stdout)

                parser = CommandOutputParser()
                tree = parser.buildObjectTree(config, commandOutput, config.get("iterate_subtree_mapping"))
                tree["config"] = config
                wood.append(tree)
        return wood

    def run(self):

        owl = OntoGenerator(self.loadedYaml.get('owl_ontology_repository'), self.loadedYaml.get('owl_input_ontology_file'))

        wood = self.parseAndBuildWood()

        owl.generateByObjectHierarchy(self.loadedYaml, wood)

        owl.save(self.loadedYaml.get('owl_output_ontology_file'), self.loadedYaml.get('owl_output_ontology_file_type'))



if __name__ == "__main__":
    import sys
    cli2owl = Cli2Owl(sys.argv[1], sys.argv[2], sys.argv[3])
    cli2owl.run()
