__author__ = 'yoav'

from django.contrib import admin

from soccer.soccerapp.models import Team, League, Player, Match, Position, TeamRank, PlayerMatch, TeamMatch


admin.site.register(Team)

admin.site.register(TeamRank)

class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'full_title', 'position_group')
admin.site.register(Position, PositionAdmin)



class LeagueAdmin(admin.ModelAdmin):
    list_display = ('nami', 'year', 'country', 'rank', 'total_round', 'type')
admin.site.register(League, LeagueAdmin)


class PlayerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'nationality', 'dob', 'height', 'weight')
    search_fields = ('first_name', 'last_name')
    list_filter = ('nationality', )

admin.site.register(Player, PlayerAdmin)

class TeamMatchAdmin(admin.ModelAdmin):
    list_display = ('get_team_name', 'pretty_match', 'goals_final', 'goals_half', 'formation', 'corners', 'fouls_commited')
    search_fields = ('get_team_name', )

    def get_team_name(self, obj):
        return obj.team.nami
    get_team_name.admin_order_field = 'nami'
    get_team_name.short_description = 'Team Name'
    def pretty_match(self, obj):
        return obj.match.get_pretty_name()

admin.site.register(TeamMatch, TeamMatchAdmin)

class MatchAdmin(admin.ModelAdmin):
    list_display = ('get_league_name', 'get_home_team_name', 'get_away_team_name', 'match_date', 'referee', 'stadium', 'weather', 'minutes_played')
    search_fields = ('home_team', 'away_team')

    def get_home_team_name(self, obj):
        return obj.home_team.nami
    def get_away_team_name(self, obj):
        return obj.away_team.nami
    def get_league_name(self, obj):
        return obj.league.get_pretty_name()

admin.site.register(Match, MatchAdmin)


class PlayerMatchAdmin(admin.ModelAdmin):
    list_display = ('get_player_name', 'get_match_name', 'get_team_name', 'get_position_name', 'get_match_date',
'opening', 'get_minutes', 'goals', 'assists', 'passes', 'shots', 'shots_on_target', 'touches', 'fouls')

    def get_player_name(self, obj):
        return obj.player.get_full_name()
    def get_match_name(self, obj):
        return obj.team.match.get_pretty_name()
    def get_team_name(self, obj):
        return obj.team.team.nami
    def get_league_name(self, obj):
        return obj.team.match.league.get_pretty_name()
    def get_position_name(self, obj):
        return obj.position.title
    def get_match_date(self, obj):
        return obj.team.match.match_date
    def get_minutes(self, obj):
        p_minutes = obj.get_minutes_played()
        return p_minutes

admin.site.register(PlayerMatch, PlayerMatchAdmin)