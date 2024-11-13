import random

class Card:
    def __init__(self, value):
        self.value = value
        # Bullheads based on the card number:
        if value % 10 == 0:         # Multiples of 10 (e.g., 10, 20) have 3 bullheads
            self.bullheads = 3
        elif value % 11 == 0:       # Multiples of 11 (e.g., 11, 22) have 5 bullheads
            self.bullheads = 5
        elif value % 5 == 0:        # Multiples of 5 (but not 10) have 2 bullheads
            self.bullheads = 2
        else:
            self.bullheads = 1      # All other cards have 1 bullhead

    def __repr__(self):
        return f"Card({self.value}, bullheads={self.bullheads})"


class SixNimmtGame:
    def __init__(self, num_players=4):
        self.num_players = num_players
        self.deck = [Card(value) for value in range(1, 105)]
        self.players = [[] for _ in range(num_players)]
        self.scores = [0] * num_players
        self.rows = [[] for _ in range(4)]

    def deal_cards(self):
        random.shuffle(self.deck)
        for player in range(self.num_players):
            self.players[player] = [self.deck.pop() for _ in range(10)]
        for row in range(4):
            self.rows[row] = [self.deck.pop()]

    def display_game_state(self):
        print("\nCurrent rows:")
        for idx, row in enumerate(self.rows):
            print(f"Row {idx + 1}: {[card.value for card in row]}")

        for player, hand in enumerate(self.players, start=1):
            print(f"Player {player}'s hand: {[card.value for card in hand]}")
        print(f"Scores: {self.scores}")

    def play_round(self):
        # Each player selects a card
        chosen_cards = []
        for player in range(self.num_players):
            hand = self.players[player]
            chosen_card = hand.pop(random.randint(0, len(hand) - 1))  # Random choice for simplicity
            chosen_cards.append((chosen_card, player))

        # Sort chosen cards by value to place them in ascending order
        chosen_cards.sort(key=lambda x: x[0].value)

        # Place each card in the appropriate row
        for chosen_card, player in chosen_cards:
            placed = False
            print(f"\nPlayer {player + 1} plays {chosen_card.value}:")

            # Find the row where this card fits (highest card less than chosen card)
            best_row = -1
            best_value = -1
            for i, row in enumerate(self.rows):
                if row[-1].value < chosen_card.value and row[-1].value > best_value:
                    best_value = row[-1].value
                    best_row = i

            if best_row == -1:
                # No row has a lower last card, so player must take a row
                self.choose_and_take_row(player, chosen_card)
            else:
                # Place the card in the row
                if len(self.rows[best_row]) == 5:
                    # Row is full, player must take it
                    print(f"Row {best_row + 1} is full. Player {player + 1} takes it.")
                    self.scores[player] += sum(card.bullheads for card in self.rows[best_row])
                    self.rows[best_row] = [chosen_card]
                else:
                    # Add the card to the chosen row
                    self.rows[best_row].append(chosen_card)
                    print(f"Placed in row {best_row + 1}.")

    def choose_and_take_row(self, player, chosen_card):
        # For simplicity, the player takes the row with the fewest bullheads
        min_bullheads = min(sum(card.bullheads for card in row) for row in self.rows)
        chosen_row = min((i for i, row in enumerate(self.rows) if sum(card.bullheads for card in row) == min_bullheads), key=lambda x: sum(card.bullheads for card in self.rows[x]))
        print(f"Player {player + 1} must take a row and chooses row {chosen_row + 1}.")
        self.scores[player] += sum(card.bullheads for card in self.rows[chosen_row])
        self.rows[chosen_row] = [chosen_card]

    def play_game(self):
        self.deal_cards()
        for round_num in range(10):
            print(f"\n--- Round {round_num + 1} ---")
            self.display_game_state()
            self.play_round()
        self.display_final_scores()

    def display_final_scores(self):
        print("\nFinal Scores:")
        for player, score in enumerate(self.scores, start=1):
            print(f"Player {player}: {score} bullheads")
        winner = self.scores.index(min(self.scores)) + 1
        print(f"\nPlayer {winner} wins!")

# Run the game with 4 players
game = SixNimmtGame(num_players=4)
game.play_game()
