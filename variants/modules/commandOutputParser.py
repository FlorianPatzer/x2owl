import re
import copy

class CommandOutputParser():

    def fillTree(self, template, co, tree):
        coTmp = ""

        for subTemplate in template:
            if not tree.get("objects"):
                tree["objects"] = []

            if subTemplate.get("regex") is not None:
                regexResult = re.search(r"" + subTemplate.get("regex"), co)

                if regexResult is None:
                    if subTemplate.get("default_value") is None:
                        continue
                    else:
                        tree["objects"].append({"value": subTemplate.get("default_value")})
                else:
                    tree["objects"].append({"value": regexResult.group(1)})


                if not subTemplate.get("regex_rewind") and regexResult:
                    co = co[regexResult.end(1):]
                    coTmp = co
            else:
                tree["objects"].append({"value": subTemplate.get("default_value")})

            tree["objects"][-1]["object"] = subTemplate.get("object")

            if subTemplate.get("objects") is not None:
                coTmp = self.fillTree(subTemplate["objects"], co, tree["objects"][-1])
        return coTmp

    def buildObjectTree(self, template, commandOutput, iterateSubtreeMapping):
        tree = {}
        if template.get("object") is not None:
            tree["object"] = template.get("object")

            if template.get("regex") is not None:
                regexResult = re.search(r"" + template["regex"], commandOutput)
                if regexResult is None:
                    if template.get("default_value") is not None:
                        tree["value"] = template["default_value"]
                    else:
                        raise Exception("No result found for object %s with regex %s and no default value is set.", (template.get("object"), template["regex"]))
                else:
                    tree["value"] = regexResult.group(1)

            if template.get("objects") is not None:
                tree["objects"] = []
                co = self.fillTree(template["objects"], commandOutput, tree)

                if iterateSubtreeMapping:
                    equalOutput = False
                    while not equalOutput:
                        tmpCo = self.fillTree(template["objects"], co, tree)
                        if tmpCo == co:
                            equalOutput = True
                        else:
                            co = tmpCo
        return tree

    def findObjectValue(self, objectTree, targetObject):
        if objectTree.get("object") == targetObject:
            return objectTree.get("value")

        if objectTree.get("objects"):
            for child in objectTree.get("objects"):
                res = self.findObjectValue(child, targetObject)
                if res:
                    return res
        return None