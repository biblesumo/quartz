#!/usr/bin/env python3
"""
Fast Skat Double Dummy Solver
Optimized version for running 1000 hand simulations.
"""

import random
import time
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum

class Suit(Enum):
    CLUBS = "C"
    SPADES = "S" 
    HEARTS = "H"
    DIAMONDS = "D"

class Rank(Enum):
    ACE = "A"
    TEN = "10"
    KING = "K"
    QUEEN = "Q"
    JACK = "J"
    NINE = "9"
    EIGHT = "8"
    SEVEN = "7"

@dataclass
class Card:
    suit: Suit
    rank: Rank
    
    def __str__(self):
        return f"{self.rank.value}{self.suit.value}"
    
    def __hash__(self):
        return hash((self.suit, self.rank))

class FastSkatGame:
    """Optimized Skat game state for fast simulation."""
    
    def __init__(self, declarer_hand: List[Card], left_opponent: List[Card], 
                 right_opponent: List[Card], skat: List[Card], trump_suit: Suit):
        self.declarer_hand = declarer_hand.copy()
        self.left_opponent = left_opponent.copy()
        self.right_opponent = right_opponent.copy()
        self.skat = skat.copy()
        self.trump_suit = trump_suit
        
        # Game state
        self.current_trick: List[Tuple[int, Card]] = []
        self.lead_player = 0
        self.tricks_won = [0, 0, 0]
        self.points_won = [0, 0, 0]
        self.trick_number = 0
        
    def get_card_value(self, card: Card) -> int:
        """Get point value of a card."""
        if card.rank == Rank.ACE:
            return 11
        elif card.rank == Rank.TEN:
            return 10
        elif card.rank == Rank.KING:
            return 4
        elif card.rank == Rank.QUEEN:
            return 3
        else:
            return 0
    
    def is_trump(self, card: Card) -> bool:
        """Check if a card is trump."""
        return (card.rank == Rank.JACK or 
                (card.suit == self.trump_suit and card.rank != Rank.JACK))
    
    def get_trump_rank(self, card: Card) -> int:
        """Get trump ranking for comparison."""
        if card.rank == Rank.JACK:
            jack_order = {Suit.CLUBS: 4, Suit.SPADES: 3, Suit.HEARTS: 2, Suit.DIAMONDS: 1}
            return jack_order[card.suit]
        elif card.suit == self.trump_suit:
            trump_order = {Rank.ACE: 7, Rank.TEN: 6, Rank.KING: 5, Rank.QUEEN: 4,
                          Rank.NINE: 3, Rank.EIGHT: 2, Rank.SEVEN: 1}
            return trump_order[card.rank]
        else:
            return 0
    
    def get_suit_rank(self, card: Card) -> int:
        """Get suit ranking for non-trump cards."""
        suit_order = {Rank.ACE: 7, Rank.TEN: 6, Rank.KING: 5, Rank.QUEEN: 4,
                     Rank.NINE: 3, Rank.EIGHT: 2, Rank.SEVEN: 1}
        return suit_order[card.rank]
    
    def card_beats(self, card1: Card, card2: Card) -> bool:
        """Check if card1 beats card2."""
        trump1, trump2 = self.is_trump(card1), self.is_trump(card2)
        
        if trump1 and not trump2:
            return True
        elif not trump1 and trump2:
            return False
        elif trump1 and trump2:
            return self.get_trump_rank(card1) > self.get_trump_rank(card2)
        else:
            if card1.suit == card2.suit:
                return self.get_suit_rank(card1) > self.get_suit_rank(card2)
            else:
                return False
    
    def get_legal_moves(self, player: int) -> List[Card]:
        """Get legal moves for a player."""
        if player == 0:
            hand = self.declarer_hand
        elif player == 1:
            hand = self.left_opponent
        else:
            hand = self.right_opponent
        
        if not self.current_trick:
            return hand
        
        lead_card = self.current_trick[0][1]
        lead_suit = lead_card.suit
        
        suit_cards = [card for card in hand if card.suit == lead_suit]
        
        if suit_cards:
            return suit_cards
        else:
            return hand
    
    def play_card(self, player: int, card: Card) -> bool:
        """Play a card and return True if trick is complete."""
        if player == 0:
            if card in self.declarer_hand:
                self.declarer_hand.remove(card)
            else:
                return False
        elif player == 1:
            if card in self.left_opponent:
                self.left_opponent.remove(card)
            else:
                return False
        else:
            if card in self.right_opponent:
                self.right_opponent.remove(card)
            else:
                return False
        
        self.current_trick.append((player, card))
        
        if len(self.current_trick) == 3:
            self.resolve_trick()
            return True
        else:
            self.lead_player = (self.lead_player + 1) % 3
            return False
    
    def resolve_trick(self):
        """Resolve the current trick."""
        if len(self.current_trick) != 3:
            return
        
        winning_card = self.current_trick[0][1]
        winning_player = self.current_trick[0][0]
        
        for player, card in self.current_trick[1:]:
            if self.card_beats(card, winning_card):
                winning_card = card
                winning_player = player
        
        self.tricks_won[winning_player] += 1
        trick_points = sum(self.get_card_value(card) for _, card in self.current_trick)
        self.points_won[winning_player] += trick_points
        
        self.current_trick = []
        self.lead_player = winning_player
        self.trick_number += 1
    
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return (len(self.declarer_hand) == 0 and 
                len(self.left_opponent) == 0 and 
                len(self.right_opponent) == 0)
    
    def get_declarer_points(self) -> int:
        """Get total points won by declarer."""
        return self.points_won[0]
    
    def copy(self):
        """Create a deep copy of the game state."""
        new_game = FastSkatGame(
            self.declarer_hand.copy(),
            self.left_opponent.copy(), 
            self.right_opponent.copy(),
            self.skat.copy(),
            self.trump_suit
        )
        new_game.current_trick = self.current_trick.copy()
        new_game.lead_player = self.lead_player
        new_game.tricks_won = self.tricks_won.copy()
        new_game.points_won = self.points_won.copy()
        new_game.trick_number = self.trick_number
        return new_game

