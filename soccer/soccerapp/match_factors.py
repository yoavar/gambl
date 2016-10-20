__author__ = 'yoav'
from soccer.soccerapp.models import Match, Referee
import numpy as np

''' Class for managing and generating per match features and factors '''

class MatchFactors():

    def __init__(self, match):
        self.match = match

    def referee_factors(self):
        match_ref = self.match.referee
        referee_matches = Match.objects.filter(referee=match_ref)
        ref_avg_goals = np.mean([match.get_total_goals for match in referee_matches])
        ref_avg_fouls = np.mean([match.get_total_fouls for match in referee_matches])
        cards = [match.get_total_fouls for match in referee_matches]
        ref_avg_yellow_cards = np.mean([x[0] for x in cards])
        ref_avg_red_cards = np.mean([x[1] for x in cards])
        ref_avg_penatly_given = 0 ##TODO Need to scrap this from match events and find a place in models
    #
    # def weather_factors(self):
    #     rain_factor = None
    #     temp_factor = None
    #     humid_factor = None
    #     wind_factor = None
    #
    # def crowd_factors(self):
    #     crowd_factor = (max(stadium_crowd), actual_crowd)
    #
    # def date_factors(self):
    #     day_of_week = None
    #     hour_of_day = None
    #
    def tournament_factors(self):
        knockout_ind = 1 if self.match.get_knockout_ind()=='knockout' else 0
        round = None

