__author__ = 'yoav'
from soccer.soccerapp.models import Match, Referee
import numpy as np
import json

''' Class for managing and generating per match features and factors '''

class MetaFactors():

    def __init__(self, match):
        self.match = match

    def get_all_factors(self):
        factors = {}
        factors.update(self.referee_factors())
        factors.update(self.weather_factors())
        factors.update(self.crowd_factors())
        factors.update(self.date_factors())
        factors.update(self.tournament_factors())
        return factors

    def referee_factors(self):
        match_ref = self.match.referee
        referee_matches = Match.objects.filter(referee=match_ref, match_date__lt=self.match.match_date)
        ref_avg_goals = np.mean([match.get_total_goals() for match in referee_matches])
        ref_avg_fouls = np.mean([match.get_total_fouls() for match in referee_matches])
        cards = [match.get_total_cards() for match in referee_matches]
        ref_avg_yellow_cards = np.mean([x[0] for x in cards])
        ref_avg_red_cards = np.mean([x[1] for x in cards])
        ref_avg_penalties = np.mean([match.get_total_penalties() for match in referee_matches])
        return {'ref_avg_goals':ref_avg_goals,
                'ref_avg_fouls': ref_avg_fouls,
                'ref_avg_yellow_cards': ref_avg_yellow_cards,
                'ref_avg_red_cards': ref_avg_red_cards,
                'ref_avg_penalties': ref_avg_penalties}
    #
    def weather_factors(self):
        weather = self.match.weather
        weather_factors = {'rain': None, 'temp': None, 'humidity': None, 'wind': None}
        if not weather:
            return weather_factors
        else:
            try:
                weather = json.loads(weather)
            except json.JSONDecodeError:
                return weather_factors
            return weather

    def crowd_factors(self):
        factor = {'crowd_factor': None}
        if not self.match.crowd or not self.match.stadium.max_size:
            return factor
        crowd_factor = self.match.crowd / float(self.match.stadium.max_size)
        factor['crowd_factor'] = crowd_factor
        return factor

    def date_factors(self):
        day = self.match.match_date.weekday()
        hour = self.match.match_date.hour
        return {'day': day, 'hour': hour}

    def tournament_factors(self):
        knockout_ind = 1 if self.match.get_match_type()=='knockout' else 0
        return {'knockout_ind': knockout_ind}

