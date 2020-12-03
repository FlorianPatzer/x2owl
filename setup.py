import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="x2owl", # Replace with your own username
    version="0.0.1",
    author="Florian Patzer",
    author_email="florian.patzer@iosb.fraunhofer.de",
    description="X2Owl is a tool to configure mappings from arbitrary information sources (currently cli output parsing and OPC UA are supported) to OWL 2 using owlready2.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/FlorianPatzer/x2owl.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: LGPLV2+ License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)