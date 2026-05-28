from matchsimulation import MatchSimulation
import random
from player import Player, load_player
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import os
import json

TOUR_LEVEL = ['FUTURE', 'CHALLENGER', 'ATP_TOUR', 'GRAND_SLAM']
TOURNAMENT_LEVEL = ['CHALLENGER_50', 'CHALLENGER_75', 'CHALLENGER_80', 'CHALLENGER_90', 'CHALLENGER_100',
                    'CHALLENGER_110', 'CHALLENGER_125', 'CHALLENGER_175', 'ATP_250', 'ATP_500', 'ATP_1000',
                    'ATP_FINALS', 'GRAND_SLAM']


def atp_tour_draw(players: list[Player], draw_size: int, tournament_level: str, tournament_name: str) -> (
        list, list, list):
    direct_acceptance = 0
    # wild_card = 0
    quali_draw_size = 0
    qualifier_amount = 0
    min_rank = 0
    max_rank = 0
    seeds = 0

    tournament_draw_composition = [
        {'tournament_level': 'GRAND_SLAM', 'main_draw_size': 128, 'direct_acceptance': 104, 'wild_card': 8,
         'quali_draw_size': 128, 'qualifier_amount': 16, 'min_rank': 1, 'max_rank': 200, 'seeds': 32},
        {'tournament_level': 'ATP_1000', 'main_draw_size': 48, 'direct_acceptance': 39, 'wild_card': 3,
         'quali_draw_size': 24, 'qualifier_amount': 6, 'min_rank': 1, 'max_rank': 250, 'seeds': 16},
        {'tournament_level': 'ATP_1000', 'main_draw_size': 56, 'direct_acceptance': 45, 'wild_card': 4,
         'quali_draw_size': 28, 'qualifier_amount': 7, 'min_rank': 1, 'max_rank': 250, 'seeds': 16},
        {'tournament_level': 'ATP_1000', 'main_draw_size': 96, 'direct_acceptance': 79, 'wild_card': 5,
         'quali_draw_size': 48, 'qualifier_amount': 12, 'min_rank': 1, 'max_rank': 250, 'seeds': 32},
        {'tournament_level': 'ATP_500', 'main_draw_size': 32, 'direct_acceptance': 24, 'wild_card': 4,
         'quali_draw_size': 16, 'qualifier_amount': 4, 'min_rank': 1, 'max_rank': 300, 'seeds': 8},
        {'tournament_level': 'ATP_500', 'main_draw_size': 48, 'direct_acceptance': 37, 'wild_card': 5,
         'quali_draw_size': 24, 'qualifier_amount': 6, 'min_rank': 1, 'max_rank': 300, 'seeds': 16},
        {'tournament_level': 'ATP_500', 'main_draw_size': 56, 'direct_acceptance': 43, 'wild_card': 6,
         'quali_draw_size': 28, 'qualifier_amount': 7, 'min_rank': 1, 'max_rank': 300, 'seeds': 16},
        {'tournament_level': 'ATP_250', 'main_draw_size': 28, 'direct_acceptance': 21, 'wild_card': 3,
         'quali_draw_size': 16, 'qualifier_amount': 4, 'min_rank': 51, 'max_rank': 400, 'seeds': 8},
        {'tournament_level': 'ATP_250', 'main_draw_size': 32, 'direct_acceptance': 25, 'wild_card': 3,
         'quali_draw_size': 16, 'qualifier_amount': 4, 'min_rank': 51, 'max_rank': 400, 'seeds': 8},
        {'tournament_level': 'ATP_250', 'main_draw_size': 48, 'direct_acceptance': 40, 'wild_card': 4,
         'quali_draw_size': 16, 'qualifier_amount': 4, 'min_rank': 51, 'max_rank': 400, 'seeds': 16},
        {'tournament_level': 'ATP_250', 'main_draw_size': 56, 'direct_acceptance': 47, 'wild_card': 5,
         'quali_draw_size': 16, 'qualifier_amount': 4, 'min_rank': 51, 'max_rank': 400, 'seeds': 16},
        {'tournament_level': 'CHALLENGER_80', 'main_draw_size': 48, 'direct_acceptance': 41, 'wild_card': 5,
         'quali_draw_size': 4, 'qualifier_amount': 2, 'min_rank': 50, 'max_rank': 900, 'seeds': 16},
        {'tournament_level': 'CHALLENGER_80', 'main_draw_size': 56, 'direct_acceptance': 48, 'wild_card': 6,
         'quali_draw_size': 4, 'qualifier_amount': 2, 'min_rank': 50, 'max_rank': 900, 'seeds': 16},
        {'tournament_level': 'CHALLENGER_90', 'main_draw_size': 48, 'direct_acceptance': 41, 'wild_card': 5,
         'quali_draw_size': 4, 'qualifier_amount': 2, 'min_rank': 50, 'max_rank': 800, 'seeds': 16},
        {'tournament_level': 'CHALLENGER_90', 'main_draw_size': 56, 'direct_acceptance': 48, 'wild_card': 6,
         'quali_draw_size': 4, 'qualifier_amount': 2, 'min_rank': 50, 'max_rank': 800, 'seeds': 16},
        {'tournament_level': 'CHALLENGER_100', 'main_draw_size': 48, 'direct_acceptance': 41, 'wild_card': 5,
         'quali_draw_size': 4, 'qualifier_amount': 2, 'min_rank': 50, 'max_rank': 700, 'seeds': 16},
        {'tournament_level': 'CHALLENGER_100', 'main_draw_size': 56, 'direct_acceptance': 48, 'wild_card': 6,
         'quali_draw_size': 4, 'qualifier_amount': 2, 'min_rank': 50, 'max_rank': 700, 'seeds': 16},
        {'tournament_level': 'CHALLENGER_110', 'main_draw_size': 48, 'direct_acceptance': 41, 'wild_card': 5,
         'quali_draw_size': 4, 'qualifier_amount': 2, 'min_rank': 50, 'max_rank': 600, 'seeds': 16},
        {'tournament_level': 'CHALLENGER_110', 'main_draw_size': 56, 'direct_acceptance': 48, 'wild_card': 6,
         'quali_draw_size': 4, 'qualifier_amount': 2, 'min_rank': 50, 'max_rank': 600, 'seeds': 16},
        {'tournament_level': 'CHALLENGER_125', 'main_draw_size': 48, 'direct_acceptance': 39, 'wild_card': 5,
         'quali_draw_size': 16, 'qualifier_amount': 4, 'min_rank': 50, 'max_rank': 500, 'seeds': 16},
        {'tournament_level': 'CHALLENGER_125', 'main_draw_size': 56, 'direct_acceptance': 47, 'wild_card': 5,
         'quali_draw_size': 16, 'qualifier_amount': 4, 'min_rank': 50, 'max_rank': 500, 'seeds': 16},
    ]

    for t in tournament_draw_composition:
        if t['tournament_level'] == tournament_level and t['main_draw_size'] == draw_size:
            direct_acceptance = t['direct_acceptance']
            # wild_card = t['wild_card']
            quali_draw_size = t['quali_draw_size']
            qualifier_amount = t['qualifier_amount']
            min_rank = t['min_rank']
            max_rank = t['max_rank']
            seeds = t['seeds']
            continue

    # print(f'{tournament_name}({tournament_level}): {min_rank} to {max_rank}')

    available_players = []
    wildcards = []
    #weights = []
    for p in players:
        if min_rank <= p.atp_ranking <= max_rank and not p.current_tournament:
            available_players.append(p.name)
            #weights.append(min(1, max_rank - p.atp_ranking))
            #if p.name == 'Thibault Jaray':
            #    print(f'{p.atp_ranking}. {p.name} DIRECT')
        if max_rank < p.atp_ranking <= max_rank + 500 and not p.current_tournament:
            wildcards.append(p.name)
            #if p.name == 'Thibault Jaray':
            #    print(f'{p.atp_ranking}. {p.name} WILD-CARD')
        #elif p.current_tournament:
            #if p.name == 'Thibault Jaray':
            #    print(f'{p.atp_ranking}. {p.name} busy at {p.current_tournament}')
            #pass

    acceptances = min(len(available_players), direct_acceptance)
    #if len(available_players) < acceptances:
    #print(f'Need {acceptances} direct acceptances and have {len(available_players)}')
    # print(f'Need {acceptances} direct acceptances and have {len(available_players)}')

    direct_acceptances = get_random_weighted_draw(players=available_players, draw_size=acceptances)
    for p in direct_acceptances:
        if p in wildcards:
            wildcards.remove(p)
            # print('removed WC from available')
    # print(f'DIRECT done')

    wild_card = draw_size - acceptances - qualifier_amount
    #if len(wildcards) < wild_card:
    #print(f'Need {wild_card} wild cards and have {len(wildcards)}')
    # print(f'Need {wild_card} direct acceptances and have {len(wildcards)}')
    wild_cards = get_random_weighted_draw(players=wildcards, draw_size=wild_card)
    for p in wild_cards:
        if p in available_players:
            available_players.remove(p)
            # print('removed pyr')
        if p in wildcards:
            wildcards.remove(p)
            # print('removed wc')
    qualifier_pool = [*available_players, *wildcards]
    # print(f'WC done')

    qualifiers = get_random_weighted_draw(players=qualifier_pool, draw_size=quali_draw_size)
    # print(f'Q done')

    # print('Draw complete!')

    return direct_acceptances, wild_cards, qualifiers, qualifier_amount, seeds


