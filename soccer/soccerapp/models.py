__author__ = 'yoav'

from django.db import models



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
                        'uefachampionsleague': {'country': 'intl', 'type': 'mix', 'rank': 1},}


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


class Team(models.Model):
    nami = models.CharField(max_length=200)

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

class Stadium(models.Model):
    title = models.CharField(max_length=100)
    max_size = models.IntegerField(null=True)
    construction_year = models.DateField(null=True)
    cords = models.ForeignKey(Cords, related_name='stadiums', null=True)##TODO adjust scraping to crate these objects

class Match(models.Model):
    league = models.ForeignKey(League, related_name='matches')
    home_team = models.ForeignKey(Team, related_name='home_matches')
    away_team = models.ForeignKey(Team, related_name='away_matches')
    match_date = models.DateField()
    round = models.IntegerField(default=0)
    weather = models.CharField(max_length=20, null=True)
    referee = models.ForeignKey(Referee, related_name='matches', null=True)
    stadium = models.ForeignKey(Stadium, null=True, related_name='matches')
    crowd = models.IntegerField(default=0)
    minutes_played = models.IntegerField()

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

    def get_match_type(self):
        if self.league.type == 'league':
            return 'regular'
        elif self.league.type == 'cup':
            return 'knockout'
        else:
            if self.match.date.month >= 1:
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


class PlayerMatch(models.Model):
    player = models.ForeignKey(Player, related_name='matches')
    team = models.ForeignKey(TeamMatch, related_name='players')
    position = models.ForeignKey(Position)
    opening = models.BooleanField()
    enter_minute = models.IntegerField(null=True)
    exit_minute = models.IntegerField(null=True)
    yellow_cards = models.IntegerField(null=True)## TODO something not working with the cards parsing :(
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