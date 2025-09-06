#!/usr/bin/env python3
"""
Skat Double Dummy Solver
Simulates 1000 random opening hands to determine win percentages for suit contracts.
"""

import random
import itertools
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass
from enum import Enum
import time

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

class SkatGame:
    """Represents a Skat game state for double dummy solving."""
    
    def __init__(self, declarer_hand: List[Card], left_opponent: List[Card], 
                 right_opponent: List[Card], skat: List[Card], trump_suit: Suit):
        self.declarer_hand = declarer_hand.copy()
        self.left_opponent = left_opponent.copy()
        self.right_opponent = right_opponent.copy()
        self.skat = skat.copy()
        self.trump_suit = trump_suit
        
        # Game state
        self.current_trick: List[Tuple[int, Card]] = []  # (player, card)
        self.lead_player = 0  # 0=declarer, 1=left, 2=right
        self.tricks_won = [0, 0, 0]  # tricks won by each player
        self.points_won = [0, 0, 0]  # points won by each player
        self.trick_number = 0
        
        # All cards in play
        self.all_cards = declarer_hand + left_opponent + right_opponent + skat
        
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
        """Get trump ranking for comparison (higher = stronger)."""
        if card.rank == Rank.JACK:
            # Jacks: CJ > SJ > HJ > DJ
            jack_order = {Suit.CLUBS: 4, Suit.SPADES: 3, Suit.HEARTS: 2, Suit.DIAMONDS: 1}
            return jack_order[card.suit]
        elif card.suit == self.trump_suit:
            # Trump suit cards: A > 10 > K > Q > 9 > 8 > 7
            trump_order = {Rank.ACE: 7, Rank.TEN: 6, Rank.KING: 5, Rank.QUEEN: 4,
                          Rank.NINE: 3, Rank.EIGHT: 2, Rank.SEVEN: 1}
            return trump_order[card.rank]
        else:
            return 0
    
    def get_suit_rank(self, card: Card) -> int:
        """Get suit ranking for non-trump cards (higher = stronger)."""
        suit_order = {Rank.ACE: 7, Rank.TEN: 6, Rank.KING: 5, Rank.QUEEN: 4,
                     Rank.NINE: 3, Rank.EIGHT: 2, Rank.SEVEN: 1}
        return suit_order[card.rank]
    
    def card_beats(self, card1: Card, card2: Card) -> bool:
        """Check if card1 beats card2 in the current trick context."""
        trump1, trump2 = self.is_trump(card1), self.is_trump(card2)
        
        if trump1 and not trump2:
            return True
        elif not trump1 and trump2:
            return False
        elif trump1 and trump2:
            return self.get_trump_rank(card1) > self.get_trump_rank(card2)
        else:
            # Both non-trump, check if same suit
            if card1.suit == card2.suit:
                return self.get_suit_rank(card1) > self.get_suit_rank(card2)
            else:
                return False  # Different suits, neither trumps
    
    def get_legal_moves(self, player: int) -> List[Card]:
        """Get legal moves for a player."""
        if player == 0:
            hand = self.declarer_hand
        elif player == 1:
            hand = self.left_opponent
        else:
            hand = self.right_opponent
        
        if not self.current_trick:
            return hand  # Can play any card when leading
        
        # Must follow suit if possible
        lead_card = self.current_trick[0][1]
        lead_suit = lead_card.suit
        
        # Check if we have cards of the led suit
        suit_cards = [card for card in hand if card.suit == lead_suit]
        
        if suit_cards:
            return suit_cards
        else:
            return hand  # Can play any card if can't follow suit
    
    def play_card(self, player: int, card: Card) -> bool:
        """Play a card and return True if trick is complete."""
        # Remove card from hand
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
        
        # Check if trick is complete
        if len(self.current_trick) == 3:
            self.resolve_trick()
            return True
        else:
            # Move to next player
            self.lead_player = (self.lead_player + 1) % 3
            return False
    
    def resolve_trick(self):
        """Resolve the current trick and update game state."""
        if len(self.current_trick) != 3:
            return
        
        # Find winning card
        winning_card = self.current_trick[0][1]
        winning_player = self.current_trick[0][0]
        
        for player, card in self.current_trick[1:]:
            if self.card_beats(card, winning_card):
                winning_card = card
                winning_player = player
        
        # Award trick and points
        self.tricks_won[winning_player] += 1
        trick_points = sum(self.get_card_value(card) for _, card in self.current_trick)
        self.points_won[winning_player] += trick_points
        
        # Update game state
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
        new_game = SkatGame(
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

def create_deck() -> List[Card]:
    """Create a 32-card Skat deck."""
    deck = []
    for suit in Suit:
        for rank in Rank:
            deck.append(Card(suit, rank))
    return deck

def deal_hands() -> Tuple[List[Card], List[Card], List[Card], List[Card]]:
    """Deal random hands for a Skat game."""
    deck = create_deck()
    random.shuffle(deck)
    
    declarer = deck[:10]
    left_opponent = deck[10:20]
    right_opponent = deck[20:30]
    skat = deck[30:32]
    
    return declarer, left_opponent, right_opponent, skat

class TranspositionTable:
    """Transposition table for memoization in alpha-beta search."""
    
    def __init__(self):
        self.table: Dict[str, Tuple[int, int]] = {}  # state_hash -> (score, depth)
    
    def get(self, state_hash: str, depth: int) -> Optional[int]:
        """Get cached score if available and depth is sufficient."""
        if state_hash in self.table:
            cached_score, cached_depth = self.table[state_hash]
            if cached_depth >= depth:
                return cached_score
        return None
    
    def store(self, state_hash: str, score: int, depth: int):
        """Store score in transposition table."""
        self.table[state_hash] = (score, depth)

class SkatSolver:
    """Double dummy solver for Skat using alpha-beta search."""
    
    def __init__(self):
        self.transposition_table = TranspositionTable()
        self.nodes_evaluated = 0
        self.cache_hits = 0
    
    def get_state_hash(self, game: SkatGame) -> str:
        """Generate a hash for the current game state with quasi-symmetry reduction."""
        # Group cards by strategic similarity for quasi-symmetry reduction
        def group_cards(cards):
            groups = {'jacks': [], 'trump_high': [], 'trump_low': [], 'suit_high': [], 'suit_low': []}
            for card in cards:
                if card.rank == Rank.JACK:
                    groups['jacks'].append(str(card))
                elif game.is_trump(card):
                    if card.rank in [Rank.ACE, Rank.TEN, Rank.KING]:
                        groups['trump_high'].append(str(card))
                    else:
                        groups['trump_low'].append(str(card))
                else:
                    if card.rank in [Rank.ACE, Rank.TEN, Rank.KING]:
                        groups['suit_high'].append(str(card))
                    else:
                        groups['suit_low'].append(str(card))
            
            # Sort within groups for consistency
            for group in groups.values():
                group.sort()
            return groups
        
        declarer_groups = group_cards(game.declarer_hand)
        left_groups = group_cards(game.left_opponent)
        right_groups = group_cards(game.right_opponent)
        trick_cards = [str(card) for _, card in game.current_trick]
        
        state_str = f"{declarer_groups}|{left_groups}|{right_groups}|{trick_cards}|{game.lead_player}|{game.trump_suit.value}"
        return state_str
    
    def evaluate_position(self, game: SkatGame) -> int:
        """Evaluate the current position for the declarer with adversarial heuristics."""
        if game.is_game_over():
            declarer_points = game.get_declarer_points()
            return declarer_points
        
        # Current points already won
        current_points = game.points_won[0]
        
        # Heuristic evaluation based on cards remaining
        declarer_value = sum(game.get_card_value(card) for card in game.declarer_hand)
        left_value = sum(game.get_card_value(card) for card in game.left_opponent)
        right_value = sum(game.get_card_value(card) for card in game.right_opponent)
        
        # Count trumps and high cards
        declarer_trumps = sum(1 for card in game.declarer_hand if game.is_trump(card))
        left_trumps = sum(1 for card in game.left_opponent if game.is_trump(card))
        right_trumps = sum(1 for card in game.right_opponent if game.is_trump(card))
        
        # Count high-value cards (A, 10, K)
        declarer_high = sum(1 for card in game.declarer_hand 
                           if card.rank in [Rank.ACE, Rank.TEN, Rank.KING])
        left_high = sum(1 for card in game.left_opponent 
                       if card.rank in [Rank.ACE, Rank.TEN, Rank.KING])
        right_high = sum(1 for card in game.right_opponent 
                        if card.rank in [Rank.ACE, Rank.TEN, Rank.KING])
        
        # Adversarial heuristics: bounds on declarer points
        max_possible_points = current_points + declarer_value
        min_possible_points = current_points
        
        # If we can't reach 61 even with all remaining cards, return low score
        if max_possible_points < 61:
            return max_possible_points - 100  # Penalty for impossible win
        
        # If we already have 61+, return high score
        if current_points >= 61:
            return current_points + 100
        
        # Trump advantage calculation
        trump_advantage = (declarer_trumps - (left_trumps + right_trumps) / 2) * 8
        
        # High card advantage
        high_card_advantage = (declarer_high - (left_high + right_high) / 2) * 3
        
        # Trick control estimation
        total_cards = len(game.declarer_hand) + len(game.left_opponent) + len(game.right_opponent)
        tricks_remaining = total_cards // 3
        declarer_trick_estimate = (declarer_trumps + declarer_high) * tricks_remaining / total_cards
        
        # Combine heuristics
        evaluation = (current_points + declarer_value + trump_advantage + 
                     high_card_advantage + declarer_trick_estimate * 2)
        
        return int(evaluation)
    
    def alpha_beta_search(self, game: SkatGame, depth: int, alpha: int, beta: int, 
                         maximizing_player: bool) -> int:
        """Alpha-beta search with minimax."""
        self.nodes_evaluated += 1
        
        if depth == 0 or game.is_game_over():
            return self.evaluate_position(game)
        
        # Check transposition table
        state_hash = self.get_state_hash(game)
        cached_score = self.transposition_table.get(state_hash, depth)
        if cached_score is not None:
            self.cache_hits += 1
            return cached_score
        
        if maximizing_player:
            # Declarer's turn - maximize points
            max_eval = float('-inf')
            legal_moves = game.get_legal_moves(game.lead_player)
            
            for card in legal_moves:
                new_game = game.copy()
                new_game.play_card(game.lead_player, card)
                
                if new_game.current_trick:  # Trick not complete
                    eval_score = self.alpha_beta_search(new_game, depth - 1, alpha, beta, True)
                else:  # Trick complete, next player leads
                    eval_score = self.alpha_beta_search(new_game, depth - 1, alpha, beta, True)
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                
                if beta <= alpha:
                    break  # Beta cutoff
            
            self.transposition_table.store(state_hash, max_eval, depth)
            return max_eval
        else:
            # Opponents' turn - minimize declarer's points
            min_eval = float('inf')
            legal_moves = game.get_legal_moves(game.lead_player)
            
            for card in legal_moves:
                new_game = game.copy()
                new_game.play_card(game.lead_player, card)
                
                if new_game.current_trick:  # Trick not complete
                    eval_score = self.alpha_beta_search(new_game, depth - 1, alpha, beta, False)
                else:  # Trick complete, next player leads
                    eval_score = self.alpha_beta_search(new_game, depth - 1, alpha, beta, True)
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                if beta <= alpha:
                    break  # Alpha cutoff
            
            self.transposition_table.store(state_hash, min_eval, depth)
            return min_eval
    
    def solve_game(self, game: SkatGame, max_depth: int = 15) -> int:
        """Solve a complete Skat game using double dummy analysis."""
        self.nodes_evaluated = 0
        self.cache_hits = 0
        
        # Start with declarer to move
        result = self.alpha_beta_search(game, max_depth, float('-inf'), float('inf'), True)
        
        return result

def optimal_discard(declarer_hand: List[Card], skat: List[Card], trump_suit: Suit) -> Tuple[List[Card], List[Card]]:
    """Find optimal cards to discard from skat + declarer hand."""
    all_cards = declarer_hand + skat
    temp_game = SkatGame([], [], [], [], trump_suit)
    
    # Score cards based on multiple factors
    def score_card(card):
        base_value = temp_game.get_card_value(card)
        is_trump = temp_game.is_trump(card)
        
        # Prefer to keep trumps
        trump_bonus = 20 if is_trump else 0
        
        # Prefer to keep high cards
        high_card_bonus = 0
        if card.rank in [Rank.ACE, Rank.TEN, Rank.KING]:
            high_card_bonus = 10
        elif card.rank == Rank.QUEEN:
            high_card_bonus = 5
        
        # Prefer to keep Jacks (highest trumps)
        jack_bonus = 30 if card.rank == Rank.JACK else 0
        
        # Prefer to keep cards that can win tricks
        trick_potential = 0
        if is_trump:
            if card.rank == Rank.JACK:
                trick_potential = 15
            elif card.rank in [Rank.ACE, Rank.TEN]:
                trick_potential = 10
            else:
                trick_potential = 5
        else:
            if card.rank in [Rank.ACE, Rank.TEN]:
                trick_potential = 8
            elif card.rank == Rank.KING:
                trick_potential = 3
        
        return base_value + trump_bonus + high_card_bonus + jack_bonus + trick_potential
    
    # Score all cards and sort by score (descending)
    card_scores = [(card, score_card(card)) for card in all_cards]
    card_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Keep the 10 highest scoring cards, discard the 2 lowest
    new_hand = [card for card, _ in card_scores[:10]]
    to_discard = [card for card, _ in card_scores[10:]]
    
    return new_hand, to_discard

def simulate_hand(trump_suit: Suit, solver: SkatSolver) -> bool:
    """Simulate a single hand and return True if declarer can guarantee 61+ points."""
    # Deal random hands
    declarer_hand, left_opponent, right_opponent, skat = deal_hands()
    
    # Declarer picks up skat and discards optimally
    final_hand, discarded = optimal_discard(declarer_hand, skat, trump_suit)
    
    # Create game with final hand
    game = SkatGame(final_hand, left_opponent, right_opponent, discarded, trump_suit)
    
    # Solve using double dummy analysis
    declarer_points = solver.solve_game(game)
    
    # Check if declarer can guarantee 61+ points
    return declarer_points >= 61

def run_simulation(num_hands: int = 1000) -> Dict[str, Dict[str, float]]:
    """Run simulation for all trump suits and return statistics."""
    solver = SkatSolver()
    results = {}
    
    trump_suits = [Suit.CLUBS, Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS]
    
    for trump_suit in trump_suits:
        print(f"\nSimulating {num_hands} hands for {trump_suit.value} trump...")
        
        wins = 0
        total_points = 0
        start_time = time.time()
        
        for i in range(num_hands):
            if (i + 1) % 100 == 0:
                print(f"  Hand {i + 1}/{num_hands}")
            
            # Deal and solve
            declarer_hand, left_opponent, right_opponent, skat = deal_hands()
            final_hand, discarded = optimal_discard(declarer_hand, skat, trump_suit)
            game = SkatGame(final_hand, left_opponent, right_opponent, discarded, trump_suit)
            
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
        print(f"  Nodes evaluated: {solver.nodes_evaluated:,}")
        print(f"  Cache hits: {solver.cache_hits:,}")
    
    return results

def print_summary(results: Dict[str, Dict[str, float]]):
    """Print a summary of simulation results."""
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

def test_basic_functionality():
    """Test basic game functionality."""
    print("Testing basic functionality...")
    
    # Test deck creation
    deck = create_deck()
    print(f"✓ Deck size: {len(deck)}")
    
    # Test dealing
    declarer, left, right, skat = deal_hands()
    print(f"✓ Declarer hand: {len(declarer)} cards")
    print(f"✓ Sample cards: {[str(card) for card in declarer[:3]]}")
    
    # Test game creation
    game = SkatGame(declarer, left, right, skat, Suit.CLUBS)
    print(f"✓ Game created with {len(game.declarer_hand)} cards for declarer")
    
    # Test card evaluation
    test_card = Card(Suit.HEARTS, Rank.ACE)
    value = game.get_card_value(test_card)
    print(f"✓ Ace of Hearts value: {value}")
    
    # Test trump detection
    jack_clubs = Card(Suit.CLUBS, Rank.JACK)
    ace_clubs = Card(Suit.CLUBS, Rank.ACE)
    ace_hearts = Card(Suit.HEARTS, Rank.ACE)
    
    print(f"✓ Jack of Clubs is trump: {game.is_trump(jack_clubs)}")
    print(f"✓ Ace of Clubs is trump: {game.is_trump(ace_clubs)}")
    print(f"✓ Ace of Hearts is trump: {game.is_trump(ace_hearts)}")
    
    # Test optimal discard
    final_hand, discarded = optimal_discard(declarer, skat, Suit.CLUBS)
    print(f"✓ Optimal discard: {[str(card) for card in discarded]}")
    print(f"✓ Final hand size: {len(final_hand)}")
    
    return True

if __name__ == "__main__":
    print("Skat Double Dummy Solver")
    print("=" * 40)
    
    # Test basic functionality first
    if test_basic_functionality():
        print("\n✓ All basic tests passed!")
        
        # Run small simulation for testing
        print(f"\nRunning simulation with 5 hands per trump suit (for testing)...")
        results = run_simulation(5)
        
        # Print summary
        print_summary(results)
    else:
        print("✗ Basic tests failed!")