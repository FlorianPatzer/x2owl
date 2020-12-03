# X2OWL
X2Owl is a module, which can be used to configure and automate mappings from arbitrary information sources (currently cli output parsing and OPC UA are implemented) to OWL 2 using owlready2.

## Restrictions
A major issue is the lack of support of some OWL restrictions by the owlready2 package.
To build an ontology the package can handle, the _utils.ontologyPreprocessor.py_ is provided.
It additionally renames the properties with iri `[some_prefix]name` to `[some_prefix]hasName`, which otherwise would end up as an attribute `name`
in the domain resource, which conflicts with the existing attribute `name` each resource has.
the script _utils.ontologyPostprocessor.py_ rewinds the renaming.

Note that the assertions building on the unsupported OWL restrictions are not reintroduced.
