from rdflib import Namespace

goodrelations = goodrelationsNS = Namespace("http://purl.org/goodrelations/v1#")
lottery = lotteryNS = Namespace("http://vocabs-ld.org/vocabs/lottery#")
schema = schemaOrgNS = Namespace("http://schema.org/")
rdf = rdfNS = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
hydra = Namespace("http://www.w3.org/ns/hydra/core#")
xhtml = Namespace("http://www.w3.org/1999/xhtml#")


def bind_all_namespaces(graph):
    bindings = (
        ("gr", goodrelations), 
        ("lottery", lottery),
        ("schema", schema),
        ("hydra", hydra),
        ("xhtml", xhtml),        
    )
    for prefix, ns in bindings:
        graph.bind(prefix, ns)
    return graph
