from setuptools import setup


setup(
    name="lottery_rdf",
    install_requires=[
        "lxml==3.3.1",
        "pytest==2.5.2",
        "pytest-flakes==0.2",
        "python-dateutil==2.2",
        "rdflib==4.1.0",
        "requests==2.2.1",
    ],
    packages=[
        "lottery_rdf",
    ]
)
