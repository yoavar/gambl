__author__ = 'yoav'
import pandas as pd


from soccer.soccerapp.models import League, Match, Team, Referee, BetMatch, TeamMatch
import datetime


class DataWorker():

    asian_bets_mapping = {'GBAHH': {'bookie_name': 'gamebookers', 'bet_type': None},
    'GBAHA': {'bookie_name': 'gamebookers', 'bet_type': None},}

    bet_mapping = {'WHD': {'bookie_name': 'William hill', 'bet_type': 'draw'},
     'WHH': {'bookie_name': 'William hill', 'bet_type': 'ht_win'},
     'WHA': {'bookie_name': 'William hill', 'bet_type': 'aw_win'},
     'B365H': {'bookie_name': 'bet365', 'bet_type': 'ht_win'},
     'B365D': {'bookie_name': 'bet365', 'bet_type': 'draw'},
     'B365A': {'bookie_name': 'bet365', 'bet_type': 'at_win'},
     'GB>2.5': {'bookie_name': 'gamebookers', 'bet_type': 'over_goals_2.5'},
     'GB<2.5': {'bookie_name': 'gamebookers', 'bet_type': 'under_goals_2.5'},
     'B365>2.5': {'bookie_name': 'bet365', 'bet_type': 'over_goals_2.5'},
     'B365<2.5': {'bookie_name': 'bet365', 'bet_type': 'under_goals_2.5'},
     }

    def __init__(self):
        self.league_names_map = {'E0': 'premierleague', 'E1': 'championship',
                                 'F1': 'ligue1', 'D1': 'budesliga', 'I1': 'seriea', 'SP1': 'laliga'}

    def parse_file_data(self, file_name):
        data_df = pd.read_csv(file_name)
        league = data_df.loc[0, 'Div']
        first_match_date = data_df.loc[0, 'Date']
        league = self.get_league(league, first_match_date)
        if not league:
            return False
        for ind, row in data_df.iterrows():
            ht_team = row['HomeTeam']
            aw_team = row['AwayTeam']
            match_date = datetime.datetime.strptime(row['Date'], '%d/%m/%y')
            match = self.get_match(league, ht_team, aw_team, match_date)
            self.set_team_matches(match, row)
            self.set_additional_match_features(match, row)
            self.set_bets(match, row)

    def get_league(self, league, first_match_date):
        league_name = self.league_names_map[league]
        parsed_date = datetime.datetime.strptime(first_match_date, "%d/%m/%y")
        year = parsed_date.year-1 if parsed_date.month < 8 else parsed_date.year
        l = League.objects.filter(nami=league_name, year=year)
        if len(l) == 0:
            l = None
        else:
            l = l[0]
        return l

    def get_match(self, league, home_team_name, away_team_name, match_date):
         home_team_obj = Team.objects.get_or_create(home_team_name.lower())
         away_team_obj = Team.objects.get_or_create(away_team_name.lower())
         match = Match.objects.filter(league=league, home_team=home_team_obj, away_team=away_team_obj,
                              match_date__gte=match_date, match_date__lte=match_date+datetime.timedelta(1))
         if len(match) > 0:
             m = match[0]
         else:
             match = Match(league=league, home_team=home_team_obj, away_team=away_team_obj, match_date=match_date)
             match.save()
             m = match
         return m

    def set_team_matches(self, match, df_row):
         self.set_team_match(match, match.home_team, df_row['FTHG'], df_row['HTHG'], df_row['HC'], df_row['HF'])
         self.set_team_match(match, match.away_team, df_row['FTAG'], df_row['HTAG'], df_row['AC'], df_row['AF'])

    def set_team_match(self, match, team, goals_final, goals_half, corners, fouls_commited):
         defaults = {}
         defaults['goals_final'] = goals_final
         defaults['goals_half'] = goals_half
         if corners is not None:
             defaults['corners'] = corners
         if fouls_commited is not None:
             defaults['fouls_commited'] = fouls_commited
         new_team_match, _ = TeamMatch.objects.update_or_create(match=match, team=team, defaults=defaults)

    def set_additional_match_features(self, match, df_row):
         crowd = df_row.get('Attendance', None)
         if crowd is not None:
             match.crowd = crowd
         ref_name = df_row.get('Refere', None)
         if ref_name is not None:
             ref_name = ref_name.lower().split(" ")
             ref_first_letter = ref_name[0]
             ref_last_name = ref_name[1]
             refi = Referee.objects.filter(first_name__startswith=ref_first_letter, last_name=ref_last_name)
             if len(refi) == 0:
                 refi = Referee.objects(first_name=ref_first_letter, last_name=ref_last_name)
                 refi.save()
             match.referee = refi
         match.save()


    def set_bets(self, match, df_row):
         match_handicap_matching = None
         gamebookers_handicap_size = df_row.get('GBAH' , None)
         if gamebookers_handicap_size is not None:
             match_handicap_matching = self.asian_bet_mapping.copy()
             match_handicap_matching['GBAHH']['bet_type'] = 'ht_handicap_{0}'.format(gamebookers_handicap_size)
             match_handicap_matching['GBAHA']['bet_type'] = 'at_handicap_{0}'.format(gamebookers_handicap_size)

         for key, val_dict in self.bet_mapping.items():
             bet_val = df_row.get(key, None)
             if bet_val is not None:
                 BetMatch.objects.get_or_create(match=match, bookie_name=val_dict['bookie_name'],
                                                type=val_dict['bet_type'], value=bet_val)
         if match_handicap_matching is not None:
            for key, val_dict in match_handicap_matching.items():
             bet_val = df_row['key']
            BetMatch.objects.get_or_create(match=match, bookie_name=val_dict['bookie_name'],
                                        type=val_dict['bet_type'], value=bet_val)

