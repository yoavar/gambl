__author__ = 'yoav'
from django.db.models import Avg
from soccer.soccerapp.models import Match, TeamMatch, Team, BetMatch
import datetime
import numpy as np

class MentalFactors():

    bet_max_factor = 1.65 ##100/1.65 >> 60% probablity of outcome

    mental_factors = {'match_cnt': None, 'home_games_cnt': None, 'lossing_strict': None,
                       'winning_strict': None, 'bad_beat': None, 'last_is_bad_beat': None,
                      'sensation': None, 'last_is_sensation': None, 'players_age': None, 'players_nationality': None}

    def __init__(self):
        pass

    def get_team_factors(self, team, date):
        team_last_matches = self.get_last_matches(team, date)
        factors = self.get_last_matches_factors(team, team_last_matches)
        return factors

    def get_last_matches(self, team, date, days_back=30):
        last_matches = TeamMatch.objects.filter(team=team,
                                                    match__match_date__gt=date - datetime.timedelta(days_back),
                                                    match__match_date__lt=date)
        return last_matches

    def get_last_matches_factors(self, team, last_matches):
        mental_factors = {}
        mental_factors['match_cnt'] = len(last_matches)
        mental_factors['home_games_cnt'] = sum([1 if team_match.get_home_away() == 'home' else 0 for team_match in last_matches])
        mental_factors['wins_strict'], mental_factors['loses_strict'] = self.get_matches_stricts_factors(team ,last_matches)
        mental_factors.update(self.get_bets_factors(team, last_matches))
        return mental_factors

    def get_bets_factors(self, team, last_matches):
        match_bet_factors = []
        for team_match in sorted(last_matches, key=lambda x:x.match.match_date, reverse=True):
            match_good_beat = 0
            match_bad_beat = 0
            home_away = team_match.get_home_away()
            match_result = team_match.get_team_match_result()
            bets = {bet_type: bet_val for bet_type, bet_val in team_match.match.bets.filter(type__in=['ht_win', 'aw_win', 'draw'],
                                                value__lte=self.bet_max_factor).values_list('type', 'value').
            annotate(mean_val=Avg('value')).values_list('type', 'mean_val')}
            print(bets, match_result)
            if match_result == 'draw':
               b = bets.get('draw', None)
               if b:
                   match_bad_beat = 1.0 / b
            else:
                ht_b = bets.get('ht_win', None)
                at_b = bets.get('at_win', None)
                if match_result == 'win':
                   if home_away == 'home' and at_b:##Away was predicted to win
                      match_good_beat = 1.0 / at_b
                   if home_away == 'away' and ht_b:##Home was predicted to win
                       match_good_beat = 1.0 / ht_b
                else:##Team Lost
                    if home_away == 'home' and ht_b:##Team was predicted to win
                        match_bad_beat = 1.0 / ht_b
                    if home_away == 'away' and at_b:##Team was predicted to win
                        match_bad_beat = 1.0 / at_b
            match_bet_factors.append((match_good_beat, match_bad_beat))
        factors_dict = {}
        factors_dict['last_bad_beat'] = match_bet_factors[0][1]
        factors_dict['last_good_beat'] = match_bet_factors[0][0]
        factors_dict['bad_beats'] = np.mean([x[1] for x in match_bet_factors])
        factors_dict['good_beats'] = np.mean([x[0] for x in match_bet_factors])
        return factors_dict

    def get_matches_stricts_factors(self, team, last_matches):
        lossing_strict = 0
        winning_strict = 0
        results_matches = [(team_match.match.match_date, team_match.get_team_match_result()) for team_match in last_matches]
        results_matches = [x[1] for x in sorted(results_matches, key=lambda x:x[0], reverse=True)]
        last_match_result = results_matches[0]
        if last_match_result != 'draw':
            strict_cnt = 1
            for m_result in results_matches[1:] :
                if m_result == last_match_result:
                    strict_cnt += 1
                else:
                   break
        if last_match_result == 'win':
            winning_strict = strict_cnt
        elif last_match_result == 'loss':
            lossing_strict = strict_cnt
        return winning_strict, lossing_strict
