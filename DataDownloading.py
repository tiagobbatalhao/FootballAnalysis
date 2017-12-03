
import requests,re

months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

def choice_of_championships():
	championships = {}

	for year in range(2003,2018):
		for level in range(1,4):
			label = 'BRA_{:4d}_{:1d}'.format(year,level)
			if level==1:
				url_string = 'http://www.rsssfbrasil.com/tablesae/br{:4d}.htm'.format(year)
			else:
				url_string = 'http://www.rsssfbrasil.com/tablesae/br{:4d}l{:1d}.htm'.format(year,level)
			championships[label] = url_string
	return championships

def donwload_championship(url_string):
	page = requests.get(url_string)
	if page:
		page.encoding = 'utf-8'
		return page.text.split('\n')

class Team():
	def __init__(self,line):
		try:
			split = line.split(' - ')
			self.name = split[0].strip()
			split = split[1].split('(')
			self.name_long = split[0].strip()
			self.city = split[1].strip('()').strip()
		except IndexError:
			pass

def parse_championship(page):
	# line_types = ['blank','new_round','new_day','new_game']
	current_round = 0
	current_day = 0
	current_game = []
	games = []

	for line_raw in page:
		line = line_raw.strip('\n\t')
		if ' canc ' in line or 'cancelado' in line or 'abandoned' in line:
			continue
		if not line:
            # Line type is 'blank'
			if current_game:
				games.append((current_game,current_round,current_day))
			current_game = []
			current_round = 0
		else:
			if current_round==0:
				if current_game:
					games.append((current_game,current_round,current_day))
				current_game = []
				regexp = re.search('(Round )([0-9]*)',line)
				if regexp:
                    # Line type is 'new_round'
					current_round = int(regexp.group(2))
			else:
				if line[0]=='[' and line[1:4] in months:
                    # Line type is 'new_day'
					if current_game:
						games.append((current_game,current_round,current_day))
					current_game = []
					current_day = line.strip(' []\n\t')
				else:
					score = re.search('[0-9]+-[0-9]+',line)
					if score:
                        # Line type is 'new_game'
						if current_game:
							games.append((current_game,current_round,current_day))
						current_game = [line]
					else:
						if len(current_game):
							current_game.append(line)
	if current_game:
		games.append((current_game,current_round,current_day))
	current_game = []
	current_round = 0


	return games



def parse_championship_broken(page):
	current_round = 0
	current_day = None
	line_index = 0
	games = []

	while line_index < len(page):
		line = page[line_index]
		if not line:
			current_round = 0
			line_index += 1
		else:
			if current_round==0:
				regexp = re.search('(Round )([0-9]*)',line)
				if regexp:
					current_round = int(regexp.group(2))
				line_index += 1
			else:
				if line[0]=='[' and line[1:4] in months:
					current_day = line.strip('[]')
					line_index += 1
				# if line.strip()[0] in '[<' or ' canc ' in line or 'cancelled' in line:
				# 	print(line[:20])
				# 	line_index += 1
				else:
					score = re.search('[0-9]*-[0-9]*',line)
					if score:
						if score.group(0) == '0-0':
							games.append(Game(line,'',current_round,current_day))
							line_index += 1
						else:
							games.append(Game(line,page[line_index+1],current_round,current_day))
							line_index += 2
					else:
						line_index += 1
	return games

