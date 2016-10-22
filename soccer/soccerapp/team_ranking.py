__author__ = 'yoav'
import datetime
from soccer.soccerapp.models import Match, TeamMatch, Team
import numpy as np

class TeamRanking():

    ranking_factors = {'avg_goals_scored': None, 'avg_goals_conceeded': None, 'last_game_goals_scored': None,
                       'last_game_goals_conceeded': None}

    def __init__(self):
        pass

    def get_team_ranking_factors(self, team, date):
        last_matches = self.get_last_matches(team, date)
        goal_factors = self.get_goals_factors(last_matches)
        return goal_factors

    def get_last_matches(self, team, date, days_back=30):
        last_matches = TeamMatch.objects.filter(team=team,
                                                match__match_date__gt=date - datetime.timedelta(days_back),
                                                match__match_date__lt=date)
        return last_matches

    def get_goals_factors(self, last_matches):
        if len(last_matches) == 0:
           return self.ranking_factors
        goals_scored = []
        goals_conceeded = []
        for mat in last_matches:
            match_goals = mat.match.get_total_goals()
            team_goals_scored = mat.goals_final
            team_goals_conceeded = match_goals - team_goals_scored
            goals_scored.append(team_goals_scored)
            goals_conceeded.append(team_goals_conceeded)

        avg_goals_scored = np.mean(goals_scored)
        avg_goals_conceeded = np.mean(goals_conceeded)
        last_game_goals_scored = goals_scored[-1]
        last_game_goals_conceeded = goals_conceeded[-1]
        return {'avg_goals_scored': avg_goals_scored,
                'avg_goals_conceeded': avg_goals_conceeded,
                'last_game_goals_scored': last_game_goals_scored,
                'last_game_goals_conceeded': last_game_goals_conceeded}


