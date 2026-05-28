from player import Player
from dataclasses import dataclass
import random


@dataclass
class PointSimulation:
    server: Player = None
    returner: Player = None
    previous_roll: int = 0

    def swap_server_returner(self):
        self.server, self.returner = self.returner, self.server
        #print(f'PLAYER SWAP. New server is {self.server.name}. Max roll for an ace: {self.server.ace}')

    def sim_point(self, points_score: [int, int], player_a: str, game_type: str = 'Standard') -> (str, str):
        point_type = self.determine_point_type(points_score=points_score, player_a=player_a, game_type=game_type)
        return self.point_simulation_tree(point_type=point_type)

    def determine_point_type(self, points_score: [int, int], player_a: str, game_type: str = 'Standard') -> str:
        # Determine if break opportunity from score given as [score_player_A, score_player_B]
        if self.server.name == player_a:
            points_server, points_returner = points_score[0], points_score[1]
        else:
            points_server, points_returner = points_score[1], points_score[0]

        if game_type == 'Standard' and points_returner >= 3 and points_returner > points_server:
            # print('Break Opportunity')
            return 'Break Oppy'

        if game_type == 'Tie-Break' and points_returner >= 6 and points_returner > points_server:
            # print('Break Opportunity')
            return 'Break Oppy'

        return 'Standard'

    def point_simulation_tree(self, point_type: str) -> (str, str):
        # print(f'{self.server.name} is serving...')
        if self.roll_for_first_serve_in():
            if self.roll_for_ace():
                return self.server.name, 'ace', point_type, self.server.name
            if self.roll_for_first_serve_win(point_type=point_type):
                return self.server.name, '1st_serve_won', point_type, self.server.name
            else:
                return self.returner.name, '1st_serve_return_won', point_type, self.server.name

        if self.roll_for_double_fault():
            return self.returner.name, 'double_fault', point_type, self.server.name

        if self.roll_for_second_serve_win(point_type=point_type):
            return self.server.name, '2nd_serve_won', point_type, self.server.name
        else:
            return self.returner.name, '2nd_serve_return_won', point_type, self.server.name

    def check_versus_random(self, stat_to_check: int, max_random_roll: int = 1000, previous_roll: bool = False) -> bool:
        if not previous_roll:
            rng = random.randint(1, max_random_roll)
            self.previous_roll = rng
        else:
            rng = self.previous_roll
            self.previous_roll = 0

        return True if rng <= stat_to_check else False

    def log_five_formula(self, server_stat_to_compute: str, returner_stat_to_compute: str) -> int:
        prob_server = getattr(self.server, server_stat_to_compute) / 1000
        prob_returner = getattr(self.returner, returner_stat_to_compute) / 1000

        log_numerator = prob_server - prob_server * prob_returner
        log_denominator = prob_server + prob_returner - 2 * prob_server * prob_returner
        if log_denominator == 0:
            log = 0.01
        else:
            log = log_numerator / log_denominator * 1000
        #print(f'{log_numerator} over {log_denominator} is {int(log)}')
        return int(log)

    def roll_for_first_serve_in(self) -> bool:
        return True if self.check_versus_random(stat_to_check=self.server.first_serve_in) else False

    def roll_for_ace(self) -> bool:
        return True if self.check_versus_random(stat_to_check=self.server.ace, previous_roll=True) else False

    def roll_for_first_serve_win(self, point_type: str) -> bool:
        if point_type == 'Standard':
            first_serve_win = self.log_five_formula(server_stat_to_compute='first_serve_won',
                                                    returner_stat_to_compute='return_first_serve_won')
        else:
            first_serve_win = self.log_five_formula(server_stat_to_compute='break_point_saved',
                                                    returner_stat_to_compute='break_point_won')
        return True if self.check_versus_random(first_serve_win) else False

    def roll_for_double_fault(self) -> bool:
        return True if self.check_versus_random(self.server.double_fault) else False

    def roll_for_second_serve_win(self, point_type: str) -> bool:
        if point_type == 'Standard':
            second_serve_win = self.log_five_formula(server_stat_to_compute='second_serve_won',
                                                     returner_stat_to_compute='return_second_serve_won')
        else:
            second_serve_win = self.log_five_formula(server_stat_to_compute='break_point_saved',
                                                     returner_stat_to_compute='break_point_won')
        return True if self.check_versus_random(second_serve_win) else False
