from rdflib import Graph
from lottery_rdf.namespaces import xhtml, lottery, hydra, rdf, bind_all_namespaces
from itertools import groupby


def viewing_lottery_summary(input_graph, index_iri):
    out_g = bind_all_namespaces(Graph())

    _all_jackpots(input_graph, out_g)
    _all_states(input_graph, out_g, index_iri)

    return out_g


def viewing_state_lottery(input_graph, state_iri, index_iri):
    out_g = bind_all_namespaces(Graph())

    #_all_states(input_graph, out_g, index_iri)
    _all_jackpots(
        input_graph, 
        out_g,
        state_iri=state_iri
    )

    return out_g


def _all_jackpots(input_graph, out_g, state_iri=None):
    if state_iri:
        extra_where = """
            ?game_s lottery:hasState <{state_iri}>
        """.format(state_iri=state_iri)
    else:
        extra_where = ""

    result = input_graph.query("""
    SELECT 
        ?game_s ?game_p ?game_o 
        ?jackpot_s ?jackpot_p ?jackpot_o
        ?state_iri 
    {{
       ?game_s rdf:type lottery:Game ;
           ?game_p ?game_o ;
           lottery:hasNext ?jackpot_s .

       ?jackpot_s ?jackpot_p ?jackpot_o .
       {extra_where} 
    }}""".format(extra_where=extra_where))

    for row in result:
        out_g.add((row.game_s, row.game_p, row.game_o))
        out_g.add((row.jackpot_s, row.jackpot_p, row.jackpot_o))


def _all_states(input_graph, out_g, index_iri):
    states = input_graph.query("""
    SELECT
      ?s ?p ?o
    {
      ?s rdf:type lottery:State .
      ?s ?p ?o .
    }
    """)
    for state_iri, state in groupby(states, key=lambda row:row.s):
        out_g.add((index_iri, lottery.viewState, state_iri))
        out_g.add((state_iri, xhtml.start, index_iri))

        for row in state:
            out_g.add(row)

    out_g.add((lottery.viewState, rdf.type, hydra.Link))
    out_g.add((xhtml.start, rdf.type, hydra.Link))

    return out_g
