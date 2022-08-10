from flask.blueprints import Blueprint
from flask.helpers import make_response
from func import compare_runs, is_pb, convert_run, get_personal_best, generate_comparison, get_games_index
from models import *
from flask import render_template, redirect, url_for

routes = Blueprint('routes', __name__)

@routes.route('/')
def load_runs():
    run_output = get_games_index(get_pb=True)
    return render_template('home.html', runs=run_output)


@routes.route('/games')
def get_games():
    games = get_games_index(display_checks=False)
    return render_template('games.html', games=games)


@routes.route("/run/<runid>")
def get_run(runid=None):
    if runid is None:
        return "Invalid ID"
    run = RunModel.query.filter_by(url_id=runid).first()
    if run is None:
        return "Invalid ID"

    obj = convert_run(run)

    return render_template('run.html', run=obj, is_pb=is_pb(run))


@routes.route("/run/<runid>/splits")
def get_splits(runid=None):
    if runid is None:
        return "Invalid ID"
    run = RunModel.query.filter_by(url_id=runid).first()
    if run is None:
        return "Invalid ID"

    if run.splits is None:
        return "Invalid"

    splits = generate_comparison(run)
    response = make_response(splits)
    response.headers.set('Content-Type', 'application/octet-stream')
    response.headers.set('Content-Disposition', f'attachment; filename={run.url_id}.lss')

    return response


@routes.route('/<game_abv>')
def game(game_abv=None):
    if game_abv is None:
        return "Invalid ID"
    game = GameModel.query.filter_by(abbreviation=game_abv).first()
    if game is None:
        return "Invalid ID"

    obj = {
        'abv': game.abbreviation,
        'name': game.name,
        'categories': []
    }

    for x in CategoryModel.query.filter_by(held_game=game.id).order_by(CategoryModel.order_by):
        best_times = get_personal_best(x)
        times = []
        for run in best_times:
            if run is None:
                continue
            times.append(convert_run(run, game=game, category=x))
        
        obj['categories'].append({
            'order_by': x.order_by,
            'name': x.name,
            'abv':  x.abbreviation,
            'personal_best': times
        })

    return render_template('game.html', game=obj)


@routes.route('/<game_abv>/<category_abv>')
def category(game_abv=None, category_abv=None):
    if game_abv is None or category_abv is None:
        return "Invalid ID"
    game = GameModel.query.filter_by(abbreviation=game_abv).first()
    if game is None:
        return "Invalid ID"
    category = CategoryModel.query.filter_by(held_game=game.id, abbreviation=category_abv).first()
    if category is None:
        return "Invalid ID"

    best_times = get_personal_best(category)
    times = []
    for run in best_times:
        if run is None:
            continue
        times.append(convert_run(run, game=game, category=category))

    obj = {
        'name': category.name,
        'abv':  category.abbreviation,
        'filter': category.subcategory_filter,
        'personal_best': times
    }
    runs = RunModel.query.filter_by(category=category.id).order_by(RunModel.date.desc(), RunModel.time.asc())

    # This is really really dumb because obj['run_history'] can either be a dict or list. Should fix.
    list_of_pbs = []
    for x in obj['personal_best']:
        list_of_pbs.append(x['url_id'])
    if category.subcategory_filter:
        temp = {}
        for x in runs:
            if x.url_id not in list_of_pbs:
                if x.subcategory in temp:
                    temp[x.subcategory].append(convert_run(x))
                else:
                    temp.update({str(x.subcategory): []})
                    temp[x.subcategory].append(convert_run(x))
        
        obj['run_history'] = temp
    else:
        temp = []
        for x in runs:
            if x.url_id not in list_of_pbs:
                temp.append(convert_run(x))
        obj['run_history'] = temp

    return render_template('category.html', category=obj)


