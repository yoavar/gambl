__author__ = 'yoav'

from soccer.soccerapp.match_factors import MatchFactors
from soccer.soccerapp.models import Match, League, TeamMatch
import datetime
import pandas as pd

class ModelPrep():

    def __init__(self):
        self.creation_date = datetime.datetime.now()

    def get_preped_model(self, league):
        match_factor_dicts = []
        league_matches = league.matches
        if not league_matches:
            return None
        for match in league_matches.all():
            match_factors = {'home_team_goals': TeamMatch.objects.get(match=match, team=match.home_team).goals_final, 'away_team_goals': TeamMatch.objects.get(match=match, team=match.away_team).goals_final,
                             'match_id': match.id}
            match_factors_obj = MatchFactors(match)
            match_factors.update(match_factors_obj.get_match_meta_factors())
            rankings_factors = match_factors_obj.get_teams_rankings_factors()
            match_factors.update(self.parse_rankings_factors(rankings_factors))
            match_factor_dicts.append(match_factors)
        res = pd.DataFrame(match_factor_dicts)
        return res

    def parse_rankings_factors(self, rankings_factors):
        def get_renamed_factors(org_dict, char_append):
            factors = {}
            for fact, val in org_dict.items():
                factors["{0}{1}".format(char_append, fact)] = val
            return factors

        new_rankings_factors = {}
        new_rankings_factors.update(get_renamed_factors(rankings_factors['home_team'], 'h_'))
        new_rankings_factors.update(get_renamed_factors(rankings_factors['away_team'], 'a_'))
        return new_rankings_factors
