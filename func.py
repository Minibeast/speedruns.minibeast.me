import datetime
from models import *
import private


def pb_rules(run : RunModel, category : CategoryModel = None) -> bool:
    if run.game == 1:
        if category is not None:
            runs = RunModel.query.filter_by(category=category.id)
            n64_found = False
            for x in runs:
                if x.subcategory == "N64":
                    n64_found = True
            if not n64_found:
                return True
        return "N64" in run.subcategory
    else:
        return True


def date_format(year : int, month : int, day : int) -> datetime.datetime:
    month = str(month)
    month = month.zfill(2)
    day = str(day)
    day = day.zfill(2)
    return datetime.datetime.fromisoformat(f"{year}-{month}-{day}")


def compare_time(time_1 : datetime.time, time_2 : datetime.time) -> bool:
    time_1_s = int(time_1.hour) * 3600
    time_2_s = int(time_2.hour) * 3600
    time_1_s += int(time_1.minute) * 60
    time_2_s += int(time_2.minute) * 60
    time_1_s += int(time_1.second)
    time_2_s += int(time_2.second)
    time_1_s += float(f".{time_1.microsecond}")
    time_2_s += float(f".{time_2.microsecond}")
    return time_1_s < time_2_s


def get_embed_url(url : str) -> str:
    if url is None:
        return None
    if "youtube" in url or "youtu.be" in url:
        video_id = url[-11:]
        return f"https://www.youtube-nocookie.com/embed/{video_id}"
    elif "twitch" in url:
        video_id = url.split("/")[4]
        return f"https://player.twitch.tv/?video={video_id}&parent={private.PARENT}&autoplay=false"
    else:
        return url


def get_personal_best(category : CategoryModel) -> list:
    if category.is_multiplayer:
        times = []
        for z in RunModel.query.filter_by(category=category.id).order_by(RunModel.time):
            found = False
            for a in times:
                if a['players'] == z.players:
                    found = True
                    if compare_time(z.time, a['run'].time) and pb_rules(z):
                        a['run'] = z
            if not found:
                times.append({
                    'players': z.players,
                    'run': z
                })
        output = []
        for x in times:
            output.append(x['run'])
        return output
    else:
        best_time = None
        for z in RunModel.query.filter_by(category=category.id):
            if best_time is None or (compare_time(z.time, best_time.time) and pb_rules(z)):
                best_time = z

        return [best_time]


def is_pb(run : RunModel) -> list:
    category = CategoryModel.query.filter_by(id=run.category).first()
    pb_list = get_personal_best(category)
    for x in pb_list:
        if run.players == x.players:
            if run.time == x.time and pb_rules(run, category=category):
                return [True, x.url_id]
            else:
                return [False, x.url_id]
    return [False, ""]


def check_valid_change(category : CategoryModel, check : int = 1) -> bool:
    if check == 1:
        runs = RunModel.query.filter_by(category=category.id, subcategory=None)
        return runs.count() == 0
    if check == 2:
        runs = RunModel.query.filter_by(category=category.id, players=None) 
        return runs.count() == 0


def convert_run(run : RunModel, category : CategoryModel = None, game : GameModel = None) -> dict:
    if run is None:
        return None

    timestring = datetime.time.strftime(run.time, '%H:%M:%S')
    datestring = date_format(run.date.year, run.date.month, run.date.day)

    if game is None:
        game = GameModel.query.filter_by(id=run.game).first()
    if category is None:
        category = CategoryModel.query.filter_by(id=run.category).first()

    if run.players is None or len(run.players) == 0 or not category.is_multiplayer:
        players = None
    else:
        players = ""
        for x in (run.players).split(","):
            players += x + ", "
        
        if len(players) > 0:
            players = players[:-2]
        
    video = []
    if run.video is not None:
        # I don't know how to use lambda...
        for x in (run.video).split(" "):
            video.append(get_embed_url(x))

    return {
        'url_id': run.url_id,
        'game_abv': game.abbreviation,
        'game_name': game.name,
        'category_name': category.name,
        'category_abv': category.abbreviation,
        'timestring': timestring,
        'video': video,
        'hasvideo': len(video) > 0,
        'subcategory': run.subcategory,
        'platform': run.platform,
        'date': datestring.strftime("%b %d, %Y"),
        'rssdate': datestring.strftime('%a, %d %b %Y'),
        'demos': run.demos,
        'splits': generate_preview_splits(run),
        'players': players
    }


