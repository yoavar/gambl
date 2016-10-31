__author__ = 'yoav'

from django.contrib import admin

from soccer.soccerapp.models import Team, League, Player, Match, Position, TeamRank, PlayerMatch, TeamMatch, Stadium


admin.site.register(Team)

admin.site.register(TeamRank)

class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'full_title', 'position_group')
admin.site.register(Position, PositionAdmin)

class StadiumAdmin(admin.ModelAdmin):
    list_display = ('title', 'max_size', 'construction_year', 'cords_x', 'cords_y')

    actions = ('merge',)
    def cords_x(self, obj):
        if not obj.cords:
                return ''
        return obj.cords.x
    cords_x.short_description = 'Latitude'

    def cords_y(self, obj):
        if not obj.cords:
            return ''
        return obj.cords.y
    cords_y.short_description = 'Longitude'

    def merge(self, request, queryset):
        main = queryset[0]
        tail = queryset[1:]

        for other_stadium in tail:
            if main.cords is None:
               main.cords = other_stadium.cords
            if main.max_size is None:
               main.max_size = other_stadium.max_size
            if main.construction_year is None:
               main.construction_year = other_stadium.construction_year

            for match in other_stadium.matches.all():
                match.stadium = main
                match.save()
            other_stadium.delete()
        main.save()
## TODO -- class for checking what data is missing.
## Leagues (by years), matches(per league), matches data(model factors), players data

admin.site.register(Stadium, StadiumAdmin)

class LeagueAdmin(admin.ModelAdmin):
    list_display = ('nami', 'year', 'country', 'rank', 'total_round', 'type', 'matches_cnt', 'teams_cnt',
                    'stadiums_cnt', 'players_cnt', 'referees_cnt',)
    def matches_cnt(self, obj):
        return obj.matches.all().count()
    matches_cnt.short_description = 'Matches Count'
    def teams_cnt(self, obj):
        return obj.matches.all().values_list('teams__team').distinct().count()
    teams_cnt.short_description = 'Teams Count'
    def stadiums_cnt(self, obj):
        return obj.matches.all().values_list('stadium').distinct().count()
    stadiums_cnt.short_description = 'Stadiums Count'
    def players_cnt(self, obj):
        team_matches = obj.matches.all().values_list('teams__team', flat=True)
        players_cnt = PlayerMatch.objects.filter(team_id__in=team_matches).distinct().count()
        return players_cnt
    players_cnt.short_description = 'Players Count'
    def referees_cnt(self, obj):
        return obj.matches.all().values_list('referee').distinct().count()
    referees_cnt.short_description = 'Referees Count'

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