class FastSkatSolver:
    """Fast double dummy solver using simplified search."""
    
    def __init__(self):
        self.nodes_evaluated = 0
    
    def evaluate_position(self, game: FastSkatGame) -> int:
        """Fast position evaluation."""
        if game.is_game_over():
            return game.get_declarer_points()
        
        # Current points
        current_points = game.points_won[0]
        
        # Remaining card values
        declarer_value = sum(game.get_card_value(card) for card in game.declarer_hand)
        
        # Quick win/loss check
        if current_points >= 61:
            return current_points + 100
        
        if current_points + declarer_value < 61:
            return current_points - 100
        
        # Count trumps
        declarer_trumps = sum(1 for card in game.declarer_hand if game.is_trump(card))
        left_trumps = sum(1 for card in game.left_opponent if game.is_trump(card))
        right_trumps = sum(1 for card in game.right_opponent if game.is_trump(card))
        
        # Simple heuristic
        trump_advantage = (declarer_trumps - (left_trumps + right_trumps) / 2) * 5
        
        return current_points + declarer_value + trump_advantage
    
    def minimax_search(self, game: FastSkatGame, depth: int, maximizing: bool) -> int:
        """Simplified minimax search."""
        self.nodes_evaluated += 1
        
        if depth == 0 or game.is_game_over():
            return self.evaluate_position(game)
        
        if maximizing:
            max_eval = float('-inf')
            legal_moves = game.get_legal_moves(game.lead_player)
            
            # Limit search to top moves for speed
            if len(legal_moves) > 5:
                # Sort by card value and take top 5
                legal_moves.sort(key=lambda c: game.get_card_value(c), reverse=True)
                legal_moves = legal_moves[:5]
            
            for card in legal_moves:
                new_game = game.copy()
                new_game.play_card(game.lead_player, card)
                
                if new_game.current_trick:
                    eval_score = self.minimax_search(new_game, depth - 1, True)
                else:
                    eval_score = self.minimax_search(new_game, depth - 1, True)
                
                max_eval = max(max_eval, eval_score)
            
            return max_eval
        else:
            min_eval = float('inf')
            legal_moves = game.get_legal_moves(game.lead_player)
            
            # Limit search to top moves for speed
            if len(legal_moves) > 5:
                legal_moves.sort(key=lambda c: game.get_card_value(c), reverse=True)
                legal_moves = legal_moves[:5]
            
            for card in legal_moves:
                new_game = game.copy()
                new_game.play_card(game.lead_player, card)
                
                if new_game.current_trick:
                    eval_score = self.minimax_search(new_game, depth - 1, False)
                else:
                    eval_score = self.minimax_search(new_game, depth - 1, True)
                
                min_eval = min(min_eval, eval_score)
            
            return min_eval
    
    def solve_game(self, game: FastSkatGame) -> int:
        """Solve a game using fast search."""
        self.nodes_evaluated = 0
        return self.minimax_search(game, 8, True)  # Reduced depth for speed

def create_deck() -> List[Card]:
    """Create a 32-card Skat deck."""
    deck = []
    for suit in Suit:
        for rank in Rank:
            deck.append(Card(suit, rank))
    return deck

