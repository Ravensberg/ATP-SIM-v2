# -*- coding: UTF-8 -*-
from dataclasses import dataclass, asdict, field
import pandas as pd
import json
import os


@dataclass
class Player:
    # Percentages imputed as per thousand to use only integers
    name: str = ''

    # Stats as a Server
    ace: int = 0
    double_fault: int = 0
    first_serve_in: int = 0
    first_serve_won: int = 0
    second_serve_won: int = 0
    break_point_saved: int = 0

    # Stats as a Returner
    return_first_serve_won: int = 0
    return_second_serve_won: int = 0
    break_point_won: int = 0

    # ATP points and results
    atp_points: int = 0
    # atp_points_updated: bool = False
    atp_ranking: int = 0
    wins: int = 0
    losses: int = 0
    tournament_wins: int = 0
    current_tournament: str = ''
    tournaments_played: int = 0

    all_stats: dict = field(default_factory=dict)
    atp_main_titles: dict = field(default_factory=dict)
    players_history: dict = field(default_factory=dict)
    singles_race_points: int = 0
    singles_race_points_updated: bool = False
    '''top_tournaments = {3: (0, 'Australian Open'), 21: (0, 'Roland Garros'), 26: (0, 'Wimbledon'),
                       35: (0, 'US Open'), 10: (0, 'Indian Wells'), 12: (0, 'Miami'), 18: (0, 'Madrid'),
                       19: (0, 'Rome'), 32: (0, 'Toronto'), 33: (0, 'Cincinnati'), 41: (0, 'Shanghai'),
                       44: (0, 'Paris')}
    '''
    last_52_weeks: dict = field(default_factory=dict)
    top_tournaments: dict = field(default_factory=dict)

    # def increase_atp_points(self, amount) -> None:
    # self.atp_points += amount
    # print(f'{self.name} gained {amount} ATP points')

    def initialize_stats(self, surface: str) -> None:
        self.ace = self.all_stats[surface]['pct_ace']
        self.double_fault = self.all_stats[surface]['pct_double_fault']
        self.first_serve_in = self.all_stats[surface]['pct_first_serve_in']
        self.first_serve_won = self.all_stats[surface]['pct_first_serve_won']
        self.second_serve_won = self.all_stats[surface]['pct_second_serve_won']
        self.break_point_saved = self.all_stats[surface]['pct_break_point_saved']
        self.return_first_serve_won = self.all_stats[surface]['pct_return_first_serve_won']
        self.return_second_serve_won = self.all_stats[surface]['pct_return_second_serve_won']
        self.break_point_won = self.all_stats[surface]['pct_break_point_won']

    def record_tournament_points_for_singles_race(self, tournament_name: str = '', points: int = 0,
                                                  week: int = 1):
        top_tournaments_singles = ['Australian Open', 'Roland Garros', 'Wimbledon', 'US Open', 'Indian Wells', 'Miami',
                                   'Madrid', 'Rome', 'Montreal', 'Cincinnati', 'Shanghai', 'Paris']
        '''
        # Week: (points, tournament name) // 3: (0, 'A')
        top_tournaments = {3: (0, 'Australian Open'), 21: (0, 'Roland Garros'), 26: (0, 'Wimbledon'),
                           35: (0, 'US Open'), 10: (0, 'Indian Wells'), 12: (0, 'Miami'), 18: (0, 'Madrid'),
                           19: (0, 'Rome'), 32: (0, 'Toronto'), 33: (0, 'Cincinnati'), 41: (0, 'Shanghai'),
                           44: (0, 'Paris')}
        last_52_weeks = {}
        '''
        tournament_accounted_for = False
        points_dropped = False
        top_events_points = []
        singles_points = []
        gain = False

        # Grand Slams and mandatory ATP 1000 - Record points and check for dropped points
        if tournament_name in top_tournaments_singles and str(week) in self.top_tournaments:
            #if self.name == 'Thibault Jaray' and self.top_tournaments[str(week)][0] > 0:
                #print(f'dropped {self.top_tournaments[str(week)][0]} points from {self.top_tournaments[str(week)][1]} - Week {week}')
            self.top_tournaments[str(week)] = (0, self.top_tournaments[str(week)][1])
            points_dropped = True
        if tournament_name in top_tournaments_singles:
            gain = True
            self.top_tournaments[str(week)] = (points, tournament_name)
            tournament_accounted_for = True

        for w in self.top_tournaments:
            singles_points.append(self.top_tournaments[w][0])

        #if gain and self.name == 'Thibault Jaray' :
            #print(f'GAINED {points} points from {tournament_name} - total {sum(singles_points)}')
        # for w in self.top_tournaments:
        #    print(self.top_tournaments[w][0])
        # print('...........')

        # Other tournaments - Record points and check for dropped points
        if not points_dropped and not tournament_accounted_for:
            #if self.name == 'Thibault Jaray' and self.last_52_weeks[str(week)][0] > 0:
                #print(
                    #f'dropped {self.last_52_weeks[str(week)][0]} points from {self.last_52_weeks[str(week)][1]} - Week {week}')
            self.last_52_weeks[str(week)] = (0, 'tournament name')
            points_dropped = True

        if not tournament_accounted_for and tournament_name:
            self.last_52_weeks[str(week)] = (points, tournament_name)
            #if self.name == 'Thibault Jaray' and self.last_52_weeks[str(week)][0] > 0:
                #print(f'GAINED {points} points from {tournament_name} - Week {week}')

        for t in self.last_52_weeks:
            top_events_points.append(self.last_52_weeks[t][0])
        top_events_points.sort(reverse=True)
        singles_points.extend(top_events_points[0:7])

        points_buffer = int((52 - week + 1) / 52 * self.atp_points)
        singles_points.append(points_buffer)

        self.singles_race_points = sum(singles_points)
        self.singles_race_points_updated = True