def get_random_weighted_draw(players: list, draw_size: int, weights: list = None) -> list:
    if weights:
        draw = random.choices(population=players, weights=weights, k=draw_size)
    else:
        draw = random.choices(population=players, k=draw_size)

    # print(len(set(players)))
    duplicates = check_for_duplicates_in_draw(draw)
    # print(duplicates)

    while duplicates > 0:
        draw = list(set(draw))
        # print(len(draw))
        for p in draw:
            if p in players:
                # print(p)
                players.remove(p)
        # print(f'Replace {duplicates} direct acceptances and have {len(players)}')
        additional_draw = random.choices(population=players, weights=weights, k=duplicates)
        draw.extend(additional_draw)
        # print(f'New draw: {len(draw)}')
        duplicates = check_for_duplicates_in_draw(draw)
        # print(duplicates)

    return draw


def check_for_duplicates_in_draw(draw: list) -> int:
    # print(f'duplicates: {len(draw) - len(set(draw))}')
    return len(draw) - len(set(draw))


def create_seeded_tournament_draw(draw_size: int, unseeded_draw: list[str], seeds: list[str]):
    # All indices shifted by -1 as list indices start at 0
    # Seeding spots is a list of tuples of (seeds, spots) format
    # Bye spots should be -1 if the seed in uneven and +1 is the seed is even. Ex 0 & 1 and 2 & 3
    seeded_draw = []
    bye_spots = []
    seeding_spots = []
    buffer = 9999
    draw_size_with_byes = 0
    seeds = 0

    tournament_seeding_structure = [
        {'main_draw_size': 28, 'seeds': 8, 'bye_spots': [1, 9, 22, 30], 'seeding_spots': [
            ([0, 1], [0, 31]),
            ([2, 3], [8, 23]),
            ([4, 5, 6, 7], [7, 15, 16, 24])
        ]},
        {'main_draw_size': 32, 'seeds': 8, 'bye_spots': [], 'seeding_spots': [
            ([0, 1], [0, 31]),
            ([2, 3], [8, 23]),
            ([4, 5, 6, 7], [7, 15, 16, 24])
        ]},
        {'main_draw_size': 48, 'seeds': 16, 'bye_spots': [1, 17, 46, 14, 30, 33, 49, 9, 25, 38, 54, 6, 22, 41, 57, 62],
         'seeding_spots': [
             ([0, 1], [0, 63]),
             ([2, 3], [16, 47]),
             ([4, 5, 6, 7], [15, 31, 32, 48]),
             ([8, 9, 10, 11], [8, 24, 39, 55]),
             ([12, 13, 14, 15], [7, 23, 40, 56])
         ]},
        {'main_draw_size': 56, 'seeds': 16, 'bye_spots': [1, 17, 46, 14, 30, 33, 49, 62], 'seeding_spots': [
            ([0, 1], [0, 63]),
            ([2, 3], [16, 47]),
            ([4, 5, 6, 7], [15, 31, 32, 48]),
            ([8, 9, 10, 11], [8, 24, 39, 55]),
            ([12, 13, 14, 15], [7, 23, 40, 56])
        ]},
        {'main_draw_size': 64, 'seeds': 16, 'bye_spots': [1, 9, 22, 30], 'seeding_spots': [
            ([0, 1], [0, 63]),
            ([2, 3], [16, 47]),
            ([4, 5, 6, 7], [15, 31, 32, 48]),
            ([8, 9, 10, 11], [8, 24, 39, 55]),
            ([12, 13, 14, 15], [7, 23, 40, 56])
        ]},
        {'main_draw_size': 96, 'seeds': 32,
         'bye_spots': [1, 126, 33, 94, 30, 62, 65, 99, 17, 49, 78, 110, 14, 46, 81, 113, 9, 22, 41, 54, 73, 86, 105,
                       118, 6, 25, 38, 57, 70, 89, 102, 121], 'seeding_spots': [
            ([0, 1], [0, 127]),
            ([2, 3], [32, 95]),
            ([4, 5, 6, 7], [31, 63, 64, 98]),
            ([8, 9, 10, 11], [16, 48, 79, 111]),
            ([12, 13, 14, 15], [15, 47, 80, 112]),
            ([16, 17, 18, 19, 20, 21, 22, 23], [8, 23, 40, 55, 72, 87, 104, 119]),
            ([24, 25, 26, 27, 28, 29, 30, 31], [7, 24, 39, 56, 71, 88, 103, 120])
        ]},
        {'main_draw_size': 128, 'seeds': 32, 'bye_spots': [], 'seeding_spots': [
            ([0, 1], [0, 127]),
            ([2, 3], [32, 95]),
            ([4, 5, 6, 7], [31, 63, 64, 98]),
            ([8, 9, 10, 11], [16, 48, 79, 111]),
            ([12, 13, 14, 15], [15, 47, 80, 112]),
            ([16, 17, 18, 19, 20, 21, 22, 23], [8, 23, 40, 55, 72, 87, 104, 119]),
            ([24, 25, 26, 27, 28, 29, 30, 31], [7, 24, 39, 56, 71, 88, 103, 120])
        ]}
    ]

    # Pick tournament
    for t in tournament_seeding_structure:
        if t['main_draw_size'] == draw_size:
            bye_spots = t['bye_spots']
            seeding_spots = t['seeding_spots']
            seeds = t['seeds']
            draw_size_with_byes = draw_size + len(t['bye_spots'])
            seeded_draw = create_list_of_player(size=draw_size_with_byes, buffer=buffer)

    if not seeding_spots:
        return None

    # Place byes as needed
    if bye_spots:
        seeded_draw = place_byes(draw=seeded_draw, spots=bye_spots)
    # print(f'1. {seeded_draw}')

    # Place seeded players
    for s in seeding_spots:
        place_seed(draw=seeded_draw, all_seeds=unseeded_draw, seeds=s[0], spots=s[1])

    # Place remaining players
    available_seeds = create_list_of_player(size=draw_size - seeds, buffer=seeds)
    for idx, s in enumerate(seeded_draw):
        if not isinstance(s, str):
            random_seed, available_seeds = pick_random_seed_number(available_seeds=available_seeds)
            #if len(unseeded_draw) + len(bye_spots) < len(seeded_draw):
            #    print(f'Missing {len(seeded_draw) - len(unseeded_draw) - len(bye_spots)} players')
            seeded_draw[idx] = unseeded_draw[random_seed]
    # print(f'FINAL DRAW {seeded_draw}')

    return seeded_draw


