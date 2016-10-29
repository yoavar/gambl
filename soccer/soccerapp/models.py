__author__ = 'yoav'

from django.db import models
import pandas as pd
import urllib
import json
from django.conf import settings
from soccer.soccerapp.weather import WeatherWorker
import re
from django.db.models import Count

class ExternalData(models.Model):
    data_type = models.CharField(max_length=50)
    related_obj = models.CharField(max_length=50, null=True)
    data_info = models.CharField(max_length=50, null=True)
    data = models.CharField(max_length=10000, null=True)

class League(models.Model):
    nami = models.CharField(max_length=200)
    year = models.IntegerField()
    rank = models.IntegerField(default=1)#first/second/etc..
    type = models.CharField(max_length=50, null=True)##Cup/League
    country = models.CharField(max_length=200, null=True)
    total_round = models.IntegerField(null=True)

    league_meta_dict = {'laliga': {'country': 'spain', 'type': 'league', 'rank': 1},
                            'seriea': {'country': 'italy', 'type': 'league', 'rank': 1},
                            'bundesliga': {'country': 'germany', 'type': 'league', 'rank': 1},
                            'championship': {'country': 'england', 'type': 'league', 'rank': 2},
                        'premiereleague': {'country': 'england', 'type': 'league', 'rank': 1},
                        'coppaitalia': {'country': 'italy', 'type': 'cup', 'rank': 1},
                        'uefachampionsleague': {'country': 'intl', 'type': 'mix', 'rank': 1},
                        'uefacleague': {'country': 'intl', 'type': 'mix', 'rank': 1},
                        'ligue1': {'country': 'france', 'type': 'league', 'rank': 1},}

    class Meta():
        unique_together = ('nami', 'year')

    def get_pretty_name(self):
        return "{0} {1}".format(self.nami, self.year)

    def set_meta_features(self):
        meta_dict = self.league_meta_dict.get(self.nami, None)
        if meta_dict:
            self.country = meta_dict['country']
            self.type = meta_dict['type']
            self.rank = meta_dict['rank']
            self.save()

    def get_matches_per_team(self):
        return self.matches.all().values_list('teams__team__nami')\
            .annotate(cnt=Count('*')).values_list('cnt', 'teams__team__nami')

    def get_league_match_ids(self):
        external_name = '{0}-{1}'.format(self.nami, self.year)
        external_data = ExternalData.objects.filter(data_info='[\'who scored relevant matches ids\']',
                                                    related_obj=external_name)
        if len(external_data) == 0:
            print('no external data')
            return []
        else:
            match_ids = re.findall('\d+', external_data[0].data)
            if not match_ids:
                return []
            return match_ids

    @classmethod
    def crawl_who_score_matches(cls, match_ids):
        from soccerscraper.soccerscraper.spiders.whoscored_match import MatchSpider
        import scrapy
        from scrapy.crawler import CrawlerProcess
        process = CrawlerProcess({
            'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
        })
        process.crawl(MatchSpider, match_ids=match_ids)
        process.start()


class TeamManager(models.Manager):

    def get_or_create(self, team_nami):
        t = Team.objects.filter(nami=team_nami)
        if len(t) > 0:
            return t[0]
        else:
            t = Team(nami=team_nami)
            t.save()
            return t

class Team(models.Model):
    nami = models.CharField(max_length=200)

    objects = TeamManager()

class PlayerManager(models.Manager):
      pass
      # def scrape_users_by_pages(self, min_page, max_page):
      #     from soccerscraper.soccerscraper.spiders.whoscored import WhoScoredSpider
      #     from scrapy.crawler import CrawlerProcess
      #     scrap_obj = WhoScoredSpider(min_page, max_page)
      #     process = CrawlerProcess({
      #         'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
      #     })
      #     process.crawl(WhoScoredSpider, min_page=1, max_page=5)
      #     for p in process.start():
      #         new_player = Player(first_name=p['first_name'],
      #                             last_name=p['last_name'],
      #                             age=p['age'],
      #                             nationality=p['nationality'],
      #                             height=p['height'],
      #                             weight=p['weight'])
      #         new_player.save()

