from flask.blueprints import Blueprint
from func import check_form, check_valid_change
from models import *
from flask import redirect, request, render_template
from flask_login import current_user, login_required
import datetime

management = Blueprint('management', __name__)

@management.route("/create_game", methods=["POST", "GET"])
@login_required
def create_game():
    if request.method == "POST":
        name = check_form(request.form['name'])
        abbreviation = check_form(request.form['abv'])
        order_by = int(check_form(request.form['order_by']))
        try:
            use_game_time = check_form(request.form['use_game_time']) == 'on'
        except KeyError:
            use_game_time = False

        try:
            show_on_home = check_form(request.form['show_on_home']) == 'on'
        except KeyError:
            show_on_home = False


        game = GameModel(name=name, abbreviation=abbreviation, order_by=order_by, use_game_time=use_game_time, show_on_home=show_on_home)
        db.session.add(game)
        db.session.commit()
        return redirect("/")
    elif request.method == "GET":
        games = GameModel.query.count()
        return render_template('management/create_game.html', order_by_num=games + 1)
    return redirect("/")


@management.route("/create_category", methods=["POST", "GET"])
@login_required
def create_category():
    if request.method == "POST":
        name = check_form(request.form['name'])
        abbreviation = check_form(request.form['abv'])
        held_game = check_form(request.form['game_input'])
        held_game = GameModel.query.filter_by(abbreviation=held_game).first()
        try:
            show_on_home = check_form(request.form['show_on_home']) == 'on'
        except KeyError:
            show_on_home = False
        try:
            filter_subcats = check_form(request.form['filter_subcats']) == 'on'
        except KeyError:
            filter_subcats = False

        try:
            is_multiplayer = check_form(request.form['is_multiplayer']) == 'on'
        except KeyError:
            is_multiplayer = False

        order_by = int(check_form(request.form['order_by']))

        category = CategoryModel(name=name, abbreviation=abbreviation, held_game=held_game.id, show_on_home=show_on_home, 
                                    order_by=order_by, subcategory_filter=filter_subcats, is_multiplayer=is_multiplayer)
        db.session.add(category)
        db.session.commit()
        return redirect("/")
    elif request.method == "GET":
        categories = CategoryModel.query.count()
        return render_template('management/create_category.html', games=GameModel.query, order_by_num=categories + 1)
    return redirect("/")


@management.route("/create_run", methods=["POST", "GET"])
@login_required
def create_run():
    if request.method == "POST":
        cat_input = check_form(request.form['cat_input'])
        category = CategoryModel.query.filter_by(id=cat_input).first()
        subcategory = check_form(request.form['subcategory'])
        if subcategory is None and category.subcategory_filter:
            return "Run must include a subcategory for the filter."
        game = GameModel.query.filter_by(id=category.held_game).first()
        time = datetime.time(hour=int(check_form(request.form['hours'])), minute=int(check_form(request.form['minutes'])), second=int(check_form(request.form['seconds'])))
        date = datetime.datetime.strptime(request.form['date'], "%Y-%m-%d")
        date = datetime.date(date.year, date.month, date.day)
        user = current_user.id
        video = check_form(request.form['video'])
        demos = check_form(request.form['demos'])
        platform = check_form(request.form['platform'])
        splits = check_form(request.form['splits'])
        players = check_form(request.form['players'])
        if players is None and category.is_multiplayer:
            return "Players must be completed for multiplayer categories."

        run = RunModel(game=game.id, category=category.id, time=time, user=user, video=video, 
                        subcategory=subcategory, platform=platform, date=date, demos=demos, splits=splits, players=players)
        
        run.set_url_id()

        db.session.add(run)
        db.session.commit()
        return redirect("/")
    elif request.method == "GET":
        output = []
        categories = CategoryModel.query
        for x in categories:
            game = GameModel.query.filter_by(id=x.held_game).first()
            output.append({
                'category_id': x.id,
                'name': f"{game.name} - {x.name}"
            })
        return render_template('management/create_run.html', categories=output)
    return redirect("/")


@management.route('/edit_game/<game_abv>', methods=["POST", "GET"])
@login_required
def edit_game(game_abv=None):
    if game_abv is None:
            return "Invalid ID"
    game = GameModel.query.filter_by(abbreviation=game_abv).first()
    if game is None:
        return "Invalid ID"

    if request.method == "POST":
        game.name = check_form(request.form['name'])
        game.abbreviation = check_form(request.form['abv'])
        game.order_by = int(check_form(request.form['order_by']))
        try:
            game.use_game_time = check_form(request.form['use_game_time']) == 'on'
        except KeyError:
            game.use_game_time = False

        try:
            game.show_on_home = check_form(request.form['show_on_home']) == 'on'
        except KeyError:
            game.show_on_home = False

        db.session.add(game)
        db.session.commit()
        return redirect("/")
    else:
        if game.use_game_time:
            use_game_time_value = 'true'
        else:
            use_game_time_value = 'false'
        
        if game.show_on_home:
            show_on_home_value = 'true'
        else:
            show_on_home_value = 'false'

        return render_template('management/edit_game.html', game=game, use_game_time_value=use_game_time_value, show_on_home_value=show_on_home_value)