def pick_random_seed_number(available_seeds: list) -> (int, list):
    pick = random.choices(population=available_seeds, k=1)[0]
    available_seeds.remove(pick)
    return pick, available_seeds


'''
def seeding_main_32_seeds_8(draw_size: int, unseeded_draw: list[str], seeds: list[str]):
    seeded_draw = create_list_of_player(size=32, buffer=9999)

    # All indices shifted by -1 as list indices start at 0

    # Place byes as needed
    if draw_size == 28:
        bye_spots = [1, 9, 22, 30]
        seeded_draw = place_byes(draw=seeded_draw, spots=bye_spots)

        # for s in seeds:
        #    unseeded_draw.remove(s)

    print(f'1. {seeded_draw}')
    # Seed 1 in spot 1 and seed 2 in last spot
    seeded_draw[0], seeded_draw[-1] = seeds[0], seeds[1]
    print(f'2. {seeded_draw}')

    # Seeds 3-4 in spots 9 and 24
    place_seed(seeded_draw, seeds, [2, 3], [8, 23])
    print(f'3. {seeded_draw}')

    # Seeds 5-8 in spots 8, 16, 17, 25
    place_seed(seeded_draw, seeds, [4, 5, 6, 7], [7, 15, 16, 24])
    print(f'4. {seeded_draw}')

    # Place remaining players

    if draw_size == 32:
        remaining_seeds = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
        remaining_spots = [1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 17, 18, 19, 20, 21, 22, 25, 26, 27, 28, 29, 30]
    elif draw_size == 28:
        remaining_seeds = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
        remaining_spots = [2, 3, 4, 5, 6, 10, 11, 12, 13, 14, 17, 18, 19, 20, 21, 25, 26, 27, 28, 29]
    seeded_draw = place_seed(seeded_draw, unseeded_draw, remaining_seeds, remaining_spots)
    print(f'5. {seeded_draw}')

    return seeded_draw


def seeding_main_64_seeds_16(draw_size: int, unseeded_draw: list[str], seeds: list[str]):
    seeded_draw = create_list_of_player(size=64, buffer=9999)
    random.shuffle(unseeded_draw)
    bye_spots = []
    # All indices shifted by -1 as list indices start at 0

    # Place byes as needed
    if draw_size == 48:
        bye_spots = [1, 17, 46, 14, 30, 33, 49, 9, 25, 38, 54, 6, 22, 41, 57, 62]
        seeded_draw = place_byes(draw=seeded_draw, spots=bye_spots)
    elif draw_size == 56:
        bye_spots = [1, 17, 46, 14, 30, 33, 49, 62]
        seeded_draw = place_byes(draw=seeded_draw, spots=bye_spots)

    if draw_size != 64:
        for bye in bye_spots:
            unseeded_draw.append('BYE')

    # Seed 1 in spot 1 and seed 2 in last spot
    seeded_draw[0], seeded_draw[-1] = seeds[0], seeds[1]

    # Seeds 3-4 in spots 17 and 48
    seeded_draw = place_seed(seeded_draw, seeds, [2, 3], [16, 47])

    # Seeds 5-8 in spots 16, 32, 33, 49
    place_seed(seeded_draw, seeds, [4, 5, 6, 7], [15, 31, 32, 48])

    # Seeds 9-12 in spots 9, 25, 40, 56
    seeded_draw = place_seed(seeded_draw, seeds, [8, 9, 10, 11], [8, 24, 39, 55])

    # Seeds 13-16 in spots 8, 24, 41, 57
    seeded_draw = place_seed(seeded_draw, seeds, [12, 13, 14, 15], [7, 23, 40, 56])

    # Place remaining players
    remaining_seeds = [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39,
                       40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55,
                       56, 57, 58, 59, 60, 61, 62, 63]
    # print(len(remaining_seeds))
    remaining_spots = [1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 17, 18, 19, 20, 21, 22, 25, 26, 27, 28, 29, 30, 33, 34,
                       35, 36, 37, 38, 41, 42, 43, 44, 45, 46, 49, 50, 51, 52, 53, 54, 57, 58, 59, 60, 61, 62]

    # print(len(remaining_spots))
    seeded_draw = place_seed(seeded_draw, unseeded_draw, remaining_seeds, remaining_spots)

    print(len(seeded_draw))

    return seeded_draw


def seeding_main_128_seeds_32(draw_size: int, unseeded_draw: list[str], seeds: list[str]):
    seeded_draw = create_list_of_player(size=128, buffer=9999)
    random.shuffle(unseeded_draw)
    # print(f'Seeds of {len(seeds)}')

    # All indices shifted by -1 as list indices start at 0

    # Seed 1 in spot 1 and seed 2 in last spot
    seeded_draw[0], seeded_draw[-1] = seeds[0], seeds[1]

    # Seeds 3-4 in spots 33 and 96
    seeded_draw = place_seed(seeded_draw, seeds, [2, 3], [32, 95])

    # Seeds 5-8 in spots 32, 64, 65, 97
    seeded_draw = place_seed(seeded_draw, seeds, [4, 5, 6, 7], [31, 63, 64, 98])

    # Seeds 9-12 in spots 17, 49, 80, 112
    seeded_draw = place_seed(seeded_draw, seeds, [8, 9, 10, 11], [16, 48, 79, 111])

    # Seeds 13-16 in spots 16, 48, 81, 113
    seeded_draw = place_seed(seeded_draw, seeds, [12, 13, 14, 15], [15, 47, 80, 112])

    # Seeds 17-24 in spots 9, 24, 41, 56, 73, 88, 105, 120
    seeded_draw = place_seed(seeded_draw, seeds, [16, 17, 18, 19, 20, 21, 22, 23], [8, 23, 40, 55, 72, 87, 104, 119])

    # Seeds 25-32 in spots 8, 25, 40, 57, 72, 89, 104, 121
    seeded_draw = place_seed(seeded_draw, seeds, [24, 25, 26, 27, 28, 29, 30, 31], [7, 24, 39, 56, 71, 88, 103, 120])

    # Place remaining players
    remaining_seeds = [32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55,
                       56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79,
                       80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102,
                       103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121,
                       122, 123, 124, 125, 126, 127]
    # print(len(remaining_seeds))
    remaining_spots = [1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 17, 18, 19, 20, 21, 22, 25, 26, 27, 28, 29, 30, 33, 34,
                       35, 36, 37, 38, 41, 42, 43, 44, 45, 46, 49, 50, 51, 52, 53, 54, 57, 58, 59, 60, 61, 62, 65, 66,
                       67, 68, 69, 70, 73, 74, 75, 76, 77, 78, 81, 82, 83, 84, 85, 86, 89, 90, 91, 92, 93, 94, 96, 97,
                       99, 100, 101, 102, 105, 106, 107, 108, 109, 110, 113, 114, 115, 116, 117, 118, 121, 122, 123,
                       124, 125, 126]
    seeded_draw = place_seed(seeded_draw, unseeded_draw, remaining_seeds, remaining_spots)

    # Place byes as needed
    if draw_size == 96:
        bye_spots = [1, 33, 94, 30, 62, 65, 99, 17, 49, 78, 110, 14, 46, 81, 113, 9, 22, 41, 54, 73, 86, 105, 118, 6,
                     25, 38, 57, 70, 89, 102, 119, 126]
        seeded_draw = place_byes(draw=seeded_draw, spots=bye_spots)
    print(seeded_draw)
    return seeded_draw
'''