class Player(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    dob = models.DateField(null=True)
    nationality = models.CharField(max_length=50)
    strong_side = models.CharField(max_length=50, default="")
    height = models.IntegerField(null=True)
    weight = models.IntegerField(null=True)
    current_team = models.ForeignKey(Team, null=True)

    objects = PlayerManager()

    @classmethod
    class Meta:
        unique_together = ('first_name', 'last_name')

    def get_full_name(self):
        if self.first_name == self.last_name:
            return self.first_name

        full_name = "{0} {1}".format(self.first_name, self.last_name)
        return full_name

class Position(models.Model):
    title = models.CharField(max_length=50)
    full_title = models.CharField(max_length=200, null=True, default="")
    position_group = models.CharField(max_length=200, null=True, default="")


class Referee(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    nationality = models.CharField(max_length=50, null=True)

class Cords(models.Model):
    x = models.FloatField()
    y = models.FloatField()


class StadiumManager(models.Manager):
      stadiums_file_name = '~/gambl/data/stadiums_data.csv'

      def set_stadiums_cords_and_max_size(self):
          stadiums_df = pd.read_csv(self.stadiums_file_name)
          for ind, row in stadiums_df.iterrows():
              stadium_name = row['Stadium'].lower()
              s = Stadium.objects.filter(title=stadium_name)
              if len(s) > 0:
                  s = s[0]
              else:
                  s = Stadium(title=stadium_name)
              s_cords = Cords(x=row['Latitude'], y=row['Longitude'])
              s_cords.save()
              s.max_size=row['Capacity']
              s.cords=s_cords
              s.save()

class Stadium(models.Model):
    title = models.CharField(max_length=100)
    max_size = models.IntegerField(null=True)
    construction_year = models.DateField(null=True)
    cords = models.ForeignKey(Cords, related_name='stadiums', null=True)

    objects = StadiumManager()

    def guess_max_size(self):
        matches_crowd = self.matches.values_list('crowd', flat=True)
        self.max_size = max(matches_crowd)
        self.save()

class MatchManager(models.Manager):

    def set_matches_weather(self):
        weather_obj = WeatherWorker()
        for m in Match.objects.all():
            weather = weather_obj.get_match_weather(m)
            if weather:
                m.weather = weather
                m.save()

class Match(models.Model):
    league = models.ForeignKey(League, related_name='matches')
    home_team = models.ForeignKey(Team, related_name='home_matches')
    away_team = models.ForeignKey(Team, related_name='away_matches')
    match_date = models.DateTimeField()
    round = models.IntegerField(default=0)
    weather = models.CharField(max_length=200, null=True)
    referee = models.ForeignKey(Referee, related_name='matches', null=True)
    stadium = models.ForeignKey(Stadium, null=True, related_name='matches')
    crowd = models.IntegerField(default=0)
    minutes_played = models.IntegerField(default=90)

    objects = MatchManager()
    class Meta():
        unique_together = ('league', 'home_team', 'away_team', 'match_date')

    def get_pretty_name(self):
        p_name = "{0} - {1} - {2}".format(self.league.nami, self.home_team.nami, self.away_team.nami)
        return p_name

    def get_total_goals(self):
        team_matches = self.teams.all()
        total_goals = sum([x.goals_final for x in team_matches])
        return total_goals

    def get_total_fouls(self):
        match_players = PlayerMatch.objects.filter(team__in=[x for x in self.teams.all()])
        total_fouls = sum([x.fouls for x in match_players])
        return total_fouls

    def get_total_cards(self):
        match_players = PlayerMatch.objects.filter(team__in=[x for x in self.teams.all()])
        yellow_cards = sum([x.yellow_cards for x in match_players])
        red_cards = sum([x.red_cards for x in match_players])
        return yellow_cards, red_cards

    def get_total_penalties(self):
        match_players = PlayerMatch.objects.filter(team__in=[x for x in self.teams.all()])
        total_penatlies = sum([x.penalties for x in match_players])
        return total_penatlies

    def get_match_type(self):
        if self.league.type == 'league':
            return 'regular'
        elif self.league.type == 'cup':
            return 'knockout'
        else:
            if self.match_date.month >= 1:
                return 'knockout'
            else:
                return 'regular'


class TeamMatch(models.Model):
    team = models.ForeignKey(Team, related_name='matches')
    match = models.ForeignKey(Match, related_name='teams')
    goals_final = models.IntegerField()
    goals_half = models.IntegerField()
    formation = models.CharField(max_length=10, null=True)
    corners = models.IntegerField(null=True)
    fouls_commited = models.IntegerField(null=True)

    class Meta():
        unique_together = ('team', 'match')

class BetMatch(models.Model):
    match = models.ForeignKey(Match, related_name='bets')
    type = models.CharField(max_length=50)##ht_win, draw, aw_win, over_goals_d
    bookie_name = models.CharField(max_length=50, null=True)##Bet365, WilliamHill
    value = models.FloatField()

    class Meta():
        unique_together = ('match', 'type', 'bookie_name')

class PlayerMatch(models.Model):
    player = models.ForeignKey(Player, related_name='matches')
    team = models.ForeignKey(TeamMatch, related_name='players')
    position = models.ForeignKey(Position)
    opening = models.BooleanField()
    enter_minute = models.IntegerField(null=True)
    exit_minute = models.IntegerField(null=True)
    yellow_cards = models.IntegerField(null=True)
    red_cards = models.IntegerField(null=True)
    goals = models.IntegerField(null=True)
    assists = models.IntegerField(null=True)
    passes = models.IntegerField(null=True)
    shots = models.IntegerField(null=True)
    shots_on_target = models.IntegerField(null=True)
    touches = models.IntegerField(null=True)
    fouls = models.IntegerField(null=True)
    penalties = models.IntegerField(null=True)

    class Meta():
        unique_together = ('player', 'team')

    def get_minutes_played(self):
        last_m = self.exit_minute or 0
        first_m = self.enter_minute or 0
        return last_m - first_m

class TeamRank(models.Model):
    date = models.DateField()
    team = models.ForeignKey(Team)
    rank = models.IntegerField()
    league = models.ForeignKey(League)

class Transaction(models.Model):
    player = models.ForeignKey(Player)
    price = models.IntegerField()
    sell_team = models.ForeignKey(Team, related_name='sell_transactions')
    buy_team = models.ForeignKey(Team, related_name='buy_transactions')
    date = models.DateField()