class Game():
	def __init__(self,game,current_round,current_day):
		self.round = current_round
		self.day = current_day
		self.extra_information = []
		self.goals_home = []
		self.goals_away = []
		if len(game)>=1:
			# pattern = '([\S]*)[\s]*([0-9]*)-([0-9]*)[\s]*([\S]*)[\s]*([\S]*)'
			score = re.search('([0-9]*)-([0-9]*)',game[0])
			try:
				groups = score.groups()
				self.score_home = int(groups[0])
				self.score_away = int(groups[1])
			except (IndexError,ValueError):
				pass
			span = score.span()
			self.team_home,extra = sanitize_teamname(game[0][:span[0]])
			self.team_away,extra = sanitize_teamname(game[0][span[1]:])
		if len(game)>=3:
			self.extra_information += game[2:]
		if len(game)>=2:
			# self.goal_timings_line = game[1]
			line = game[1].strip(' []')

			if self.score_home > 0 and self.score_away == 0:
				goals = line.split(',')
				self.goals_home = [Goal(x) for x in goals]
			elif self.score_home == 0 and self.score_away > 0:
				goals = line.split(',')
				self.goals_away = [Goal(x) for x in goals]
			elif self.score_home > 0 and self.score_away > 0:
				goals_home,goals_away = line.split(';')
				goals_home = goals_home.split(',')
				self.goals_home = [Goal(x) for x in goals_home]
				goals_away = goals_away.split(',')
				self.goals_away = [Goal(x) for x in goals_away]

			for k in range(1,len(self.goals_home)):
				if self.goals_home[k].player == '':
					self.goals_home[k].player = self.goals_home[k-1].player
			for k in range(1,len(self.goals_away)):
				if self.goals_away[k].player == '':
					self.goals_away[k].player = self.goals_away[k-1].player

def sanitize_teamname(name):
	team = name.strip(' ()[]\n\t')
	delimiters = ['(','[']
	while any([x in team for x in delimiters]):
		for delim in delimiters:
			if delim in team:
				index = team.index(delim)
				team = team[0:index].strip()
	team_index = name.index(team)
	extra = name[team_index+len(team):]
	return team.strip(),extra.strip(' ()[]')

class Goal():
	def __init__(self,line):
		try:
			split = line.split()
			self.minute = split[-1]
			self.player = ' '.join([x.strip() for x in split[:-1]])
		except IndexError:
			print(line)

def manual_parser():

	encodings = {}
	encodings['BRA1_2017'] = 'utf-8'
	encodings['BRA1_2016'] = 'iso-8859-1'
	encodings['BRA1_2015'] = 'iso-8859-1'
	encodings['BRA1_2013'] = 'iso-8859-1'
	encodings['BRA1_2012'] = 'iso-8859-1'
	encodings['BRA1_2011'] = 'iso-8859-1'
	encodings['BRA1_2010'] = 'iso-8859-1'
	encodings['BRA1_2009'] = 'iso-8859-1'
	encodings['BRA1_2008'] = 'iso-8859-1'
	encodings['BRA1_2007'] = 'iso-8859-1'
	encodings['BRA1_2006'] = 'iso-8859-1'
	encodings['BRA1_2005'] = 'iso-8859-1'
	encodings['BRA1_2004'] = 'iso-8859-1'
	encodings['BRA1_2003'] = 'iso-8859-1'

	encodings['BRA2_2017'] = 'utf-8'
	encodings['BRA2_2016'] = 'iso-8859-1'
	encodings['BRA2_2015'] = 'iso-8859-1'
	encodings['BRA2_2013'] = 'iso-8859-1'
	encodings['BRA2_2012'] = 'iso-8859-1'
	encodings['BRA2_2011'] = 'iso-8859-1'
	encodings['BRA2_2010'] = 'iso-8859-1'
	encodings['BRA2_2009'] = 'iso-8859-1'

	data = {}
	for label,method in encodings.items():
		with open('Data_html/'+label+'.htm','rb') as f:
			text = f.readlines()
		# text = '\n'.join([x.decode(method) for x in text])
		# lines = text.split('\n')
		# print(lines)
		lines = [x.decode(method) for x in text]
		data[label] = parse_championship(lines)

	return data

def check_data(data):
	for label,value in data.items():
		for rnd in range(1,39):
			games = [x for x in value if x[1]==rnd]

			if label[3]=='1' and int(label[-4:])>=2006 and len(games)!=10:
				print('{} R{} {}'.format(label,rnd,len(games)))
			if label[3]=='1' and int(label[-4:])==2005 and len(games)!=11:
				print('{} R{} {}'.format(label,rnd,len(games)))
			if label[3]=='1' and int(label[-4:]) in [2003,2004] and len(games)!=12:
				print('{} R{} {}'.format(label,rnd,len(games)))
			if label[3]=='2' and int(label[-4:])>=2006 and int(label[-4:])!=2016 and len(games)!=10:
				print('{} R{} {}'.format(label,rnd,len(games)))
