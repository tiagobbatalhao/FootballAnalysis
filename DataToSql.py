import sqlite3
import os.path
import DataDownloading as donwload_module

months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
months = {name:k+1 for k,name in enumerate(months)}

def create_table_from_dict(database,table_name,columns):
    """
    Create a table from a dictionary containing column names and data types
    """
    command = u'CREATE TABLE ' + str(table_name) + u' ( '
    command += u' , '.join([str(column) + u' ' + str(typ) for column,typ in columns.items()])
    command += u' ) ; '
    try:
        database.execute(command)
        database.commit()
    except sqlite3.OperationalError as exception:
        print(exception)


def update_from_dict(database,table_name,dictionary,condition_dictionary):
    dic = {}
    dic.update({u'set_'+x : y for x,y in dictionary.items() if y is not None})
    dic.update({u'con_'+x : y for x,y in condition_dictionary.items() if y is not None})
    set_clause = u' , '.join([str(x[4:]) + u' = :' + str(x) for x,y in dic.items() if x[:3]=='set'])
    con_clause = u' AND '.join([str(x[4:]) + u' = :' + str(x) for x,y in dic.items() if x[:3]=='con'])
    command = u'UPDATE ' + str(table_name) + u' SET ' + str(set_clause) + u' WHERE ' + str(con_clause)
    try:
        database.execute(command,dic)
        database.commit()
    except sqlite3.OperationalError as exception:
        print(exception)

def insert_from_dict(database,table_name,dictionary):
    dic = {}
    dic.update({u'set_'+str(x) : y for x,y in dictionary.items() if y is not None})
    columns = u' , '.join([x[4:] for x in dic])
    values = u' , '.join([u':'+x for x in dic])
    command = u'INSERT INTO ' + str(table_name) + u' ( ' + str(columns) + u' ) VALUES ( ' + str(values) + u' );'
    try:
        database.execute(command,dic)
        database.commit()
    except sqlite3.OperationalError as exception:
        print(exception)


def _create_table_matches(database,table_name = u'matches'):
    columns = {}
    columns[u'match_id'] = u'VARCHAR(30) PRIMARY KEY'
    columns[u'championship'] = u'TEXT'
    columns[u'round'] = u'INTEGER'
    columns[u'day'] = u'DATE'
    columns[u'team_home'] = u'TEXT'
    columns[u'team_away'] = u'TEXT'
    columns[u'score_home'] = u'INTEGER'
    columns[u'score_away'] = u'INTEGER'
    create_table_from_dict(database,table_name,columns)

def _create_table_goals(database,table_name = u'goals'):
    columns = {}
    columns[u'goal_id'] = u'VARCHAR(30) PRIMARY KEY'
    columns[u'match_id'] = u'VARCHAR(30) NOT NULL'
    columns[u'home_away'] = u'TEXT'
    columns[u'minute'] = u'TEXT'
    columns[u'note'] = u'TEXT'
    columns[u'scoreafter_home'] = u'INTEGER'
    columns[u'scoreafter_away'] = u'INTEGER'
    create_table_from_dict(database,table_name,columns)

def main():
    folder = os.getcwd()
    database_filename = folder + '/FootballDatabase.sqlite'
    if not os.path.isfile(database_filename):
        database = sqlite3.Connection(database_filename)
        _create_table_matches(database)
        _create_table_goals(database)
    else:
        database = sqlite3.Connection(database_filename)

    for label,games in donwload_module.manual_parser().items():
        division = int(label[3])
        year = int(label[-4:])
        base_id = 'BRA{:01d}{:04d}'.format(division,year) +'{:03d}'
        championship_name = 'BRA_{:01d}_{:04d}'.format(division,year)
        save_championship(database,games,base_id,championship_name)

        #
        #     championship_name = 'BRA_{:04d}_1'.format(year)
        #
        #
        # # First Division
        # for year in range(2003,2018):
        #     url_string = 'http://www.rsssfbrasil.com/tablesae/br{:04d}.htm'.format(year)
        #     try:
        #         save_championship(database,url_string,base_id,championship_name)
        #     except:
        #         print('Problem with {:04d}'.format(year))




def save_championship(database,games,base_id,championship_name):
        games = [donwload_module.Game(*x) for x in games]
        for k,game in enumerate(games):
            idd = {'match_id': base_id.format(k)}
            update = convert_game_to_dict(game,2017)
            update['championship'] = championship_name
            try:
                insert_from_dict(database,'matches',idd)
            except sqlite3.IntegrityError:
                pass
            update_from_dict(database,'matches',update,idd)
            #
            # for goal in game.goals_home:


def convert_game_to_dict(game,year):
    game_dict = {}
    game_dict['round'] = int(game.round)
    month,day = game.day.split()
    game_dict['day'] = '{:04d}-{:02d}-{:02d}'.format(int(year),int(months[month]),int(day))
    game_dict['team_home'] = game.team_home
    game_dict['team_away'] = game.team_away
    if 'score_home' in vars(game):
        game_dict['score_home'] = int(game.score_home)
    if 'score_away' in vars(game):
        game_dict['score_away'] = int(game.score_away)
    return game_dict

# def goal_to_dict(goal)
