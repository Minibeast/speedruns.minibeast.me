from flask.blueprints import Blueprint
from flask.helpers import make_response
from werkzeug.datastructures import MultiDict
from func import convert_run
from models import *
from flask import redirect, request, render_template

feeds = Blueprint('feeds', __name__)


def parse_query_strings(args : MultiDict) -> list:
    game = args.get('game')
    category = args.get('category')

    if game is None and category is not None:
        return None

    if game is not None and category is not None:
        cat = CategoryModel.query.filter_by(abbreviation=category).first()
        game_model = GameModel.query.filter_by(abbreviation=game).first()

        return RunModel.query.filter_by(category=cat.id, game=game_model.id).order_by(RunModel.date.desc())
    elif game is not None:
        game_model = GameModel.query.filter_by(abbreviation=game).first()

        return RunModel.query.filter_by(game=game_model.id).order_by(RunModel.date.desc())
    elif category is not None:
        cat = CategoryModel.query.filter_by(abbreviation=category).first()

        return RunModel.query.filter_by(category=cat.id).order_by(RunModel.date.desc())
    else:
        return RunModel.query.order_by(RunModel.date.desc())


@feeds.route('/rss')
def rss_output():
    output = []
    runs = parse_query_strings(request.args)
    
    if runs is None:
        return redirect('/rss')

    i = 0
    while i < 10 and i < runs.count():
        output.append(convert_run(runs[i]))
        i += 1
    
    response = make_response(render_template('rss.xml', runs=output))
    response.headers.set('Content-Type', 'application/xml')

    return response


@feeds.route('/json')
def json_output():
    output = []
    
    runs = parse_query_strings(request.args)
    
    if runs is None:
        return redirect('/json')
    
    for x in runs:
        output.append(convert_run(x))
    response = make_response({
        'runs': output
    })
    response.headers.set('Content-Type', 'application/json')
    return response