def place_seed(draw: list, all_seeds: list, seeds: list, spots: list) -> list:
    random.shuffle(spots)
    # print(f'seeds ({len(seeds)}): {seeds} for {len(spots)} spots')
    # print(f'############################################')
    # print(f'all_seeds ({len(all_seeds)}): {all_seeds}')
    for i in range(len(seeds)):
        # print(f'{i}. {spots[i]} ')
        draw[spots[i]] = all_seeds[seeds[i]]

    return draw


def place_byes(draw: list, spots: list) -> list:
    for i in range(len(spots)):
        # print(f'{i}. {spots[i]} to BYE')
        draw[spots[i]] = 'BYE'

    return draw


def create_list_of_player(size: int, buffer: int = 0) -> list:
    players = []

    for i in range(size):
        players.append(i + buffer)

    return players


def create_main_draw(invited: list, qualifiers: list, wild_cards: list) -> list:
    return [*invited, *qualifiers, *wild_cards]


@dataclass
class Tournament:
    # Basic Information
    points_distribution: list[int] == field(default_factory=list)
    name: str = ''
    week: int = 1
    surface: str = ''
    main_draw_size: int = 0
    quali_draw_size: int = 0
    tour_level: str = ''
    tournament_level: str = ''
    cutoff: int = 1
    quali_cutoff: int = 1
    seeds: int = 0

    # Players Information
    round_of_play: int = 1
    seeded_players: list[str] = field(default_factory=list)
    direct_acceptances: list[str] = field(default_factory=list)
    wild_cards: list[str] = field(default_factory=list)
    qualifiers: list[str] = field(default_factory=list)
    draw: list[str] = field(default_factory=list)
    players: list[Player] = field(default_factory=list)
    available_players: list[Player] = field(default_factory=list)
    losers: list[str] = field(default_factory=list)
    winners: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.tournament_level == 'GRAND_SLAM':
            self.best_of_sets = 5
        else:
            self.best_of_sets = 3

    def run_tournament(self, available_players: list[Player] = None):
        self.players = available_players
        self.create_draw()
        self.play_qualification()
        self.create_main_draw()
        self.play_tournament()

    def create_draw(self):
        if not self.draw:
            self.direct_acceptances, self.wild_cards, self.qualifiers, self.quali_cutoff, self.seeds = atp_tour_draw(
                players=self.players, draw_size=self.main_draw_size, tournament_level=self.tournament_level,
                tournament_name=self.name)

        for p in [*self.direct_acceptances, *self.wild_cards, *self.qualifiers]:
            player = self.pick_player_from_list(player_name=p)
            player.current_tournament = self.name
            player.tournaments_played += 1

    def play_qualification(self):
        # print(f'Need {self.quali_cutoff} qualifiers have {len(self.qualifiers)}')
        while len(self.qualifiers) > self.quali_cutoff:
            self.qualifiers = self.play_quali_round()
            # print(f'After Round {self.round_of_play}, players remaining: {len(self.qualifiers)}')
            # print(f'----------------------------------')
            self.round_of_play += 1

        # Award points to qualified players
        for p in self.qualifiers:
            player = self.pick_player_from_list(player_name=p)
            self.award_points_quali(player_name=player.name, tournament_winner=True)

    def create_main_draw(self):

        #print(f'self.direct_acceptances: {len(self.direct_acceptances)}, self.qualifiers: {len(self.qualifiers)}, self.wild_cards: {len(self.wild_cards)}')

        self.draw = [*self.direct_acceptances, *self.qualifiers, *self.wild_cards]

        # if self.name == 'Australian Open':
        # print(f'self.draw of {len(self.draw)}')
        self.determine_seeds_from_draw()
        self.place_seeds_in_main_draw()

    def determine_seeds_from_draw(self):
        ranked_players = []
        for p in self.draw:
            player = self.pick_player_from_list(player_name=p)
            ranked_players.append((p, player.atp_ranking))
        ranked_players.sort(key=lambda tup: tup[1])

        seeds = ranked_players[0:self.seeds]
        self.seeded_players = []
        for p in seeds:
            self.seeded_players.append(p[0])

        for idx, p in enumerate(ranked_players):
            self.draw[idx] = p[0]

    def place_seeds_in_main_draw(self):
        self.draw = create_seeded_tournament_draw(draw_size=self.main_draw_size, unseeded_draw=self.draw,
                                                  seeds=self.seeded_players)

    def play_tournament(self):
        # print(self.draw)
        self.round_of_play = 1
        while len(self.draw) > self.cutoff:
            self.draw = self.play_round()
            # print(f'            After Round {self.round_of_play}, players remaining: {len(self.draw)}')
            # print(f'----------------------------------')
            self.round_of_play += 1

        # Award points to tournament winner
        self.award_points(player_name=self.draw[0], tournament_winner=True)

    def play_round(self) -> (list, list):
        i = 0
        games = int(len(self.draw) / 2)
        self.winners = []

        for game in range(games):
            # print(f'Matchup: {self.draw[i]} vs {self.draw[i + 1]}')
            if self.draw[i] == 'BYE':
                player_b = self.pick_player_from_list(player_name=self.draw[i + 1])
                self.winners.append(player_b.name)

            elif self.draw[i + 1] == 'BYE':
                player_a = self.pick_player_from_list(player_name=self.draw[i])
                self.winners.append(player_a.name)

            else:
                player_a, player_b = self.pick_player_from_list(player_name=self.draw[i]), self.pick_player_from_list(
                    player_name=self.draw[i + 1])
                player_a.initialize_stats(surface=self.surface)
                player_b.initialize_stats(surface=self.surface)

                winner, loser = self.simulate_match(player_a=player_a, player_b=player_b)
                self.winners.append(winner)
                self.award_points(player_name=loser)
            i += 2
        return self.winners

    def play_quali_round(self) -> (list, list):
        i = 0
        games = int(len(self.qualifiers) / 2)
        self.winners = []

        for game in range(games):
            player_a, player_b = self.pick_player_from_list(player_name=self.qualifiers[i]), self.pick_player_from_list(
                player_name=self.qualifiers[i + 1])
            player_a.initialize_stats(surface=self.surface)
            player_b.initialize_stats(surface=self.surface)

            winner, loser = self.simulate_match(player_a=player_a, player_b=player_b)
            if winner == 'Thibault Jaray' or loser == 'Thibault Jaray':
                print(f'QUALI {self.round_of_play} of {self.name}')
            self.winners.append(winner)
            self.award_points_quali(player_name=loser)
            i += 2

        return self.winners

    def pick_player_from_list(self, player_name: str) -> Player:
        for player in self.players:
            if player.name == player_name:
                return player

    def simulate_match(self, player_a: Player, player_b: Player) -> (str, str):
        sim_engine = MatchSimulation(best_of_sets=self.best_of_sets)
        sim_engine.initialize_simulation(player_a=player_a, player_b=player_b)
        winner_name, winner_sets = sim_engine.simulate_match()
        if winner_name == player_b.name:
            loser_name = player_a.name
        else:
            loser_name = player_b.name

        player_a_stats, player_b_stats = sim_engine.player_a_stats, sim_engine.player_b_stats
        if winner_name == 'Thibault Jaray' or loser_name == 'Thibault Jaray':
            if len(self.draw) == 2:
                print(f'[F] of {self.name}// {winner_name} beats {loser_name} over {sum(sim_engine.sets_score)} sets || {sim_engine.match_score}')
            elif len(self.draw) == 4:
                print(
                    f'[SF] of {self.name}// {winner_name} beats {loser_name} over {sum(sim_engine.sets_score)} sets || {sim_engine.match_score}')
            else:
                print(
                    f'{self.round_of_play} of {self.name}// {winner_name} beats {loser_name} over {sum(sim_engine.sets_score)} sets || {sim_engine.match_score}')

        return winner_name, loser_name

    def award_points_quali(self, player_name: str, tournament_winner: bool = False):
        player = self.pick_player_from_list(player_name=player_name)

        if not tournament_winner:
            atp_points = 0
            player.losses += 1
            player.wins += max(0, self.round_of_play - 1)

        if tournament_winner:
            player.wins += self.round_of_play - 1
            atp_points = 0

    def award_points(self, player_name: str, tournament_winner: bool = False):
        player = self.pick_player_from_list(player_name=player_name)

        if not tournament_winner:
            atp_points = self.points_distribution[min(len(self.points_distribution) - 1, self.round_of_play - 1)]
            #player.increase_atp_points(atp_points)
            player.record_tournament_points_for_singles_race(tournament_name=self.name, points=atp_points, week=self.week)
            player.losses += 1
            player.wins += max(0, self.round_of_play - 1)

            if player_name == 'Thibault Jaray':
                p = self.pick_player_from_list(player_name='Thibault Jaray')
                print(f'{self.name}: {self.tour_level} - {self.tournament_level}. Round# {self.round_of_play}\n'
                      f'{p.atp_ranking}. {p.name}: {p.singles_race_points} points, {p.tournament_wins} titles. Record: {p.wins}-{p.losses} over {p.tournaments_played} tournaments played.\n'
                      f'.....................')

        if tournament_winner:
            player.tournament_wins += 1
            player.wins += self.round_of_play - 1
            atp_points = self.points_distribution[-1]
            #player.increase_atp_points(atp_points)
            player.record_tournament_points_for_singles_race(tournament_name=self.name, points=atp_points, week=self.week)

            if player_name == 'Thibault Jaray':
                p = self.pick_player_from_list(player_name='Thibault Jaray')
                print(f'WON A TOURNAMENT!!! {self.name}: {self.tour_level} - {self.tournament_level}. Round# {self.round_of_play}\n'
                      f'{p.atp_ranking}. {p.name}: {p.singles_race_points} points, {p.tournament_wins} titles. Record: {p.wins}-{p.losses} over {p.tournaments_played} tournaments played.\n'
                      f'.....................')

            if self.tour_level == 'ATP_TOUR' and (
                    self.tournament_level == 'ATP_1000' or self.tournament_level == 'GRAND_SLAM'):
                # print(self.print_player_name_main_draw_source(player=player, extra_text=f'won {self.name} - {self.tournament_level} ({self.main_draw_size})'))
                # player.atp_main_titles.append(self.name)
                if not player.atp_main_titles:
                    player.atp_main_titles[self.name] = 1
                    return

                for t in player.atp_main_titles:
                    if t == self.name:
                        player.atp_main_titles[t] = player.atp_main_titles[t] + 1
                        return
                player.atp_main_titles[self.name] = 1

    def print_player_name_main_draw_source(self, player: Player, extra_text: str = ''):
        if player.name in self.seeded_players:
            seed = self.seeded_players.index(player.name) + 1
            return f'           [{seed}] {player.name} ({player.atp_ranking}) {extra_text}'
        if player.name in self.qualifiers:
            return f'           [Q]  {player.name} ({player.atp_ranking}) {extra_text}'
        if player.name in self.wild_cards:
            return f'           [WC] {player.name} ({player.atp_ranking}) {extra_text}'

        return f'           {player.name} ({player.atp_ranking}) {extra_text}'