def create_player_from_database(name: str, db: pd.DataFrame = None) -> Player:
    if not db:
        db = pd.read_csv('Data/atp_db_31_12_2018.csv', delimiter=";", decimal=",")

    all_stats = {}

    for surface in ['Clay', 'Hard', 'Grass']:
        filtered_df = db[(db.PLAYER == name) & (db.SURFACE == surface)]
        # if filtered_df.empty:
        #    continue

        points = int(transform_float_to_d1000(float_value=(filtered_df['Points'].values.astype(int)), default_value=0)/1000)

        stats = {}
        pct_ace = transform_float_to_d1000(float_value=(filtered_df['Ace_Pct'].values.astype(float)), default_value=80)
        pct_double_fault = transform_float_to_d1000(float_value=(filtered_df['Df_Pct'].values.astype(float)),
                                                    default_value=200)
        pct_first_serve_in = transform_float_to_d1000(
            float_value=(filtered_df['1st_Serve_Pct'].values.astype(float)), default_value=500)
        pct_first_serve_won = transform_float_to_d1000(
            float_value=(filtered_df['1st_Serve_Won_Pct'].values.astype(float)), default_value=450)
        pct_second_serve_won = transform_float_to_d1000(
            float_value=(filtered_df['2nd_Serve_Won_Pct'].values.astype(float)), default_value=350)
        pct_break_point_saved = transform_float_to_d1000(
            float_value=(filtered_df['Break_Pt_Saved_Pct'].values.astype(float)), default_value=500)
        pct_return_first_serve_won = transform_float_to_d1000(
            float_value=(filtered_df['1st_Serve_Return_Won_Pct'].values.astype(float)), default_value=300)
        pct_return_second_serve_won = transform_float_to_d1000(
            float_value=(filtered_df['2nd_Serve_Return_Won_Pct'].values.astype(float)), default_value=200)
        pct_break_point_won = transform_float_to_d1000(
            float_value=(filtered_df['Break_Pt_Won_Pct'].values.astype(float)), default_value=300)

        stats = {
            'pct_ace': pct_ace,
            'pct_double_fault': pct_double_fault,
            'pct_first_serve_in': pct_first_serve_in,
            'pct_first_serve_won': pct_first_serve_won,
            'pct_second_serve_won': pct_second_serve_won,
            'pct_break_point_saved': pct_break_point_saved,
            'pct_return_first_serve_won': pct_return_first_serve_won,
            'pct_return_second_serve_won': pct_return_second_serve_won,
            'pct_break_point_won': pct_break_point_won
        }

        all_stats[surface] = stats

    player = Player(name=name, all_stats=all_stats, atp_points=points)

    return player


def transform_float_to_d1000(float_value: float, default_value: int) -> int:
    return int(float_value * 1000) if float_value else default_value


def load_player(file_name: str) -> Player:
    with open(file_name, 'r') as f:
        data = json.load(f)
        player_dict = json.loads(data)
        return Player(**player_dict)


def save_player(player: Player, filename: str) -> None:
    data = json.dumps(player.__dict__)
    with open(filename, 'w') as f:
        json.dump(data, f)


def load_all_players(season: int, week: int) -> list[Player]:
    players = []
    folder_path = f"C:\\Users\\thiba\\Documents\\ATP_Sim\\Sim\\{season}\\Week_{week}"

    with os.scandir(folder_path) as it:
        for entry in it:
            if entry.name.endswith('.json') and entry.is_file():
                player = load_player(entry.path)
                players.append(player)

    return players


def save_all_players(players: list[Player], season: int, week: int) -> None:
    folder_path = f"C:\\Users\\thiba\\Documents\\ATP_Sim\\Sim\\{season}\\Week_{week}"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    for p in players:
        save_player(player=p, filename=f'Sim/{season}/Week_{week}/{p.name}.json')


def reset_all_players():
    df = pd.read_csv('Data/atp_db_31_12_2018.csv', delimiter=";", decimal=",")
    playerz = set(df['PLAYER'].values.tolist())
    players = []

    for player in playerz:
        player_object = create_player_from_database(name=player)
        players.append(player_object)

    return players
