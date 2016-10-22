import sys
import MySQLdb
import hashlib
from scrapy.exceptions import DropItem
from scrapy.http import Request
import MySQLdb
import re

import django
django.setup()

from soccer.soccerapp.models import Match, Team, League, Player, Referee, TeamMatch, PlayerMatch, Position, Stadium
from dateutil.parser import parse


class PlayerPipeline(object):
    def __init__(self):
        pass

    def process_item(self, player_item):
        split_name = player_item['nami'].split(" ")
        if len(split_name) == 1:
            first_name = player_item['nami'].lower().strip()
            last_name = first_name
        else:
            first_name = split_name[0].lower().strip()
            last_name = split_name[1].lower().strip()
        dob = player_item.get('dob', None)
        dob = parse(dob) if dob else None
        height = re.findall(r'\d+', player_item.get('height', ''))
        weight = re.findall(r'\d+', player_item.get('weight', ''))
        height = int(height[0]) if height else 0
        weight = int(weight[0]) if weight else 0
        Player.objects.get_or_create(first_name=first_name, last_name=last_name,
                                     height=height, weight=weight
                                     , dob=dob, nationality=player_item.get('nationality', 0))

class LeaguePipeline(object):

    def __init__(self):
        pass

    def process_item(self, nami, country, year):
        League.objects.get_or_create(nami=nami, country=country, year=year, rank=1)


class MatchPipeline(object):

    def __init__(self):
        pass

    def process_item(self, item):
        match = self.create_match_item(item)
        home_team_match, away_team_match = self.create_team_match_items(match, item)
        self.create_player_match_items(item, home_team_match, away_team_match)

    def create_match_item(self, item):
        league = self.get_league(item['league_name'], item['league_year'])
        if not league:
            return None
        home_team = self.get_team(item['home_team_name'])
        if not home_team:
            return None
        away_team = self.get_team(item['away_team_name'])
        if not away_team:
            return None
        match_date = self.parse_date(item['date'])
        if not match_date:
            return None
        referee = self.get_referee(item['referee'])
        if not referee:
            return None
        minutes_played = item.get('minutes_played', None)
        if not minutes_played:
            return None
        stadium_obj = self.get_stadium(item.get('stadium', ''))

        attendance = item.get('attendance', 0)

        match = Match.objects.filter(league=league, home_team=home_team, away_team=away_team, match_date=match_date)
        if len(match) == 0:
            match = Match(league=league, home_team=home_team, away_team=away_team, match_date=match_date,
                              referee=referee, crowd=attendance, stadium=stadium_obj, minutes_played=minutes_played)
            match.save()
        else:
            match = match[0]
        return match

    def create_team_match_items(self, match, item):
        ht_goals_final, at_goals_final = self.get_teams_goals(item['final_score'])
        ht_goals_half, at_goals_half = self.get_teams_goals(item['half_score'])
        home_team_match = self.create_one_team_match(match, ht_goals_final, ht_goals_half, item['home'])
        away_team_match = self.create_one_team_match(match, at_goals_final, at_goals_half, item['away'])
        return home_team_match, away_team_match

    def create_one_team_match(self, match, goals_final, goals_half, team_item):
        formation = team_item.get('formation', "")
        corners = team_item.get('corners', 0)
        fouls = team_item.get('fouls_commited', 0)
        cur_team = self.get_team(team_item['name'])
        team_m = TeamMatch.objects.filter(team=cur_team, match=match)
        if len(team_m) == 0:
            team_match = TeamMatch(team=cur_team, match=match, goals_final=goals_final, goals_half=goals_half, formation=formation, corners=corners, fouls_commited=fouls)
            team_match.save()
        else:
            team_match = team_m[0]
        return team_match

    def create_player_match_items(self, item, ht_match, at_match):
        home_players = item['home']['players']
        away_players = item['away']['players']
        for p in home_players:
            self.create_one_player_match(ht_match, p)
        for p in away_players:
            self.create_one_player_match(at_match, p)

    def create_one_player_match(self, team_match, player_item):
        player = self.get_player_item(player_item['name'])
        enter_minute = 0 if player_item['opening'] else player_item['minute_entered']
        exit_minute = None if player_item['position'] == 'Sub' else player_item['minute_exited'] if player_item['minute_exited'] else team_match.match.minutes_played
        position = self.get_player_position(player_item['position'])
        if not position:
            return None
        player_match = PlayerMatch.objects.filter(player=player, team=team_match)
        if len(player_match) == 0:
            player_match = PlayerMatch(player=player, team=team_match, position=position, opening=player_item['opening'], enter_minute=enter_minute, exit_minute=exit_minute, yellow_cards=player_item['yellow_cards'], red_cards=player_item['red_cards'], goals=player_item['goals'], assists=player_item['assits'], passes=player_item['passes'], touches=player_item['touches'], shots=player_item['shots'], shots_on_target=player_item['shots_on_target'], fouls=player_item['fouls'], penalties=player_item['penalties'])

            player_match.save()


    def get_player_position(self, pos):
        if pos:
            pos, _ = Position.objects.get_or_create(title=pos)
        return pos

    def get_player_item(self, nami):
        split_name = nami.split(" ")
        if len(split_name) == 1:
            first_name = nami.lower().strip()
            last_name = nami.lower().strip()
        else:
            first_name = split_name[0].lower().strip()
            last_name = split_name[1].lower().strip()
        player = Player.objects.filter(first_name=first_name, last_name=last_name)
        if len(player) == 0:
            player = Player(first_name=first_name, last_name=last_name)
            player.save()
        else:
            player = player[0]
        return player

    def get_referee(self, referee):
        if not referee:
            return None
        split_ref = referee.split(" ")
        first_name = split_ref[0].lower().strip()
        last_name = split_ref[1].lower().strip()
        ref, _ = Referee.objects.get_or_create(first_name=first_name, last_name=last_name)
        return ref

    def get_teams_goals(self, score):
        broken_score = re.findall('\d+', score)
        if broken_score:##Maybe no half time score
            return broken_score[0], broken_score[1]
        else:
            return None, None

    def parse_date(self, date_str):
        if not date_str:
            return None
        return parse(date_str)

    def get_league(self, nami, year):
        if not nami or not year:
            return None
        nami = nami.lower().replace("'", "")
        league = League.objects.filter(nami=nami, year=year)
        if len(league) == 0:
            league = League(nami=nami, year=year)
            league.save()
        else:
            league = league[0]
        return league

    def get_team(self, nami):
        if not nami:
            return None
        nami = nami.lower().replace("'", "")
        team, _ = Team.objects.get_or_create(nami=nami)
        return team

    def get_stadium(self, stadium_name):
        s = Stadium.objects.filter(title=stadium_name.lower())
        if len(s) > 0:
            return s[0]
        else:
            s = Stadium(title=stadium_name.lower())
            s.save()
            return s

