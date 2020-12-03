from pathlib import Path
from variants.cli2owl import Cli2Owl
import yamale
from utils.ontologyPostprocessor import OntologyPostprocessor
from utils.ontologyPreprocessor import OntologyPreprocessor


class X2Owl:

    def __init__(self, configFile):
        self.loadedYaml = yamale.make_data(configFile)
        loadedYamlSchema = yamale.make_schema(str(Path(__file__).parent) + "/resources/configuration_schema.yml")
        try:
            yamale.validate(loadedYamlSchema,self.loadedYaml)
        except yamale.YamaleError as e:
            print('Validation failed!\n%s' % str(e))
            exit(1)

    def run(self):
        self.loadedYaml = self.loadedYaml[0][0]
        if self.loadedYaml.get("ontology_preprocessor"):
            fName, suffix = Path(self.loadedYaml.get("owl_input_ontology_file")).name.split(".")
            outName = fName + "_preprocessed." + suffix
            dir = Path("tmp")
            dir.mkdir(exist_ok=True)
            if not Path("tmp/" + outName).exists():
                opre = OntologyPreprocessor(self.loadedYaml.get("owl_input_ontology_file"), "tmp/" + outName)
                opre.run()
            self.loadedYaml["owl_input_ontology_file"] = outName
            self.loadedYaml["owl_ontology_repository"] = "tmp/"
        if self.loadedYaml.get("mode") == 'cli':
            c2o = Cli2Owl(self.loadedYaml)
            c2o.run()
        if self.loadedYaml.get("ontology_preprocessor"):
            opost = OntologyPostprocessor(self.loadedYaml.get("owl_output_ontology_file"), self.loadedYaml.get("owl_output_ontology_file"),
                                  self.loadedYaml.get("owl_ontology_namespace"))
            self.loadedYaml["owl_output_ontology_file"] = opost.run()
        return self.loadedYaml.get("owl_output_ontology_file")


if __name__ == "__main__":
    import sys
    if len(sys.argv) <= 2:
        print("Missing parameter! Provide the path of a configuration file")
    else:
        x2o = X2Owl(sys.argv[1])
        x2o.run()
