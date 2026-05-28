import random
from dataclasses import field, dataclass
from player import Player, load_all_players, reset_all_players, save_all_players
from tournament import Tournament, load_calendar


@dataclass
class AtpTour:
    current_season: int = 2029
    current_week: int = 1
    all_players: list[Player] = field(default_factory=list)
    all_tournaments: list[Tournament] = field(default_factory=list)

    def __post_init__(self):
        self.all_players = load_all_players(season=self.current_season-1, week=52)
        #self.all_players = reset_all_players()
        self.all_tournaments = load_calendar(season=self.current_season)



        self.sort_player_rankings()
        self.reset_players_for_new_season()
        # self.reset_atp_points()
        # self.print_top_x_players(amount=10)
        # Sort by ATP points, Tournament wins, Alphabetical on existing points
        #self.all_players = sorted(self.all_players, key=lambda p: (-p.atp_points, p.name), reverse=False)
        #for rank, player in enumerate(self.all_players):
        #    player.atp_ranking = rank + 1

    #def reset_atp_points(self):
    #    for player in self.all_players:
    #        player.atp_points = 0

    def sort_player_rankings(self):
        # Sort by ATP points, Tournament wins, Alphabetical
        self.all_players = sorted(self.all_players, key=lambda p: (-p.singles_race_points, -p.tournament_wins, -p.wins, p.name),
                                  reverse=False)
        for rank, player in enumerate(self.all_players):
            player.atp_ranking = rank + 1
        # print(f'{player.atp_ranking}. {player.name}: {player.atp_points}')

    def release_players_from_tournaments(self):
        for player in self.all_players:
            player.current_tournament = ''
            player.singles_race_points_updated = False

    def print_top_x_players(self, amount: int):
        for p in self.all_players[0:amount]:
            print(
                f'{p.atp_ranking}. {p.name}: {p.singles_race_points} points, {p.tournament_wins} titles. Record: {p.wins}-{p.losses} over {p.tournaments_played} tounaments played. ATP 1000 & Grand Slams wins: {p.atp_main_titles}')
            #print(f'Top tournaments:  {p.top_tournaments}')
            #print(f'Other tournaments:  {p.last_52_weeks}')
        #print('-------------------------------------------')

    def print_me(self):
        for p in self.all_players:
            if p.name == 'Thibault Jaray':
                print(
                    f'{p.atp_ranking}. {p.name}: {p.singles_race_points} points, {p.tournament_wins} titles. Record: {p.wins}-{p.losses} over {p.tournaments_played} tournaments played. ATP 1000 & Grand Slams wins: {p.atp_main_titles}')
                #print(p.top_tournaments)
                #print(p.last_52_weeks)
        print('------------------------------------------------')

    def sort_tournaments(self):
        # Sort by Week, Tour level, Tournament level, Alphabetical
        self.all_tournaments = sorted(self.all_tournaments,
                                      key=lambda p: (p.week, p.tour_level, p.tournament_level, p.name),
                                      reverse=False)
        # for t in range(10):
        #    print(f'{self.all_tournaments[t].week}. {self.all_tournaments[t].name}: {self.all_tournaments[t].tour_level}/{self.all_tournaments[t].tournament_level}')

    def play_a_season(self):
        for week in range(52):
            self.play_a_week()
            self.current_week += 1

        #self.print_top_x_players(amount=20)
        #self.print_me()
        # Go back to week 52
        self.save_all_players(week_buffer=-1)
        #self.reset_players_for_new_season()
        self.current_week = 1
        #self.current_season += 1

    def play_a_week(self):
        #idx = 0
        for t in self.all_tournaments:
            if t.week == self.current_week:
                #print(f'     Playing in {t.name} on {t.surface} ({t.tournament_level}), Main Draw of {t.main_draw_size}')
                t.run_tournament(available_players=self.all_players)
                #idx += 1

        self.weekly_data_processing()
        # print(f'    Finished playing week {self.current_week} - {idx} tournaments')

    def play_a_tournament(self):
        tourney = random.choices(population=self.all_tournaments, k=1)[0]
        tourney.run_tournament(available_players=self.all_players)

    def weekly_data_processing(self):
        self.drop_points_from_52_weeks_ago()
        self.sort_player_rankings()
        self.release_players_from_tournaments()
        # self.print_top_x_players(amount=10)
        # save_all_players(players=self.all_players, season=self.current_season, week=self.current_week)

    def save_all_players(self, week_buffer: int = 0):
        save_all_players(players=self.all_players, season=self.current_season, week=self.current_week + week_buffer)

    def reset_players_for_new_season(self):
        for p in self.all_players:
            season_history = {}
            season_history['wins'] = p.wins
            season_history['losses'] = p.losses
            season_history['points'] = p.singles_race_points
            season_history['year-end rank'] = p.atp_ranking
            season_history['titles'] = p.tournament_wins
            season_history['tournaments played'] = p.tournaments_played
            season_history['main titles'] = p.atp_main_titles
            season_history['top tournaments'] = p.top_tournaments
            season_history['last 52 weeks'] = p.last_52_weeks
            p.players_history[f'season_{self.current_season}'] = season_history

            p.wins = 0
            p.losses = 0
            p.tournament_wins = 0
            p.current_tournament = ''
            p.tournaments_played = 0
            p.atp_points = 0
            p.atp_main_titles = {}

    def drop_points_from_52_weeks_ago(self):
        for p in self.all_players:
            if not p.singles_race_points_updated:
                p.record_tournament_points_for_singles_race(week=self.current_week)
                p.singles_race_points_updated = True
