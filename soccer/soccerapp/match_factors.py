__author__ = 'yoav'

import pandas as pd
import numpy as np
import datetime
from soccer.soccerapp.models import Match
from soccer.soccerapp.meta_factors import MetaFactors
from soccer.soccerapp.team_ranking import TeamRanking

class MatchFactors():

    def __init__(self, match):
        self.match = match

    def get_match_meta_factors(self):
        meta_factors_obj = MetaFactors(self.match)
        meta_factors = meta_factors_obj.get_all_factors()
        return meta_factors

    def get_teams_rankings_factors(self):
        team_ranking_obj = TeamRanking()
        team_rankings = {}
        team_rankings['home_team'] = team_ranking_obj.get_team_ranking_factors(self.match.home_team, self.match.match_date)
        team_rankings['away_team'] = team_ranking_obj.get_team_ranking_factors(self.match.away_team, self.match.match_date)
        return team_rankings

