import os
import glob
import copy
from typing import List, Dict, Any, Optional, Tuple

import pygame

from player import Player, load_player, create_player_from_database
from matchsimulation import MatchSimulation
from tactics import TACTICS, TARGETS, build_player_modifier, describe_choice
from tournament import load_calendar
from atptour import AtpTour

pygame.init()

WIDTH, HEIGHT = 1280, 720
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ATP SIM")
CLOCK = pygame.time.Clock()
FPS = 60

FONT_XS = pygame.font.SysFont("segoeui", 15)
FONT_SM = pygame.font.SysFont("segoeui", 18)
FONT = pygame.font.SysFont("segoeui", 21)
FONT_BOLD = pygame.font.SysFont("segoeui", 21, bold=True)
FONT_BIG = pygame.font.SysFont("segoeui", 32, bold=True)
FONT_TITLE = pygame.font.SysFont("segoeui", 52, bold=True)

BG = (18, 26, 35)
PANEL = (38, 48, 62)
PANEL_2 = (49, 61, 78)
PANEL_3 = (62, 74, 92)
TEXT = (235, 239, 244)
MUTED = (165, 174, 187)
GOLD = (210, 170, 70)
GREEN = (35, 140, 88)
RED = (160, 67, 67)
BLUE = (49, 99, 145)
WHITE = (240, 238, 228)
DARK_GREEN = (24, 80, 52)
CLAY = (178, 88, 52)
HARD = (57, 93, 122)
GRASS = (74, 126, 55)
BLACK = (8, 10, 14)

SURFACE_COLORS = {
    "Clay": CLAY,
    "Hard": HARD,
    "Grass": GRASS,
    "Carpet": (120, 75, 120),
    "Indoor": (72, 78, 92),
    "Unknown": (80, 84, 90),
}

pygame.mouse.set_visible(False)


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def text_size(text, font=FONT):
    return font.size(str(text))


def draw_text(text, x, y, font=FONT, color=TEXT, max_width=None):
    s = str(text)
    if max_width is not None:
        while font.size(s)[0] > max_width and len(s) > 3:
            s = s[:-4] + "..."
    img = font.render(s, True, color)
    SCREEN.blit(img, (x, y))
    return img.get_rect(topleft=(x, y))


def wrap_text(text, font, width):
    words = str(text).split()
    lines = []
    line = ""
    for word in words:
        trial = word if not line else line + " " + word
        if font.size(trial)[0] <= width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_wrapped(text, rect, font=FONT, color=TEXT, gap=3):
    y = rect.y
    for line in wrap_text(text, font, rect.width):
        if y + font.get_height() > rect.bottom:
            break
        draw_text(line, rect.x, y, font, color, rect.width)
        y += font.get_height() + gap
    return y


def panel(rect, title=None):
    rect = pygame.Rect(rect)
    pygame.draw.rect(SCREEN, PANEL, rect, border_radius=10)
    pygame.draw.rect(SCREEN, (83, 96, 116), rect, 1, border_radius=10)
    if title:
        draw_text(title, rect.x + 14, rect.y + 10, FONT_BOLD, GOLD, rect.width - 28)
    return rect