def deal_hands() -> Tuple[List[Card], List[Card], List[Card], List[Card]]:
    """Deal random hands."""
    deck = create_deck()
    random.shuffle(deck)
    
    declarer = deck[:10]
    left_opponent = deck[10:20]
    right_opponent = deck[20:30]
    skat = deck[30:32]
    
    return declarer, left_opponent, right_opponent, skat

def optimal_discard(declarer_hand: List[Card], skat: List[Card], trump_suit: Suit) -> Tuple[List[Card], List[Card]]:
    """Find optimal cards to discard."""
    all_cards = declarer_hand + skat
    temp_game = FastSkatGame([], [], [], [], trump_suit)
    
    def score_card(card):
        base_value = temp_game.get_card_value(card)
        is_trump = temp_game.is_trump(card)
        trump_bonus = 20 if is_trump else 0
        jack_bonus = 30 if card.rank == Rank.JACK else 0
        high_bonus = 10 if card.rank in [Rank.ACE, Rank.TEN, Rank.KING] else 0
        return base_value + trump_bonus + jack_bonus + high_bonus
    
    card_scores = [(card, score_card(card)) for card in all_cards]
    card_scores.sort(key=lambda x: x[1], reverse=True)
    
    new_hand = [card for card, _ in card_scores[:10]]
    to_discard = [card for card, _ in card_scores[10:]]
    
    return new_hand, to_discard

def run_fast_simulation(num_hands: int = 1000) -> Dict[str, Dict[str, float]]:
    """Run fast simulation for all trump suits."""
    solver = FastSkatSolver()
    results = {}
    
    trump_suits = [Suit.CLUBS, Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS]
    
    for trump_suit in trump_suits:
        print(f"\nSimulating {num_hands} hands for {trump_suit.value} trump...")
        
        wins = 0
        total_points = 0
        start_time = time.time()
        
        for i in range(num_hands):
            if (i + 1) % 200 == 0:
                print(f"  Hand {i + 1}/{num_hands}")
            
            # Deal and solve
            declarer_hand, left_opponent, right_opponent, skat = deal_hands()
            final_hand, discarded = optimal_discard(declarer_hand, skat, trump_suit)
            game = FastSkatGame(final_hand, left_opponent, right_opponent, discarded, trump_suit)
            
            declarer_points = solver.solve_game(game)
            total_points += declarer_points
            
            if declarer_points >= 61:
                wins += 1
        
        win_percentage = (wins / num_hands) * 100
        avg_points = total_points / num_hands
        elapsed_time = time.time() - start_time
        
        results[trump_suit.value] = {
            'win_percentage': win_percentage,
            'wins': wins,
            'total_hands': num_hands,
            'avg_points': avg_points,
            'elapsed_time': elapsed_time
        }
        
        print(f"  {trump_suit.value}: {win_percentage:.2f}% wins ({wins}/{num_hands})")
        print(f"  Average points: {avg_points:.2f}")
        print(f"  Time: {elapsed_time:.2f}s")
    
    return results

def print_summary(results: Dict[str, Dict[str, float]]):
    """Print simulation results summary."""
    print("\n" + "="*60)
    print("SKAT DOUBLE DUMMY SIMULATION RESULTS")
    print("="*60)
    print(f"{'Trump Suit':<12} {'Win %':<8} {'Wins':<6} {'Avg Pts':<8} {'Time (s)':<8}")
    print("-"*60)
    
    for trump_suit in ['C', 'S', 'H', 'D']:
        if trump_suit in results:
            data = results[trump_suit]
            print(f"{trump_suit:<12} {data['win_percentage']:<8.2f} "
                  f"{data['wins']:<6} {data['avg_points']:<8.2f} {data['elapsed_time']:<8.2f}")
    
    print("-"*60)
    
    # Find best trump suit
    best_trump = max(results.keys(), key=lambda x: results[x]['win_percentage'])
    best_percentage = results[best_trump]['win_percentage']
    
    print(f"\nBest trump suit: {best_trump} ({best_percentage:.2f}% win rate)")
    
    # Overall statistics
    total_wins = sum(data['wins'] for data in results.values())
    total_hands = sum(data['total_hands'] for data in results.values())
    overall_percentage = (total_wins / total_hands) * 100 if total_hands > 0 else 0
    
    print(f"Overall win rate: {overall_percentage:.2f}% ({total_wins}/{total_hands})")

if __name__ == "__main__":
    print("Fast Skat Double Dummy Solver")
    print("=" * 40)
    
    # Run simulation
    print(f"Running simulation with 1000 hands per trump suit...")
    results = run_fast_simulation(1000)
    
    # Print summary
    print_summary(results)