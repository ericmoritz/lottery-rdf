"""
This is an alternative approach to my sqllite3
in memory database.

I first convert the lottery data into RDF statements
then store those into an in-memory database
"""
from dateutil.parser import parse as parse_date_date_util
from dateutil import tz
import requests
import isodate
from lxml import etree
from time import time
from datetime import datetime, time as dtime
from rdflib import Namespace, Graph, Literal, URIRef
from urllib import quote
from collections import namedtuple

goodrelationsNS = Namespace("http://purl.org/goodrelations/v1#")
lotteryNS = Namespace("http://api.gannett.com/ontologies/lottery#")
schemaOrgNS = Namespace("http://schema.org/")

Config = namedtuple("Config", ["lottery_irl"])

# This is the timezone of the lottery data
est = tz.gettz('America/New_York')


## Public
def load_data():
    return None # Todo

def load_graph(config):
    apiNS = Namespace(config.lottery_irl)
    return _xml_to_graph(*_download_all(apiNS))

def dump(config, filename):
    triples = load_graph(config)
    g = _rdflib_import(Graph(), triples)
    with open(filename, "w") as f:
        f.write(g.serialize())


def _download_all(apiNS):
    return (
        _download_states_xml(apiNS),
        _download_games_xml(apiNS),
        _download_jackpot_xml(apiNS),
        _download_results_xml(apiNS),
    )

###===================================================================
### Queries
###===================================================================

###===================================================================
### Utils
###===================================================================
def tca(accum, func, *args, **kwargs):
    start = time()
    result = func(*args, **kwargs)
    accum.append((time() - start) * 1000)
    return result


def tc(func, *args, **kwargs):
    start = time()
    result = func(*args, **kwargs)
    return (time() - start, result)


"""
def benchmark(n):
    import pickle

    stats = {
        "shape_data": [],
        "games_by_state_key": [],
        "top_games": [],
        "set_cache": [],
        "get_cache": [],
        "pickle_size": [],
    }


    relations = load_relations()

    for i in range(n):
        conn = init()

        tca(stats['shape_data'], _import_relations, conn, relations)
        tca(stats['set_cache'], cache.set, "__benchmark__", relations, 30)
        tca(stats['get_cache'], cache.get, "__benchmark__", relations)

        stats['pickle_size'].append(len(pickle.dumps(relations)))

        tca(stats['top_games'], top_games_sql, conn, 5)

        # sample games_by_state_key by picking a random state from the
        # states relation
        state_id = random.choice(relations['states'])['id']
        tca(stats['games_by_state_key'], games_by_state_key_sql, conn, state_id)


    return {key:summarize(stats[key]) for key in stats}
"""

def percentile(sorted_stats, pct):
    size = len(sorted_stats)
    idx = int(size * (pct / 100.0)) - 1
    return sorted_stats[idx]


def summarize(stat):
    """Get the mean, and the quartile"""
    size = len(stat)
    mean = sum(stat) / size

    sorted_stat = sorted(stat)
    Percentile = [
        (pct, percentile(sorted_stat, pct))
        for pct in [50, 75, 95, 99]]

    return {"mean": mean,
            "percentile": Percentile}


def _download_states_xml(apiNS):
    url = str(apiNS["all_states_info.xml"])
    resp = requests.get(url)
    assert resp.status_code == 200
    return resp.content


def _download_games_xml(apiNS):
    url = str(apiNS["all_games_info.xml"])
    resp = requests.get(url)
    assert resp.status_code == 200
    return resp.content

def _download_jackpot_xml(apiNS):
    url = str(apiNS["all_jackpots.xml"])
    resp = requests.get(url)
    assert resp.status_code == 200
    return resp.content


def _download_results_xml(apiNS):
    url = str(apiNS["all_results.xml"])
    resp = requests.get(url)
    assert resp.status_code == 200
    return resp.content



def _draw_time(draw_time_str):
    """The lottery vendor's timezone math is wonky.  We've seen a draw
time of 25:00 for games who's timezone is -5 and the local draw time is
20:00

To fix that, I'm turning 25:00 into 01:00 EST"""
    hour, minute = int(draw_time_str[:2]), int(draw_time_str[2:])
    hour = hour % 24

    # adjust hours in case they give me more than 59 minutes
    extra_hours = minute / 60
    hour = hour + extra_hours

    # remove hours from the minutes
    minute = minute % 60

    return dtime(hour, minute)