def get_games_index(get_pb : bool = False, display_checks : bool = True) -> list:
    run_output = []
    for row in GameModel.query.order_by(GameModel.order_by):
        if row.show_on_home is False and display_checks:
            continue
        name = row.name
        abv = row.abbreviation

        obj = {
            'name': name,
            'abv': abv,
            'categories': []
        }

        for y in CategoryModel.query.filter_by(held_game=row.id).order_by(CategoryModel.order_by):
            if y.show_on_home is False and display_checks:
                continue
            
            times = []
            if get_pb:
                best_times = get_personal_best(y)
                for run in best_times:
                    if run is None:
                        continue
                    times.append(convert_run(run, game=row, category=y))
                
                if len(times) == 0 and display_checks:
                    continue

            obj['categories'].append({
                'name': y.name,
                'abv': y.abbreviation,
                'personal_best': times
            })
        
        run_output.append(obj)
    return run_output


def check_form(value : str) -> str:
    if len(value) == 0:
        return None
    else:
        return value


def generate_preview_splits(run : RunModel) -> list:
    if run.splits is None:
        return None

    split_lines = str(run.splits).split("|")
    data_list = []
    for x in split_lines:
        temp = []
        for y in x.split(","):
            temp.append(y)
        data_list.append(temp)

    splits = []
    total_time = datetime.datetime.combine(datetime.date.today(), datetime.time())
    for x in data_list:
        obj = {
            'name': x[0],
            'time': str(x[1])[:-2],
            'full_time': x[1],
            'time_obj': convert_time(x[1])
        }

        segment_datetime = datetime.datetime.combine(datetime.date.today(), obj['time_obj']) - total_time
        obj['segment_time_obj'] = (datetime.datetime.min + segment_datetime).time()
        obj['segment_time'] = datetime.datetime.strftime((datetime.datetime.min + segment_datetime), "%H:%M:%S.%f")[:-5]
        total_time += segment_datetime

        if "." not in obj['time']:
            obj['time'] = obj['full_time']
        splits.append(obj)
    return splits


def generate_comparison(run : RunModel) -> str:
    if run.splits is None:
        return None
    
    game = GameModel.query.filter_by(id=run.game).first()
    category = CategoryModel.query.filter_by(id=run.category).first()

    splits = generate_preview_splits(run)

    timingmethod = "RealTime"
    if game.use_game_time:
        timingmethod = "GameTime"

    output = f"""<?xml version="1.0" encoding="UTF-8"?>
<Run version="1.7.0">
    <GameIcon />
    <GameName>{game.name}</GameName>
    <CategoryName>{category.name}</CategoryName>
    <Metadata>
        <Run id="" />
        <Platform usesEmulator="False">
        </Platform>
        <Region>
        </Region>
        <Variables />
    </Metadata>
    <Offset>00:00:00</Offset>
    <AttemptCount>0</AttemptCount>
    <AttemptHistory />
    <Segments>
    """

    for x in splits:
        output += f"""<Segment>
            <Name>{x['name']}</Name>
            <Icon />
            <SplitTimes>
            <SplitTime name="Personal Best">
                <{timingmethod}>{x['full_time'].zfill(7)}</{timingmethod}>
            </SplitTime>
            </SplitTimes>
            <BestSegmentTime />
            <SegmentHistory />
        </Segment>
        """
    output += """</Segments>
    <AutoSplitterSettings />
</Run>
    """
    return output


def convert_time(time : str) -> datetime.time:
    dt_obj = datetime.datetime.strptime(time, "%H:%M:%S.%f")
    return datetime.time(hour=dt_obj.hour, minute=dt_obj.minute, second=dt_obj.second, microsecond=dt_obj.microsecond)


def compare_runs(run1 : RunModel, run2 : RunModel) -> dict:
    splits1 = generate_preview_splits(run1)
    splits2 = generate_preview_splits(run2)

    if splits1 is None or splits2 is None:
        return None

    if len(splits1) != len(splits2):
        return None

    i = 0
    while i < len(splits1):
        if splits1[i]['name'].lower() != splits2[i]['name'].lower():
            return None
        i+=1

    i = 0
    splits_db = []
    while i < len(splits1):
        splits_db.append({
            "split_info_1": splits1[i],
            "split_info_2": splits2[i],
            "is_gold": compare_time(splits1[i]['segment_time_obj'], splits2[i]['segment_time_obj'])})   
        i+=1

    return splits_db
