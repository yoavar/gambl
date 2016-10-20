__author__ = 'yoav'

from scrapy.spider import BaseSpider, Spider
from scrapy.selector import HtmlXPathSelector
import os
import re
from soccerscraper.items import PlayerMeta
from scrapy_djangoitem import DjangoItem
from soccerscraper.pipelines import PlayerPipeline, MatchPipeline, LeaguePipeline
import json
from collections import defaultdict

import django
django.setup()

from soccer.soccerapp.models import Player, Match
# ---scrape this https://www.whoscored.com/Players/8484  -- by player

class PlayerItem(DjangoItem):
    django_model = Player


class PlayerSpider(Spider):
    name = 'player_spider'
    base_url = 'https://www.whoscored.com/Players/'

    custom_settings = {'CONCURRENT_REQUESTS_PER_DOMAIN': 4, 'DOWNLOAD_DELAY': 0.5}
    def __init__(self, min_page, max_page):
        self.playerpipeline = PlayerPipeline()
        self.start_urls = []
        for i in range(int(min_page), int(max_page)):
            self.start_urls.append(os.path.join(self.base_url, str(i)))

    def parse(self, res):
       item = {}
       player_info = res.xpath('//div[@class="player-info"]')
       nami = player_info.xpath('.//div//div[@class="home"]//dl//dd//text()').extract()
       if len(nami) == 0:
           return None
       else:
           item['nami'] = nami[0]
       player_chars = player_info.xpath('.//div//div[@class="away"]//dl')
       for c in player_chars:
           c_type = c.xpath('.//dt/text()').extract()[0]
           if c_type == "Age:":
               item['dob'] = c.xpath('.//dd//i/text()').extract()[0]
           elif c_type == 'Height:':
               item['height'] = c.xpath('.//dd/text()').extract()[0]
           elif c_type == 'Weight:':
               item['weight'] = c.xpath('.//dd/text()').extract()[0]
           elif c_type == 'Nationality:':
               item['nationality'] = c.xpath('.//span//text()').extract()[0].replace(u'\r', '').replace(u'\n', '').replace(' ','').lower()

       t = self.playerpipeline.process_item(item)

# scrapy crawl match_spider  -a min_page=10000 -a max_page=10009
class LeagueSpider(Spider):
    league_pipeline = LeaguePipeline()
    name = 'league_spider'

    def __init__(self):
        self.start_urls = ['https://www.whoscored.com']

    def parse(self, res):
        pop_tournaments = res.xpath('//ul[@id="popular-tournaments-list"]//li')
        for tour in pop_tournaments:
            nami = tour.xpath('.//a//text()').extract()[0].lower()
            country = tour.xpath('.//a//@title').extract()[0].lower()
            self.league_pipeline.process_item(nami, country)