def _map_game(game_row, result_row, next_jackpot_row, state_game_rows, game_day_rows):
    draw_time = _draw_time(game_row['draw_time'])
    ret = {
        u"key": game_row['id'],
        u"name": game_row['name'],
        u"states": [s['state_id'] for s in state_game_rows],
        u"draw_time": draw_time,
        u"days": [False] * 7,
    }
    if result_row:
        date = result_row['date']
        time = draw_time
        ret[u"update_time"] = result_row['update_time']
        ret[u"lastdraw"] = {
            u"date": datetime(date.year, date.month, date.day,
                              time.hour, time.minute, tzinfo=est),
            u"numbers": result_row['number_str'],
            u"number_list": result_row['numbers'].split(","),
            u"bonus_name": result_row['bonus_name'],
            u"bonus_number": result_row['bonus_number'],
        }

    if next_jackpot_row:
        date = next_jackpot_row['date']
        time = draw_time

        ret[u"nextdraw"] = {
            u"date": datetime(date.year, date.month, date.day,
                              time.hour, time.minute, tzinfo=est),
            u"jackpot": next_jackpot_row['amount'],
        }

    ret["draw_count"] = len(game_day_rows)

    for game_day in game_day_rows:
        idx = game_day['day']
        ret['days'][idx] = True

    return ret


def _extract_text(parent, tagname):
    return parent.find(tagname).text


###-------------------------------------------------------------------
### Namespaces and IRI generators
###-------------------------------------------------------------------

def _day_iri(day):
    DAY_IRIS = {
        "SUN": goodrelationsNS.Sunday,
        "MON": goodrelationsNS.Monday,
        "TUE": goodrelationsNS.Tuesday,
        "WED": goodrelationsNS.Wednesday,
        "THU": goodrelationsNS.Thursday,
        "FRI": goodrelationsNS.Friday,
        "SAT": goodrelationsNS.Saturday,
    }
    return DAY_IRIS[day]


def _doc_iri(iri):
    return URIRef(u"#" + quote(iri))


def _state_iri(state_id):
    return _doc_iri(u"state/{0}".format(state_id))


def _country_iri(country_name):
    return _doc_iri(u"country/{0}".format(country_name.lower()))


def _game_iri(gameId):
    return _doc_iri(u"com.lottostrategies/game/{0}".format(gameId.lower()))

def _jackpots_iri(gameId):
    return _doc_iri(u"com.lottostrategies/game/{0}/jackpots".format(gameId.lower()))

def _jackpot_iri(game_id, isodate):
    return _doc_iri(
        u'com.lottostrategies/game/{game_id}/jackpot/{isodate}'.format(
            game_id=game_id.lower(),
            isodate=isodate,
        )
    )

# Declared Properties
hasCountry   = lotteryNS.hasCountry
hasState     = lotteryNS.hasState
hasDrawDay   = lotteryNS.hasDrawDay
hasJackpots  = lotteryNS.hasJackpots
hasNext      = goodrelationsNS.hasNext
hasPrevious  = goodrelationsNS.hasPrevious
nameProp     = schemaOrgNS.name
websiteProp  = lotteryNS.website
stateIdProp  = lotteryNS.stateId
gameIdProp   = lotteryNS.gameId
drawTimeProp = lotteryNS.drawTime
quantityProp = lotteryNS.quantity
dateProp     = lotteryNS.date

###-------------------------------------------------------------------
### XML to Graph generation
###-------------------------------------------------------------------
# XSLT may be better suited to transforming XML into RDF... but you
# go with what you know.

def _xml_to_graph(states_xml, games_xml, jackpot_xml, results_xml):
    graph = _graph()
    _state_graph(graph, states_xml)
    _game_graph(graph, games_xml)
    _jackpots_graph(graph, jackpot_xml)
    _result_graph(graph, results_xml)
    return graph


def _state_graph(graph, xml_src):
    et = etree.fromstring(xml_src)
    for state_el in et.iterfind("state"):
        country_name = _extract_text(state_el, "country")
        state_name = _extract_text(state_el, "state_name")
        website = _extract_text(state_el, "website")

        state_id = _extract_text(state_el, "state_id")
        state_iri = _state_iri(state_id)
        country_iri = _country_iri(country_name.lower())

        # Give the state a stateId, name and website
        _state(graph, state_iri, nameProp, _literal(state_name))
        _state(graph, state_iri, websiteProp, _literal(website))
        _state(graph, state_iri, stateIdProp, _literal(state_id))

        # give the state a country
        _state(graph, state_iri, hasCountry, country_iri)
        # give the country a name
        _state(graph, country_iri, nameProp, _literal(country_name))

        # give the games states
        for game_el in state_el.iterfind("games/game"):
            game_iri = _game_iri(game_el.text)
            _state(graph, game_iri, hasState, state_iri)

    return graph