@routes.route('/<game_abv>/<category_abv>/barriers')
def category_minute_barriers(game_abv=None, category_abv=None):
    if game_abv is None or category_abv is None:
        return "Invalid ID"
    game = GameModel.query.filter_by(abbreviation=game_abv).first()
    if game is None:
        return "Invalid ID"
    category = CategoryModel.query.filter_by(held_game=game.id, abbreviation=category_abv).first()
    if category is None:
        return "Invalid ID"

    obj = {
        'name': category.name,
        'abv':  category.abbreviation,
        'filter': category.subcategory_filter
    }
    runs = RunModel.query.filter_by(category=category.id).order_by(RunModel.date.asc(), RunModel.time.desc())
    run_list = []
    if category.subcategory_filter:
        temp = {}
        for x in runs:
            if x.subcategory in temp:
                if x.time.minute not in temp[x.subcategory]['queried_barriers']:
                    run_list.append(x)
                    temp[x.subcategory]['queried_barriers'].append(x.time.minute)
            else:
                temp.update({str(x.subcategory): {}})
                temp[x.subcategory]['queried_barriers'] = [x.time.minute]
                run_list.append(x)
    else:
        queried_barriers = []
        for x in runs:
            if x.time.minute not in queried_barriers:
                run_list.append(x)
                queried_barriers.append(x.time.minute)

    run_list.reverse()
    # This is really really dumb because obj['run_history'] can either be a dict or list. Should fix.
    if category.subcategory_filter:
        temp = {}
        for x in run_list:
            if x.subcategory in temp:
                temp[x.subcategory].append(convert_run(x))
            else:
                temp.update({str(x.subcategory): []})
                temp[x.subcategory].append(convert_run(x))
        
        obj['run_history'] = temp
    else:
        temp = []
        for x in run_list:
            temp.append(convert_run(x))
        obj['run_history'] = temp

    return render_template('barriers.html', category=obj)


@routes.route('/<game_abv>/<category_abv>/pb')
def get_pb(game_abv=None, category_abv=None):
    if game_abv is None or category_abv is None:
        return "Invalid ID"
    game = GameModel.query.filter_by(abbreviation=game_abv).first()
    if game is None:
        return "Invalid ID"
    category = CategoryModel.query.filter_by(held_game=game.id, abbreviation=category_abv).first()
    if category is None:
        return "Invalid ID"

    best_times = get_personal_best(category)
    if len(best_times) == 0 or best_times[0] is None:
        return "No valid PB for category."
    else:
        return redirect(url_for("routes.get_run", runid=best_times[0].url_id))


@routes.route("/compare/<run1>")
def make_comparison(run1=None):
    run1 = RunModel.query.filter_by(url_id=run1).first()

    if run1 is None:
        return "Invalid ID"

    run_obj = convert_run(run1)
    if run_obj['splits'] is None:
        return "Run does not have splits attached."

    runs = RunModel.query.filter_by(category=run1.category).order_by(RunModel.date.desc(), RunModel.time.asc())
    category = CategoryModel.query.filter_by(id=run1.category).first()
    # TODO: put this into a function. It is being unnecessarily repeated three times now.
    if category.subcategory_filter:
        temp = {}
        for x in runs:
            if x.url_id is not run1.url_id and x.splits is not None:
                if x.subcategory in temp:
                    temp[x.subcategory].append(convert_run(x))
                else:
                    temp.update({str(x.subcategory): []})
                    temp[x.subcategory].append(convert_run(x))
        
        run_history = temp
    else:
        temp = []
        for x in runs:
            if x.url_id is not run1.url_id and x.splits is not None:
                temp.append(convert_run(x))
        run_history = temp

    return render_template("make_comparison.html", run1=convert_run(run1), run_history=run_history, category_filter=category.subcategory_filter)


@routes.route("/compare/<run1>/<run2>")
def compare_runs_pg(run1=None, run2=None):
    run1 = RunModel.query.filter_by(url_id=run1).first()
    run2 = RunModel.query.filter_by(url_id=run2).first()

    if run1 is None or run2 is None:
        return "Invalid ID"

    comparison = compare_runs(run1, run2)
    if comparison is None:
        return "One or more run(s) does not have a splits file associated with it, or the splits files do not match."

    return render_template("compare_run.html", run1=convert_run(run1), run2=convert_run(run2),
                            splits_comparison=compare_runs(run1, run2))