def draw_tennis_court_background(surface_name="Clay"):
    court_color = SURFACE_COLORS.get(surface_name, CLAY)
    SCREEN.fill(BG)
    pygame.draw.rect(SCREEN, DARK_GREEN, (0, 0, WIDTH, 82))
    header = FONT_TITLE.render("ATP SIM", True, TEXT)
    SCREEN.blit(header, (WIDTH // 2 - header.get_width() // 2, 18))
    # Stadium band and court image-like area
    pygame.draw.rect(SCREEN, (232, 231, 218), (0, 82, WIDTH, 70))
    pygame.draw.rect(SCREEN, (20, 28, 37), (0, 152, WIDTH, 230))
    pygame.draw.rect(SCREEN, court_color, (0, 382, WIDTH, HEIGHT - 382))
    # perspective court, no foreground clutter on home
    line = (245, 239, 218)
    cx = WIDTH // 2
    pygame.draw.polygon(SCREEN, (max(court_color[0]-20,0), max(court_color[1]-20,0), max(court_color[2]-20,0)),
                        [(130, HEIGHT-40), (1150, HEIGHT-40), (900, 420), (380, 420)])
    for pts in [((130, HEIGHT-40),(380,420)), ((1150,HEIGHT-40),(900,420)), ((cx,HEIGHT-40),(cx,420)),
                ((235,HEIGHT-115),(1045,HEIGHT-115)), ((380,420),(900,420))]:
        pygame.draw.line(SCREEN, line, pts[0], pts[1], 2)


def draw_ball_cursor():
    x, y = pygame.mouse.get_pos()
    pygame.draw.circle(SCREEN, (224, 235, 70), (x, y), 8)
    pygame.draw.arc(SCREEN, WHITE, (x - 7, y - 7, 14, 14), 1.1, 2.5, 2)
    pygame.draw.arc(SCREEN, WHITE, (x - 7, y - 7, 14, 14), 4.25, 5.7, 2)


class Button:
    def __init__(self, rect, text, color=BLUE, selected=False):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.selected = selected
        self.enabled = True

    def handle(self, event):
        return self.enabled and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

    def draw(self):
        color = GREEN if self.selected else self.color
        if not self.enabled:
            color = PANEL_3
        pygame.draw.rect(SCREEN, color, self.rect, border_radius=8)
        pygame.draw.rect(SCREEN, GOLD if self.selected else (104, 117, 138), self.rect, 2 if self.selected else 1, border_radius=8)
        lines = wrap_text(self.text, FONT_BOLD, self.rect.width - 14)
        line_h = FONT_BOLD.get_height()
        y = self.rect.centery - (len(lines) * line_h) // 2
        for line in lines:
            img = FONT_BOLD.render(line, True, TEXT if self.enabled else MUTED)
            SCREEN.blit(img, (self.rect.centerx - img.get_width() // 2, y))
            y += line_h


class TextInput:
    def __init__(self, rect, placeholder=""):
        self.rect = pygame.Rect(rect)
        self.text = ""
        self.placeholder = placeholder
        self.active = False

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.active = False
            elif len(event.unicode) == 1:
                self.text += event.unicode

    def draw(self):
        pygame.draw.rect(SCREEN, PANEL_2, self.rect, border_radius=7)
        pygame.draw.rect(SCREEN, GOLD if self.active else (95, 108, 128), self.rect, 1, border_radius=7)
        display = self.text if self.text else self.placeholder
        color = TEXT if self.text else MUTED
        draw_text(display, self.rect.x + 12, self.rect.y + 10, FONT, color, self.rect.width - 24)


class ScrollList:
    def __init__(self, rect, items=None, row_h=34):
        self.rect = pygame.Rect(rect)
        self.items = items or []
        self.row_h = row_h
        self.offset = 0
        self.selected = 0

    def set_items(self, items):
        self.items = list(items)
        self.offset = 0
        self.selected = 0 if self.items else -1

    def selected_item(self):
        if 0 <= self.selected < len(self.items):
            return self.items[self.selected]
        return None

    def handle(self, event):
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
            self.offset = clamp(self.offset - event.y, 0, max(0, len(self.items) - self.visible_rows()))
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            idx = self.offset + (event.pos[1] - self.rect.y) // self.row_h
            if 0 <= idx < len(self.items):
                self.selected = idx

    def visible_rows(self):
        return max(1, self.rect.height // self.row_h)

    def draw(self, label_func=str):
        pygame.draw.rect(SCREEN, PANEL_2, self.rect, border_radius=8)
        rows = self.visible_rows()
        for r in range(rows):
            idx = self.offset + r
            if idx >= len(self.items):
                break
            y = self.rect.y + r * self.row_h
            row_rect = pygame.Rect(self.rect.x + 4, y + 3, self.rect.width - 8, self.row_h - 6)
            if idx == self.selected:
                pygame.draw.rect(SCREEN, GREEN, row_rect, border_radius=6)
            draw_text(label_func(self.items[idx]), row_rect.x + 9, row_rect.y + 5, FONT_SM, TEXT, row_rect.width - 18)
        if len(self.items) > rows:
            bar_h = max(24, int(self.rect.height * rows / len(self.items)))
            top = self.rect.y + int((self.rect.height - bar_h) * self.offset / max(1, len(self.items) - rows))
            pygame.draw.rect(SCREEN, GOLD, (self.rect.right - 8, top, 4, bar_h), border_radius=2)


def safe_player_label(p):
    rank = getattr(p, "atp_ranking", 0)
    if rank:
        return "#{} {}".format(rank, p.name)
    return p.name


def stat_value(player, key):
    return int(getattr(player, key, 0))


class App:
    def __init__(self):
        self.screen = "home"
        self.players = self.load_players()
        self.tournaments = self.load_tournaments()
        self.tour = self.load_tour()
        self.last_week_results = []
        self.rank_snapshot = self.rank_map()
        self.grand_slam_winners = []
        self.season_status = "Ready."
        self.season_update_count = 0
        self.season_last_week = None
        self.tournament_status = "Select a tournament."
        self.tournament_brackets = {}
        self.current_week = getattr(self.tour, "current_week", 1) if self.tour else 1

        self.home_btn = Button((500, 430, 280, 64), "Enter tour hub", GREEN)
        self.hub_buttons = [
            Button((430, 330, 420, 70), "Sim a match", GREEN),
            Button((430, 420, 420, 70), "Sim a tournament", BLUE),
            Button((430, 510, 420, 70), "Sim a season", BLUE),
        ]
        self.back_btn = Button((20, 92, 120, 48), "Back", PANEL_3)
        self.home_nav_btn = Button((152, 92, 120, 48), "Home", PANEL_3)

        self.search_a = TextInput((40, 150, 500, 44), "Search player A...")
        self.search_b = TextInput((740, 150, 500, 44), "Search player B...")
        self.list_a = ScrollList((40, 205, 500, 380), self.players)
        self.list_b = ScrollList((740, 205, 500, 380), self.players)
        if len(self.players) > 1:
            self.list_b.selected = 1
        self.best_of = 3
        self.best3_btn = Button((555, 295, 170, 48), "Best of 3", GREEN, True)
        self.best5_btn = Button((555, 355, 170, 48), "Best of 5", BLUE, False)
        self.start_match_btn = Button((540, 520, 200, 60), "Start match", GREEN)

        self.tournament_list = ScrollList((40, 160, 360, 470), self.tournaments, 34)
        self.zoom_round = 0
        self.round_buttons = []
        self.run_tournament_btn = Button((40, 642, 180, 48), "Sim selected", GREEN)
        self.zoom_left = Button((240, 642, 80, 48), "<", PANEL_3)
        self.zoom_right = Button((330, 642, 80, 48), ">", PANEL_3)

        self.next_week_btn = Button((40, 620, 210, 52), "Sim next week", GREEN)

        self.match = None
        self.player_a = None
        self.player_b = None
        self.game_log = []
        self.selected_tactic = "Baseline Defense"
        self.selected_target = "Body"
        self.tactic_buttons = []
        self.target_buttons = []
        self.continue_btn = Button((530, 642, 180, 50), "Continue", GREEN)
        self.finish_btn = Button((728, 642, 180, 50), "Finish match", RED)
        self.to_home_btn = Button((530, 642, 260, 50), "Back to main screen", GREEN)
        self.last_choice_desc = "Choose a tactic and target for the next game."
        self.refresh_tactic_buttons()

    def load_players(self):
        players = []
        seen = set()
        for pattern in ["Sim/**/*.json", "Data/**/*.json", "*.json"]:
            for path in glob.glob(pattern, recursive=True):
                try:
                    p = load_player(path)
                    if p.name and p.name not in seen:
                        seen.add(p.name)
                        players.append(p)
                except Exception:
                    pass
        if not players:
            try:
                import pandas as pd
                df = pd.read_csv("Data/atp_db_31_12_2018.csv", delimiter=";", decimal=",")
                names = sorted(set(df["PLAYER"].values.tolist()))
                for name in names:
                    try:
                        p = create_player_from_database(name=name, db=df)
                        players.append(p)
                    except Exception:
                        pass
            except Exception:
                pass
        players.sort(key=lambda p: (getattr(p, "atp_ranking", 99999) or 99999, p.name))
        for idx, p in enumerate(players):
            if not getattr(p, "atp_ranking", 0):
                p.atp_ranking = idx + 1
        return players

    def load_tournaments(self):
        try:
            return load_calendar(season=2019)
        except Exception:
            return []

    def load_tour(self):
        try:
            return AtpTour()
        except Exception:
            return None

    def rank_map(self):
        source = self.tour.all_players if self.tour and getattr(self.tour, "all_players", None) else self.players
        return {p.name: getattr(p, "atp_ranking", 9999) for p in source}

    def top_players(self):
        source = self.tour.all_players if self.tour and getattr(self.tour, "all_players", None) else self.players
        return sorted(source, key=lambda p: getattr(p, "atp_ranking", 9999))[:20]

    def refresh_tactic_buttons(self):
        names = list(TACTICS.keys())
        self.tactic_buttons = []
        x0, y0 = 430, 424
        for i, name in enumerate(names):
            row = i // 2
            col = i % 2
            self.tactic_buttons.append(Button((x0 + col * 215, y0 + row * 58, 200, 48), name, BLUE, name == self.selected_tactic))
        self.target_buttons = []
        for i, name in enumerate(TARGETS.keys()):
            self.target_buttons.append(Button((430 + i * 145, 550, 130, 44), name, PANEL_3, name == self.selected_target))

    def go_home(self):
        self.screen = "home"

    def handle_global_nav(self, event):
        if self.screen not in ["home"]:
            if self.back_btn.handle(event):
                self.screen = "hub"
            if self.home_nav_btn.handle(event):
                self.go_home()

    def handle(self, event):
        self.handle_global_nav(event)
        if self.screen == "home":
            if self.home_btn.handle(event):
                self.screen = "hub"
        elif self.screen == "hub":
            for i, b in enumerate(self.hub_buttons):
                if b.handle(event):
                    self.screen = ["match_select", "tournament", "season"][i]
        elif self.screen == "match_select":
            self.search_a.handle(event)
            self.search_b.handle(event)
            self.update_filtered_players()
            self.list_a.handle(event)
            self.list_b.handle(event)
            if self.best3_btn.handle(event):
                self.best_of = 3
            if self.best5_btn.handle(event):
                self.best_of = 5
            self.best3_btn.selected = self.best_of == 3
            self.best5_btn.selected = self.best_of == 5
            if self.start_match_btn.handle(event):
                self.start_match()
        elif self.screen == "match_play":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.advance_game()
            for b in self.tactic_buttons:
                if b.handle(event):
                    self.selected_tactic = b.text
                    self.refresh_tactic_buttons()
            for b in self.target_buttons:
                if b.handle(event):
                    self.selected_target = b.text
                    self.refresh_tactic_buttons()
            if self.match and self.match.simulation_finished:
                if self.to_home_btn.handle(event):
                    self.screen = "hub"
            else:
                if self.continue_btn.handle(event):
                    self.advance_game()
                if self.finish_btn.handle(event):
                    self.finish_match()
        elif self.screen == "tournament":
            self.tournament_list.handle(event)
            if self.zoom_left.handle(event):
                self.zoom_round = max(0, self.zoom_round - 1)
            if self.zoom_right.handle(event):
                self.zoom_round = min(6, self.zoom_round + 1)
            if self.run_tournament_btn.handle(event):
                self.sim_selected_tournament()
        elif self.screen == "season":
            if self.next_week_btn.handle(event):
                self.sim_next_week()

    def update_filtered_players(self):
        qa = self.search_a.text.lower().strip()
        qb = self.search_b.text.lower().strip()
        if qa:
            self.list_a.set_items([p for p in self.players if qa in p.name.lower()])
        if qb:
            self.list_b.set_items([p for p in self.players if qb in p.name.lower()])

    def start_match(self):
        a = self.list_a.selected_item()
        b = self.list_b.selected_item()
        if not a or not b or a.name == b.name:
            return
        self.player_a = copy.deepcopy(a)
        self.player_b = copy.deepcopy(b)
        for p in [self.player_a, self.player_b]:
            try:
                p.initialize_stats("Clay")
            except Exception:
                # direct JSON players may already have active stats
                pass
        self.match = MatchSimulation(best_of_sets=self.best_of)
        self.match.initialize_simulation(self.player_a, self.player_b)
        self.game_log = ["Match ready. Press SPACE or Continue."]
        self.last_choice_desc = "Choose a tactic and target for the next game."
        self.screen = "match_play"

    def advance_game(self):
        if not self.match or self.match.simulation_finished:
            return
        server = self.match.point_simulation.server.name
        is_player_a_serving = server == self.player_a.name
        modifier = build_player_modifier(self.selected_tactic, self.selected_target, is_player_a_serving)
        result = self.match.simulate_next_game(modifiers={self.player_a.name: modifier})
        summary = result.get("last_game_summary", "Game played.")
        self.last_choice_desc = describe_choice(self.selected_tactic, self.selected_target)
        self.game_log.append(summary)
        self.game_log = self.game_log[-12:]

    def finish_match(self):
        guard = 0
        while self.match and not self.match.simulation_finished and guard < 80:
            self.advance_game()
            guard += 1

    def sim_selected_tournament(self):
        t = self.tournament_list.selected_item()
        if not t:
            return
        try:
            source = self.tour.all_players if self.tour and getattr(self.tour, "all_players", None) else self.players
            t.players = source
            t.create_draw()
            t.play_qualification()
            t.create_main_draw()
            bracket_rounds = [list(t.draw)]
            t.round_of_play = 1
            while len(t.draw) > t.cutoff:
                t.draw = t.play_round()
                bracket_rounds.append(list(t.draw))
                t.round_of_play += 1
            if t.draw:
                t.award_points(player_name=t.draw[0], tournament_winner=True)
            self.tournament_brackets[id(t)] = bracket_rounds
            self.zoom_round = min(self.zoom_round, max(0, len(bracket_rounds) - 1))
            winner = t.draw[0] if getattr(t, "draw", None) else "-"
            self.tournament_status = "{} simulated. Winner: {}".format(t.name, winner)
        except Exception as exc:
            self.tournament_status = "Tournament sim failed: {}".format(exc)

    def sim_next_week(self):
        """Advance the season screen by one playable calendar week.

        This version does not silently depend on AtpTour.play_a_week(). It uses
        the same original Tournament/Player objects, captures winners, refreshes
        rankings, and updates visible UI fields every time the button is clicked.
        If a calendar week has no tournaments, it still advances and tells the UI.
        """
        try:
            self.season_update_count += 1

            players = None
            tournaments = None
            if self.tour and getattr(self.tour, "all_players", None):
                players = self.tour.all_players
            else:
                players = self.players

            if self.tour and getattr(self.tour, "all_tournaments", None):
                tournaments = self.tour.all_tournaments
            else:
                tournaments = self.tournaments

            if not players:
                self.season_status = "No players loaded. Season cannot advance."
                return
            if not tournaments:
                self.season_status = "No tournaments loaded. Season cannot advance."
                return

            week = int(getattr(self.tour, "current_week", self.current_week) if self.tour else self.current_week)
            if week < 1 or week > 52:
                week = 1

            previous_ranks = {}
            for p in players:
                previous_ranks[p.name] = int(getattr(p, "atp_ranking", 9999) or 9999)

            week_tournaments = []
            for t in tournaments:
                try:
                    if int(getattr(t, "week", 0) or 0) == week:
                        week_tournaments.append(t)
                except Exception:
                    pass

            self.last_week_results = []

            if not week_tournaments:
                next_week = week + 1
                if next_week > 52:
                    next_week = 1
                self.current_week = next_week
                if self.tour:
                    self.tour.current_week = next_week
                self.rank_snapshot = previous_ranks
                self.season_last_week = week
                self.season_status = "Click {}: week {} had no tournaments. Now week {}.".format(
                    self.season_update_count, week, next_week
                )
                return

            for t in week_tournaments:
                try:
                    # Reset mutable tournament state so repeated UI sims do not get
                    # stuck on a previous champion/draw.
                    t.round_of_play = 1
                    t.seeded_players = []
                    t.direct_acceptances = []
                    t.wild_cards = []
                    t.qualifiers = []
                    t.draw = []
                    t.losers = []
                    t.winners = []
                    t.players = players

                    t.run_tournament(available_players=players)

                    winner = None
                    if getattr(t, "draw", None) and len(t.draw) == 1:
                        winner = t.draw[0]
                    elif getattr(t, "winners", None):
                        winner = t.winners[0] if t.winners else None
                    if not winner:
                        winner = "No winner recorded"

                    self.last_week_results.append((
                        getattr(t, "name", "Tournament"),
                        winner,
                        getattr(t, "surface", ""),
                        getattr(t, "tournament_level", ""),
                    ))
                    if getattr(t, "tournament_level", "") == "GRAND_SLAM":
                        season = getattr(self.tour, "current_season", 2029) if self.tour else 2029
                        self.grand_slam_winners.append((getattr(t, "name", "Grand Slam"), winner, season))
                except Exception as tournament_exc:
                    self.last_week_results.append((
                        getattr(t, "name", "Tournament"),
                        "ERROR: {}".format(tournament_exc),
                        getattr(t, "surface", ""),
                        getattr(t, "tournament_level", ""),
                    ))

            # Ranking refresh. Prefer the original AtpTour post-week pipeline when
            # available, otherwise apply the equivalent local minimum.
            if self.tour:
                try:
                    self.tour.weekly_data_processing()
                except Exception:
                    try:
                        self.tour.sort_player_rankings()
                        self.tour.release_players_from_tournaments()
                    except Exception:
                        pass
            else:
                players.sort(key=lambda p: (-int(getattr(p, "singles_race_points", 0) or 0),
                                            -int(getattr(p, "tournament_wins", 0) or 0),
                                            -int(getattr(p, "wins", 0) or 0),
                                            p.name))
                for idx, p in enumerate(players):
                    p.atp_ranking = idx + 1
                    p.current_tournament = ""
                    p.singles_race_points_updated = False

            next_week = week + 1
            if next_week > 52:
                next_week = 1
            self.current_week = next_week
            if self.tour:
                self.tour.current_week = next_week

            self.rank_snapshot = previous_ranks
            self.season_last_week = week
            winners = [r for r in self.last_week_results if not str(r[1]).startswith("ERROR:")]
            self.season_status = "Click {}: week {} simulated. {} tournaments, {} winners. Now week {}.".format(
                self.season_update_count, week, len(week_tournaments), len(winners), next_week
            )

        except Exception as exc:
            self.season_status = "Click {} failed: {}".format(self.season_update_count, exc)

    def draw_nav(self):
        if self.screen != "home":
            self.back_btn.draw()
            self.home_nav_btn.draw()

    def draw(self):
        surface = "Clay"
        if self.screen == "tournament":
            t = self.tournament_list.selected_item()
            surface = getattr(t, "surface", "Clay") if t else "Clay"
        draw_tennis_court_background(surface)
        if self.screen == "home":
            self.draw_home()
        elif self.screen == "hub":
            self.draw_hub()
        elif self.screen == "match_select":
            self.draw_match_select()
        elif self.screen == "match_play":
            self.draw_match_play()
        elif self.screen == "tournament":
            self.draw_tournament()
        elif self.screen == "season":
            self.draw_season()
        self.draw_nav()
        draw_ball_cursor()

    def draw_home(self):
        r = panel((350, 210, 580, 360))
        title = "ATP Sim Pygame prototype"
        title_img = FONT_BIG.render(title, True, TEXT)
        SCREEN.blit(title_img, (r.centerx - title_img.get_width() // 2, r.y + 72))
        draw_wrapped(
            "Match, tournament, and season simulation from your Python engine.",
            pygame.Rect(r.x + 70, r.y + 126, r.width - 140, 90),
            FONT,
            MUTED,
            6,
        )
        self.home_btn.draw()
        info = "Players loaded: {}   |   Tournaments loaded: {}".format(len(self.players), len(self.tournaments))
        info_img = FONT_SM.render(info, True, MUTED)
        SCREEN.blit(info_img, (WIDTH // 2 - info_img.get_width() // 2, HEIGHT - 34))

    def draw_hub(self):
        r = panel((360, 180, 560, 470), "TOUR HUB")
        draw_wrapped(
            "Choose what to simulate. Match mode is tactical and game-by-game. Tournament and season modes use your ATP tour engine.",
            pygame.Rect(r.x + 40, r.y + 58, r.width - 80, 110),
            FONT,
            MUTED,
            6,
        )
        for b in self.hub_buttons:
            b.draw()

    def draw_match_select(self):
        draw_text("Select Player A and Player B", 40, 100, FONT_BIG, TEXT, 700)
        draw_text("Choose match length, then start a stepwise tactical match.", 40, 132, FONT_SM, MUTED, 760)
        self.search_a.draw(); self.search_b.draw()
        self.list_a.draw(safe_player_label); self.list_b.draw(safe_player_label)
        panel((555, 220, 170, 260), "FORMAT")
        self.best3_btn.draw(); self.best5_btn.draw(); self.start_match_btn.draw()

    def draw_scorebug(self):
        if not self.match:
            return
        a = self.player_a.name
        b = self.player_b.name
        bug = pygame.Rect(32, 95, 480, 82)
        pygame.draw.rect(SCREEN, DARK_GREEN, bug, border_radius=3)
        pygame.draw.rect(SCREEN, GOLD, bug, 1, border_radius=3)
        colx = [290, 335, 380, 430]
        draw_text(a.upper(), bug.x + 16, bug.y + 10, FONT_BOLD, TEXT, 250)
        draw_text(b.upper(), bug.x + 16, bug.y + 45, FONT_BOLD, TEXT, 250)
        for i, set_score in enumerate(self.match.match_score[-3:]):
            draw_text(str(set_score[0]), colx[i], bug.y + 10, FONT_BOLD, TEXT)
            draw_text(str(set_score[1]), colx[i], bug.y + 45, FONT_BOLD, TEXT)
        draw_text(str(self.match.games_score[0]), colx[2], bug.y + 10, FONT_BOLD, GOLD)
        draw_text(str(self.match.games_score[1]), colx[2], bug.y + 45, FONT_BOLD, GOLD)
        pts = self.match.format_points_score()
        draw_text(str(pts[0]), colx[3], bug.y + 10, FONT_BOLD, TEXT)
        draw_text(str(pts[1]), colx[3], bug.y + 45, FONT_BOLD, TEXT)

    def player_panel(self, rect, player, stats, title):
        panel(rect, title)
        draw_text(player.name, rect.x + 14, rect.y + 42, FONT_BOLD, TEXT, rect.width - 110)
        draw_text("#{}".format(getattr(player, "atp_ranking", "-")), rect.right - 75, rect.y + 42, FONT_BOLD, GOLD)
        left = rect.x + 14
        right = rect.x + rect.width // 2 + 18
        y = rect.y + 82
        draw_text("Base stats", left, y, FONT_SM, GOLD); draw_text("Match trackers", right, y, FONT_SM, GOLD)
        y += 28
        base = [("Ace", "ace"), ("Double fault", "double_fault"), ("1st in", "first_serve_in"), ("1st won", "first_serve_won"), ("2nd won", "second_serve_won"), ("BP saved", "break_point_saved"), ("1st return", "return_first_serve_won"), ("2nd return", "return_second_serve_won"), ("BP won", "break_point_won")]
        track = [("Aces", "ace"), ("DF", "double_fault"), ("1st in", "1st_serve_in"), ("1st won", "1st_serve_won"), ("2nd won", "2nd_serve_won"), ("BP faced", "break_point_faced"), ("BP saved", "break_point_saved"), ("BP opp", "break_point_oppy"), ("BP won", "break_point_won")]
        for i, (label, key) in enumerate(base[:9]):
            draw_text("{}: {}".format(label, stat_value(player, key)), left, y + i * 22, FONT_SM, MUTED, rect.width//2 - 24)
        for i, (label, key) in enumerate(track[:9]):
            draw_text("{}: {}".format(label, stats.get(key, 0)), right, y + i * 22, FONT_SM, MUTED, rect.width//2 - 24)

    def draw_match_play(self):
        draw_text("Tactical match", 40, 100, FONT_BIG, TEXT)
        self.draw_scorebug()
        if not self.match:
            return
        self.player_panel(pygame.Rect(30, 195, 350, 405), self.player_a, self.match.player_a_stats, "PLAYER A")
        self.player_panel(pygame.Rect(900, 195, 350, 405), self.player_b, self.match.player_b_stats, "PLAYER B")
        mid = panel((405, 195, 470, 405), "NEXT GAME STRATEGY")
        server = self.match.point_simulation.server.name if self.match.point_simulation else "-"
        draw_text("Server: {}".format(server), mid.x + 14, mid.y + 42, FONT_BOLD, GOLD, mid.width - 28)
        draw_wrapped(self.last_choice_desc, pygame.Rect(mid.x + 14, mid.y + 75, mid.width - 28, 70), FONT_SM, MUTED)
        for b in self.tactic_buttons:
            b.draw()
        for b in self.target_buttons:
            b.draw()
        log_r = panel((405, 610, 470, 82), "GAME LOG")
        recent = self.game_log[-2:]
        y = log_r.y + 34
        for line in recent:
            draw_text(line, log_r.x + 12, y, FONT_SM, TEXT, log_r.width - 24)
            y += 22
        if self.match.simulation_finished:
            draw_text("Winner: {}".format(self.match.match_winner), 520, 610, FONT_BOLD, GOLD, 360)
            self.to_home_btn.draw()
        else:
            self.continue_btn.draw(); self.finish_btn.draw()

    def draw_tournament(self):
        draw_text("Tournament simulation", 40, 100, FONT_BIG, TEXT)
        draw_text("Select a tournament. Surface changes the court background. Bracket rounds can be zoomed with arrows.", 40, 132, FONT_SM, MUTED, 900)
        self.tournament_list.draw(lambda t: "W{}  {}  ({}, {})".format(t.week, t.name, t.surface, t.tournament_level))
        t = self.tournament_list.selected_item()
        right = panel((430, 160, 810, 470), "BRACKET")
        if t:
            draw_text("{} | {} | {} draw".format(t.name, t.surface, t.main_draw_size), right.x + 14, right.y + 40, FONT_BOLD, TEXT, right.width - 28)
            self.draw_bracket(right, t)
        self.run_tournament_btn.draw(); self.zoom_left.draw(); self.zoom_right.draw()
        draw_text(self.tournament_status, 430, 655, FONT_SM, MUTED, 760)

    def bracket_round_name(self, remaining_count):
        if remaining_count <= 1:
            return "Champion"
        if remaining_count == 2:
            return "Final"
        if remaining_count == 4:
            return "Semi-finals"
        if remaining_count == 8:
            return "Quarter-finals"
        if remaining_count == 16:
            return "Round of 16"
        if remaining_count == 32:
            return "Round of 32"
        if remaining_count == 64:
            return "Round of 64"
        if remaining_count == 128:
            return "Round of 128"
        return "{} players left".format(remaining_count)

    def draw_bracket(self, rect, t):
        bracket_rounds = self.tournament_brackets.get(id(t), None)
        if bracket_rounds:
            max_idx = max(0, len(bracket_rounds) - 1)
            self.zoom_round = clamp(self.zoom_round, 0, max_idx)
            items = list(bracket_rounds[self.zoom_round])
        else:
            draw = list(getattr(t, "draw", []) or [])
            if not draw:
                names = []
                names.extend(getattr(t, "direct_acceptances", []) or [])
                names.extend(getattr(t, "qualifiers", []) or [])
                names.extend(getattr(t, "wild_cards", []) or [])
                draw = names[:getattr(t, "main_draw_size", 32)]
            if not draw:
                draw = ["Player {}".format(i + 1) for i in range(min(32, getattr(t, "main_draw_size", 32) or 32))]
            max_players = min(32, len(draw))
            round_size = max(1, max_players // (2 ** self.zoom_round))
            items = draw[:round_size]

        x = rect.x + 20
        y = rect.y + 88
        w = rect.width - 40
        row_h = 34 if len(items) <= 16 else 22
        title = self.bracket_round_name(len(items))
        draw_text(title, x, y - 28, FONT_BOLD, GOLD)

        if len(items) == 1:
            champ = pygame.Rect(x, y, min(420, w), 60)
            pygame.draw.rect(SCREEN, (235, 235, 235), champ, border_radius=6)
            draw_text("Winner: {}".format(items[0]), champ.x + 12, champ.y + 18, FONT_BOLD, BLACK, champ.width - 24)
            return

        for i in range(0, len(items), 2):
            block = pygame.Rect(x, y + (i // 2) * (row_h * 2 + 10), min(390, w), row_h * 2 + 4)
            if block.bottom > rect.bottom - 10:
                break
            pygame.draw.rect(SCREEN, (235, 235, 235), block, border_radius=6)
            pygame.draw.line(SCREEN, (180, 180, 180), (block.x + 10, block.y + row_h), (block.right - 10, block.y + row_h), 1)
            draw_text(str(items[i]), block.x + 12, block.y + 6, FONT_SM, BLACK, block.width - 24)
            if i + 1 < len(items):
                draw_text(str(items[i + 1]), block.x + 12, block.y + row_h + 6, FONT_SM, BLACK, block.width - 24)
            if block.right + 40 < rect.right:
                midy = block.centery
                pygame.draw.line(SCREEN, GOLD, (block.right, midy), (block.right + 35, midy), 2)

    def draw_season(self):
        draw_text("Season simulation", 40, 100, FONT_BIG, TEXT)
        week_value = getattr(self.tour, "current_week", self.current_week) if self.tour else self.current_week
        week_text = "Current week: {}".format(week_value)
        draw_text(week_text, 40, 135, FONT_BOLD, GOLD)
        draw_text("Updates: {}".format(self.season_update_count), 220, 135, FONT_BOLD, GOLD)
        draw_text(self.season_status, 360, 138, FONT_SM, TEXT, 850)

        left = panel((30, 170, 430, 430), "TOP 20 RANKINGS")
        y = left.y + 42
        for p in self.top_players():
            rank = getattr(p, "atp_ranking", 0)
            pts = getattr(p, "singles_race_points", getattr(p, "atp_points", 0))
            draw_text("#{:<2}".format(rank), left.x + 16, y, FONT_SM, MUTED, 44)
            draw_text(p.name, left.x + 70, y, FONT_SM, TEXT, 235)
            draw_text("{:>5} pts".format(pts), left.x + 315, y, FONT_SM, MUTED, 95)
            y += 19

        mid = panel((480, 170, 360, 430), "LAST SIMULATED WEEK")
        y = mid.y + 42
        if self.season_last_week is not None:
            draw_text("Week {}".format(self.season_last_week), mid.x + 14, y, FONT_BOLD, GOLD, mid.width - 28)
            y += 30
        if self.last_week_results:
            for name, winner, surface, level in self.last_week_results[:12]:
                draw_text(name, mid.x + 14, y, FONT_SM, TEXT, 170)
                draw_text(winner, mid.x + 190, y, FONT_SM, GOLD, 150)
                y += 24
        else:
            draw_wrapped("No tournament week simulated yet. Clicking the button will now visibly advance the week even if the calendar week is empty.", pygame.Rect(mid.x + 14, y, mid.width - 28, 110), FONT_SM, MUTED)

        right = panel((860, 170, 390, 430), "MOVERS / GRAND SLAMS")
        movers, fallers = self.get_movers()
        y = right.y + 42
        draw_text("Top 5 movers", right.x + 14, y, FONT_SM, GOLD)
        y += 24
        if movers:
            for p, delta in movers:
                draw_text("+{}  {}".format(delta, p.name), right.x + 14, y, FONT_SM, TEXT, right.width - 28)
                y += 22
        else:
            draw_text("No positive movement yet", right.x + 14, y, FONT_SM, MUTED, right.width - 28)
            y += 22
        y += 8
        draw_text("Top 5 losers", right.x + 14, y, FONT_SM, GOLD)
        y += 24
        if fallers:
            for p, delta in fallers:
                draw_text("-{}  {}".format(abs(delta), p.name), right.x + 14, y, FONT_SM, TEXT, right.width - 28)
                y += 22
        else:
            draw_text("No negative movement yet", right.x + 14, y, FONT_SM, MUTED, right.width - 28)
            y += 22
        y += 8
        draw_text("Grand Slam winners", right.x + 14, y, FONT_SM, GOLD)
        y += 24
        if self.grand_slam_winners:
            for name, winner, season in self.grand_slam_winners[-6:]:
                draw_text("{}: {}".format(name, winner), right.x + 14, y, FONT_SM, MUTED, right.width - 28)
                y += 22
        else:
            draw_text("None recorded yet", right.x + 14, y, FONT_SM, MUTED, right.width - 28)

        self.next_week_btn.draw()
        draw_text("Button clicks registered: {}".format(self.season_update_count), 270, 635, FONT_SM, GOLD, 420)

    def get_movers(self):
        if not self.tour:
            return [], []
        changes = []
        for p in self.tour.all_players:
            old = self.rank_snapshot.get(p.name, p.atp_ranking)
            delta = old - p.atp_ranking
            changes.append((p, delta))
        movers = sorted([x for x in changes if x[1] > 0], key=lambda x: -x[1])[:5]
        fallers = sorted([x for x in changes if x[1] < 0], key=lambda x: x[1])[:5]
        return movers, fallers

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle(event)
            self.draw()
            pygame.display.flip()
            CLOCK.tick(FPS)
        pygame.quit()


if __name__ == "__main__":
    App().run()