@management.route('/edit_category/<game_abv>/<cat_abv>', methods=["POST", "GET"])
@login_required
def edit_category(game_abv=None, cat_abv=None):
    if cat_abv is None or game_abv is None:
            return "Invalid ID"
    game = GameModel.query.filter_by(abbreviation=game_abv).first()
    if game is None:
        return "Invalid ID"

    cat = CategoryModel.query.filter_by(abbreviation=cat_abv, held_game=game.id).first()
    if cat is None:
        return "Invalid ID"

    if request.method == "POST":
        try:
            filter_subcats = check_form(request.form['filter_subcats']) == 'on'
        except KeyError:
            filter_subcats = False

        try:
            is_multiplayer = check_form(request.form['is_multiplayer']) == 'on'
        except KeyError:
            is_multiplayer = False
        
        if filter_subcats:
            check = check_valid_change(cat)
            if not check:
                return "Invalid Change! Category includes runs without a subcategory variable!"
        if is_multiplayer:
            check = check_valid_change(cat, check=2)
            if not check:
                return "Invalid Change! Category includes runs without players!"

        cat.subcategory_filter = filter_subcats
        cat.is_multiplayer = is_multiplayer
        cat.name = check_form(request.form['name'])
        cat.abbreviation = check_form(request.form['abv'])
        held_game = check_form(request.form['game_input'])
        cat.held_game = GameModel.query.filter_by(abbreviation=held_game).first().id
        try:
            cat.show_on_home = check_form(request.form['show_on_home']) == 'on'
        except KeyError:
            cat.show_on_home = False
        cat.order_by = int(check_form(request.form['order_by']))

        db.session.add(cat)
        db.session.commit()
        return redirect("/")
    else:
        if cat.show_on_home:
            show_on_home_value = 'true'
        else:
            show_on_home_value = 'false'
        
        if cat.subcategory_filter:
            filter_subcats_value = 'true'
        else:
            filter_subcats_value = 'false'

        if cat.is_multiplayer:
            is_multiplayer_value = 'true'
        else:
            is_multiplayer_value = 'false'
        
        return render_template('management/edit_category.html', games=GameModel.query, cat=cat, show_on_home_value=show_on_home_value, filter_subcats_value=filter_subcats_value, is_multiplayer_value=is_multiplayer_value, game=game)


@management.route("/edit_run/<run_id>", methods=["POST", "GET"])
@login_required
def edit_run(run_id=None):
    if run_id is None:
            return "Invalid ID"
    run = RunModel.query.filter_by(url_id=run_id).first()
    if run is None:
        return "Invalid ID"

    if request.method == "POST":
        cat_input = check_form(request.form['cat_input'])
        category = CategoryModel.query.filter_by(id=cat_input).first()
        subcategory = check_form(request.form['subcategory'])
        players = check_form(request.form['players'])
        if subcategory is None and category.subcategory_filter:
            return "Run must include a subcategory for the filter."
        if players is None and category.is_multiplayer:
            return "Players must be completed for multiplayer categories."
        run.subcategory = subcategory
        run.players = players
        run.category = category.id
        run.game = GameModel.query.filter_by(id=category.held_game).first().id
        run.time = datetime.time(hour=int(check_form(request.form['hours'])), minute=int(check_form(request.form['minutes'])), second=int(check_form(request.form['seconds'])))
        date = datetime.datetime.strptime(check_form(request.form['date']), "%Y-%m-%d")
        run.date = datetime.date(date.year, date.month, date.day)
        run.user = current_user.id
        run.video = check_form(request.form['video'])
        run.demos = check_form(request.form['demos'])        
        run.platform = check_form(request.form['platform'])
        run.splits = check_form(request.form['splits'])

        db.session.add(run)
        db.session.commit()
        return redirect("/")
    elif request.method == "GET":
        output = []
        categories = CategoryModel.query
        for x in categories:
            game = GameModel.query.filter_by(id=x.held_game).first()
            output.append({
                'category_id': x.id,
                'name': f"{game.name} - {x.name}"
            })

        return render_template('management/edit_run.html', categories=output, run=run, date=f"{run.date.year}-{str(run.date.month).zfill(2)}-{str(run.date.day).zfill(2)}")
    return redirect("/")


@management.route("/delete_run/<run_id>")
@login_required
def delete_run(run_id=None):
    if run_id is None:
            return "Invalid ID"
    run = RunModel.query.filter_by(url_id=run_id).first()
    if run is None:
        return "Invalid ID"

    db.session.delete(run)
    db.session.commit()
    return redirect('/')


@management.route("/delete_category/<game_abv>/<cat_abv>")
@login_required
def delete_category(game_abv=None, cat_abv=None):
    if cat_abv is None or game_abv is None:
            return "Invalid ID"
    game = GameModel.query.filter_by(abbreviation=game_abv).first()
    if game is None:
        return "Invalid ID"
    cat = CategoryModel.query.filter_by(abbreviation=cat_abv, held_game=game.id).first()
    if cat is None:
        return "Invalid ID"
    for run in RunModel.query.filter_by(game=game.id, category=cat.id):
        db.session.delete(run)
    
    db.session.delete(cat)
    db.session.commit()
    return redirect('/')


@management.route("/delete_game/<game_abv>")
@login_required
def delete_game(game_abv=None):
    if game_abv is None:
            return "Invalid ID"
    game = GameModel.query.filter_by(abbreviation=game_abv).first()
    if game is None:
        return "Invalid ID"

    for run in RunModel.query.filter_by(game=game.id):
        db.session.delete(run)

    for category in CategoryModel.query.filter_by(held_game=game.id):
        db.session.delete(category)
    
    db.session.delete(game)
    db.session.commit()
    return redirect('/')
