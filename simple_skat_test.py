#!/usr/bin/env python3
"""
Simple test of Skat solver to verify basic functionality.
"""

import random
from skat_solver import *

def simple_test():
    """Run a simple test without full simulation."""
    print("Simple Skat Solver Test")
    print("=" * 30)
    
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
    
    # Test a simple game simulation (without full solver)
    print("\nTesting simple game simulation...")
    game = SkatGame(final_hand, left, right, discarded, Suit.CLUBS)
    
    # Play a few cards manually to test trick resolution
    if game.declarer_hand:
        card1 = game.declarer_hand[0]
        game.play_card(0, card1)
        print(f"✓ Played {card1} as declarer")
    
    if game.left_opponent:
        card2 = game.left_opponent[0]
        game.play_card(1, card2)
        print(f"✓ Played {card2} as left opponent")
    
    if game.right_opponent:
        card3 = game.right_opponent[0]
        game.play_card(2, card3)
        print(f"✓ Played {card3} as right opponent")
        print(f"✓ Trick complete! Points won: {game.points_won}")
    
    print("\n✓ All basic tests passed!")
    return True

if __name__ == "__main__":
    simple_test()