def create_grand_slam(amount: int) -> (list, list):
    playerz = []
    players = []
    folder_path = "C:\\Users\\thiba\\Documents\\ATP_Sim\\Sim\\2019\\Week_1"

    with os.scandir(folder_path) as it:
        for entry in it:
            if entry.name.endswith('.json') and entry.is_file():
                # print(entry.name, entry.path)
                # with open(entry.path, 'r') as f:
                player = load_player(entry.path)
                players.append(player)
                playerz.append(player.name)

    tourneys = []
    for t in range(amount):
        draw = get_random_weighted_draw(players=playerz, draw_size=32)
        grand_slam = Tournament(name='RG 2019', surface='Clay', main_draw_size=32, tour_level='ATP_TOUR',
                                tournament_level='GRAND_SLAM', draw=draw, players=players,
                                points_distribution=[0, 1, 3, 6, 12, 24, 100])
        tourneys.append(grand_slam)

    return tourneys, players


def load_calendar(season: int) -> list[Tournament]:
    #file_name = f'Data/Calendar_{season}.json'
    file_name = f'Data/Calendar_2019.json'
    tournaments = []

    with open(file_name, 'r') as f:
        data = json.load(f)
        for t in data:
            tournaments.append(Tournament(**data[t]))

    return tournaments