class MatchSpider(Spider):
    match_pipeline = MatchPipeline()
    name = 'match_spider'
    base_url = 'https://www.whoscored.com/matches/'
    def __init__(self, min_page, max_page):
        # self.matchpipeline = MatchPipeline()
        self.start_urls = []
        for i in range(int(min_page), int(max_page)):
            self.start_urls.append(os.path.join(self.base_url, "{0}/live".format(str(i))))

    def parse(self, res):
        league = self.get_league_item(res)
        live_match_div = res.xpath('//div[@id="live-match"]')
        if live_match_div:
            match_details = self.get_match_details(res, live_match_div)
            if match_details:
                match_details.update(league)
                self.match_pipeline.process_item(match_details)

    def get_match_details_2(self, response):
        ##Where the page has live details but not all nice java 1137383
        rc = response.xpath('//div[@class="region rc"]')


    def get_match_details(self, res, live_match_div):
        ress = r'matchCentreData = (.*);'
        match_center = json.loads(re.findall(ress, res.text)[0])
        if match_center is None:
            return {}
        match_details = defaultdict(defaultdict)
        match_details['home_team_name'] = match_center['home']['name']
        match_details['away_team_name'] = match_center['away']['name']
        match_details['date'] = match_center['startDate']
        match_details['half_score'] = match_center['htScore']
        match_details['final_score'] = match_center['score']
        match_details['weather'] = match_center['weatherCode']
        match_details['referee'] = match_center['refereeName']
        match_details['attendance'] = match_center['attendance']
        match_details['stadium'] = match_center['venueName']
        match_details['minutes_played'] = match_center['maxMinute']
        for team in ['home',  'away']:
            cur_team = match_center.get(team, None)
            if cur_team is None:
                return {}
            match_details[team]['team_formation'] = cur_team['formations'][0]['formationId']
            match_details[team]['name'] = cur_team['name']
            match_details[team]['fouls_commited'] = sum(cur_team['stats']['foulsCommited'].values())
            match_details[team]['corners'] = sum(cur_team['stats'].get('cornersTotal', {}).values())

            players = []
            team_players = match_center[team]['players']
            events_dict = self.get_events_dict(cur_team['incidentEvents'])
            subs_positions_dict = {}
            for player in team_players:
                player_dict = {}
                player_dict['name'] = player['name']
                player_dict['player_id'] = player['playerId']
                player_dict['opening'] = player.get('isFirstEleven', False)

                player_dict['minute_exited'] = player.get('subbedOutExpandedMinute', None)
                if player_dict['minute_exited']:
                    subs_positions_dict['subbedInPlayerId'] = player['position']
                player_dict['minute_entered'] = player.get('subbedInExpandedMinute', None)
                if player_dict['minute_entered']:
                   player_dict['position'] = subs_positions_dict.get(player_dict['player_id'], None)
                else:
                    player_dict['position'] = player['position']##What positions are they?
                player_dict['passes'] = sum(player['stats'].get('passesTotal' , {}).values())
                player_dict['touches'] = sum(player['stats'].get('touches', {}).values())
                player_dict['fouls'] = sum(player['stats'].get('foulsCommited', {}).values())
                player_dict['shots'] = sum(player['stats'].get('shotsTotal', {}).values())
                player_dict['shots_on_target'] = sum(player['stats'].get('shotsOnTarget', {}).values())
                player_dict['assits'] = sum(player['stats'].get('assits', {}).values())
                player_dict['goals'] = sum(events_dict['goals'].get(player_dict['player_id'], []))
                player_dict['yellow_cards'] = sum(events_dict['yellow'].get(player_dict['player_id'], []))
                player_dict['red_cards'] = sum(events_dict['red'].get(player_dict['player_id'], []))
                player_dict['penalties'] = sum(events_dict['penalties'].get(player_dict['player_id'], []))
                players.append(player_dict)
            match_details[team]['players'] = players

        return match_details

    def get_events_dict(self, events):
        events_dict = {'goals': defaultdict(list), 'red': defaultdict(list), 'yellow': defaultdict(list),
                       'penalties': defaultdict(list)}
        for event in events:
            event_type = event['type']['displayName']
            if event_type == 'Goal':
               events_dict['goals'][event['playerId']].append(1)
            if event_type == 'Card':
                card_type = event['cardType']['displayName'].lower()
                if card_type == 'secondyellow':
                    card_type = 'yellow'
                events_dict[card_type][event['playerId']].append(1)
            qualies = event.get('qualifiers', [])
            for q in qualies:
                q_type = q['type']['displayName']
                if q_type == 'Penalty':
                    events_dict['penalties'][event['playerId'].append(1)]
        return events_dict

    def get_league_item(self, res):
        item = {}
        league_name, league_year = self.get_league(res.xpath('//div[@id="breadcrumb-nav"]'))
        item['league_name'] = league_name
        item['league_year'] = league_year
        return item

    def get_league(self, league_span):
        league_str = league_span.xpath('.//a/text()').extract()
        if len(league_str) > 0:
            league = league_str[0].split("-")
            nami = league[0].replace(" ", "").strip()
            year = league[1].split('/')[0].strip()
            return nami.lower(), year
        else:
            return None, None