def _game_graph(graph, xml_src):
    et = etree.fromstring(xml_src)
    for game_el in et.iterfind("game"):
        draw_time =  _extract_text(game_el, "draw_time")
        game_id = _extract_text(game_el, "game_id").lower()
        game_name = _extract_text(game_el, "game_name")

        game_iri = _game_iri(game_id)

        # give the game a gameId and name
        _state(graph, game_iri, gameIdProp, _literal(game_id))
        _state(graph, game_iri, nameProp, _literal(game_name))

        # give the game a drawTime; # TODO make iso8601
        _state(graph, game_iri, drawTimeProp, _literal(draw_time)) 

        for draw_day_el in game_el.iterfind("draw_days/draw_day"):
            _state(graph, game_iri, hasDrawDay, _day_iri(draw_day_el.text))

    return graph


def _jackpots_graph(graph, xml_src):
    et = etree.fromstring(xml_src)
    seen_games = set()

    for state_el in et.iterfind("state_jackpots"):
        for game_el in state_el.iterfind("game_jackpot"):
            game_id = game_el.attrib['game_id']
            game_iri = _game_iri(game_id)
            jackpots_iri = _jackpots_iri(game_id)
            
            if game_id not in seen_games:
                for prop, el in [(hasNext, game_el.find("next_jackpot")), (hasPrevious, game_el.find("last_jackpot"))]:
                    if el is not None:
                        prefix = "next_" if prop is hasNext else "last_"
                        dateText = _extract_text(el, "{prefix}jp_date/{prefix}full_date".format(prefix=prefix))
                        dateStr = _iso(parse_date(dateText))

                        jackpot_iri = _jackpot_iri(game_id, dateStr)

                        amount = int(_extract_text(el, "{prefix}amount_value".format(prefix=prefix)))
                        name = _extract_text(el, "{prefix}amount_desc".format(prefix=prefix))
                        
                        # give the game a jackpots iri
                        _state(graph, game_iri, hasJackpots, jackpots_iri)

                        # give the appropriate prop the jackpot_iri
                        _state(graph, game_iri, prop, jackpot_iri)
                        
                        # give the jackpot a name and date
                        _state(graph, jackpot_iri, dateProp, _literal(dateStr))
                        _state(graph, jackpot_iri, nameProp, _literal(name))
                        _state(graph, jackpot_iri, quantityProp, _literal(amount))

                seen_games.add(game_id)
    return graph


def _result_graph(graph, xml_src):
    return graph # TODO
    relation = []
    et = etree.fromstring(xml_src)
    seen_games = set()

    for state_el in et.iterfind("state_results"):
        for game_el in state_el.iterfind("game_results"):
            game_id = game_el.attrib['game_id'].lower()
            if game_id not in seen_games:
                update_time = _iso(parse_date(game_el.attrib['update_time']))
                draw_date = _iso(parse_date(_extract_text(game_el, "draw_date/full_date")))
                numbers = ",".join((n.text
                                    for n in game_el.iterfind("numbers/number")))


                bonus_el = game_el.find("bonus")
                if bonus_el is not None:
                    bonus_name = _extract_text(bonus_el, "bonus_name")
                    bonus_number = _extract_text(bonus_el, "bonus_number")
                    

                relation.append({
                    "game_id": game_id,
                    "date": draw_date,
                    "update_time": update_time,
                    "number_str": _extract_text(game_el, "number_str"),
                    "numbers": numbers,
                    "bonus_name": bonus_name,
                    "bonus_number": bonus_number,
                    })
                seen_games.add(game_id)

    return relation


def _iso(dt):
    return isodate.datetime_isoformat(dt)


def parse_date(dtstr):
    return parse_date_date_util(dtstr).replace(tzinfo=est)


###===================================================================
### Graph manipulation functions
###===================================================================
def _rdflib_import(g, triples):
    g.bind("schema", schemaOrgNS)
    g.bind("lottery", lotteryNS)
    g.bind("gr", goodrelationsNS)

    for triple in triples:
        g.add(triple)
    return g

def _graph():
    return []


def _state(graph, subject, pred, obj):
    graph.append(_statement(subject, pred, obj))
    return graph


def _statement(s, p, o):
    return (s, p, o)
        

def _literal(val):
    return Literal(val)
