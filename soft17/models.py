
#################################################################################################################################
#     @file     :    views.py   
#
#     @brief    :    Set of python functions to receive web requests /  return web responses for Soft17 site
#
#     @authors  :    Madi Davis (madelind@andrew.cmu.edu) & Aishwarya Yadav (ayadav2@andrew.cmu.edu)
#################################################################################################################################

# ------------------------------------------------------------------------------------------------------------------------------#
# --- INCLUDES --- #
# ------------------------------------------------------------------------------------------------------------------------------#
### Django Modules ####
import random
from django.db import models
from django.contrib.auth.models import User

from django.utils.translation import gettext_lazy as _

### Local Libraries ###from django.db import models

# ------------------------------------------------------------------------------------------------------------------------------#
# --- GAME MODELS --- #
# ------------------------------------------------------------------------------------------------------------------------------#
class GameRoom(models.Model):
    #############################################################################################################################
    # @brief      :       Creates django model class for a game
    #############################################################################################################################
    # Common / Core Attributes
    name = models.CharField(max_length=200, default="None")
    balance = models.IntegerField(default=1000)
    is_multiplayer = models.BooleanField(default=False)

    
    # -- STATIC METHODS --- #
    """
    @brief      :    Create a new single PLayer Game Room
    @param[in]  :    player 
    @retval     :    
    """
    @staticmethod
    def create_new_single_player_room():
        # Create New Instance of a Game Room
        new_room = GameRoom()
        # new_room.balance = 1000
        new_room.save()
        
        # Creater Dealer for Room
        Dealer.create_new_dealer(new_room)
        return new_room
    
    # -- GAME METHODS --- #
    """
    @brief      :    Return instance of Game in play
    @param[in]  :    
    @retval     :    Game 
    """
    def get_current_game(self):
        curr_game =  Game.objects.filter(game_room=self, is_completed=False)
        # If no current Game start new Game
        if curr_game.count() == 0:
            new_game = Game.create_new_game(self)
            deck = new_game.get_deck()
            deck.reset_deck()
            return new_game
        
        return curr_game[0]

    """
    @brief      :    Get Dealer
    @param[in]  :    
    @retval     :    
    """ 
    def get_dealer(self):
        dealer_set = Dealer.objects.filter(game_room=self)
        if len(dealer_set) != 1: return None
        else: return dealer_set[0]


class Dealer(models.Model):
    #############################################################################################################################
    # @brief      :       Creates django model class for dealer
    #############################################################################################################################
    game_room = models.ForeignKey(GameRoom, default=None, null=True, on_delete=models.PROTECT, related_name='game_room')

    # -- STATIC METHODS --- #
    """
    @brief      :    Create a new instance of a Dealer
    @param[in]  :    game_room - game room to assign a dealer to 
    @retval     :    
    """
    @staticmethod
    def create_new_dealer(game_room):
        # Create a new instance of a Dealer Object 
        new_dealer = Dealer()
        new_dealer.game_room = game_room
        new_dealer.save()

        # Create a New Deck of Cards and Assign to the Dealer
        Deck.create_new_deck(new_dealer)




class Game(models.Model):
    #############################################################################################################################
    # @brief      :       Creates django model class for a game
    #############################################################################################################################
    class Game_State(models.IntegerChoices):
        RESET_GAME = 0
        START_GAME = 1
        PLACE_BET = 2
        DEAL_PLAYERS = 3
        DEAL_DEALER = 4
        PLAYER_TURN = 5
        PLAYER_SCORE = 6
        DEALER_TURN = 7
        DEALER_SCORE = 8
        COMPUTE_SCORES = 9

    # Game State Variables
    is_completed = models.BooleanField(default=False)
    curr_state = models.IntegerField(choices=Game_State.choices, default=1)
    
    # Model Relationships
    num_players = models.IntegerField(default=1)
    game_room = models.ForeignKey(GameRoom, default=None, null=True, on_delete=models.PROTECT, related_name='room')
  
    # Game Data Variables
    created = models.DateTimeField(default=None, null=True, blank=True)
    completed = models.DateTimeField(default=None, null=True, blank=True)


   # -- STATIC METHODS --- #
    """
    @brief      :    Create a new game
    @param[in]  :    game_room - game room that game is hosted in
    @retval     :    
    """
    @staticmethod
    def create_new_game(game_room):
        # Initialise Game State and State Variables
        new_game = Game()
        new_game.curr_state = 1

        # Get Game Data
        new_game.game_room = game_room
        player_list = Profile.objects.filter(single_player_room=game_room).order_by('id')
        new_game.num_players = player_list.count()

        new_game.save()

        # Create Hands for player & dealer
        dealer = new_game.get_dealer()
        Hand.create_new_dealer_hand(dealer, new_game)
        for player in player_list:
            Hand.create_new_player_hand(player, new_game)

        # Create Bets for all players
        for player in player_list:
            Bet.create_new_bet(player, new_game)
        return new_game
            

    """
    @brief      :    Get a sorted list of players
    @param[in]  :    
    @retval     :    List of Players in ascending order of id
    """
    def get_game_players(self):
        return Profile.objects.get(single_player_room=self.game_room)

    """
    @brief      :    Get Number of Players
    @param[in]  :    
    @retval     :    
    """
    def get_num_players(self):
        return Profile.objects.get(single_player_room=self.game_room).count()


    """
    @brief      :    Get Dealer
    @param[in]  :    
    @retval     :    
    """ 
    def get_dealer(self):
        dealer_set = Dealer.objects.filter(game_room = self.game_room)
        if len(dealer_set) != 1: return None
        else: return dealer_set[0]


    """
    @brief      :    Get Deck
    @param[in]  :    
    @retval     :    
    """
    def get_deck(self):
        dealer = self.get_dealer()
        return Deck.objects.get(dealer = dealer)


    """
    @brief      :    Get Player Hand
    @param[in]  :    
    @retval     :    
    """
    def get_player_hand(self, player):
        return Hand.objects.filter(game=self, player=player)[0]
    
    """
    @brief      :    Get Player Hand
    @param[in]  :   dealer - dealer for current game 
    @retval     :    
    """
    def get_dealer_hand(self, dealer):
        return Hand.objects.filter(game=self, dealer=dealer)[0]


    """
    @brief      :    Get Player Bet
    @param[in]  :    
    @retval     :    
    """
    def get_player_bet(self, player):
        return Bet.objects.filter(game=self, player=player)[0]




    # --- GAME ACTIONS & LOGIC --- #
    """
    @brief      :    Deal a new card to the player
    @param[in]  :    
    @retval     :    
    """
    def deal_card_to_player(self, player):
        card = self.get_deck().deal_card()
        if(card is not None):
            self.get_player_hand(player).add_card(card)
        self.save()

    """
    @brief      :    Deal a new card to the dealer
    @param[in]  :    
    @retval     :    
    """
    def deal_card_to_dealer(self, dealer):
        card = self.get_deck().deal_card()
        if(card is not None):
            self.get_dealer_hand(dealer).add_card(card)
        self.save()
    
    # PLAYER METHODS
    """
    @brief      :    Player Hits
    @param[in]  :    
    @retval     :    true if successful (under 21), false if bust or equal to 21
    """
    def player_hit(self, player):
        # Deal Player New Card
        self.deal_card_to_player(player)
        # Check Bust
        hand = self.get_player_hand(player)
        if(hand.hand_value == 21 or hand.check_hand_bust()):
            #self.curr_state = Game.Game_State.DEALER_TURN
            return False
        return True

    """
    @brief      :    Player Doubles
    @param[in]  :    
    @retval     :    true if successful (under 21), false if bust or equal to 21
    """
    def player_double(self, player, bet_data, bet_order):
        # Update Bet
        player_bet = self.get_player_bet(player)
        player_bet.update_bet(bet_data, bet_order)
        # Deal Player New Card
        self.deal_card_to_player(player)
        #hand = self.get_player_hand(player)
        # have to stand after double
        #if(hand.hand_value == 21 or hand.check_hand_bust()):
            #self.curr_state = Game.Game_State.DEALER_TURN

        
    """
    @brief      :    Player Stands
    @param[in]  :    
    @retval     :     
    """
    def player_stand(self):
        self.curr_state = Game.Game_State.DEALER_TURN

    # DEALER METHODS
    def dealer_move(self, dealer):
        hand = self.get_dealer_hand(dealer)
        if hand.check_under_17() or hand.check_soft17():
            self.dealer_hit(dealer)
            #return True
        #else:
            #return False
    

    def dealer_hit(self, dealer):
        self.deal_card_to_dealer(dealer)
    
    def dealer_stand(self):
        pass
    
    def get_game_result(self, player, dealer):
        player_hand = self.get_player_hand(player)
        dealer_hand = self.get_dealer_hand(dealer)
        
        # get player's hand value
        player_hand_value = player_hand.hand_value
        player_hand_max_value = player_hand.get_max_hand_value()
        if(player_hand_max_value < 21):
            player_hand_value = player_hand_max_value

        # get dealer's hand value
        dealer_hand_value = dealer_hand.hand_value
        dealer_hand_max_value = dealer_hand.get_max_hand_value()
        if(dealer_hand_max_value < 21):
            dealer_hand_value = dealer_hand_max_value

        # set default winner as dealer
        result = "Dealer wins!"
        if player_hand_value > 21: # player busted
            result = "Dealer wins!"
        elif dealer_hand_value > 21: # dealer busted
            result = "You win!"
        elif player_hand_value == dealer_hand_value: # player and dealer have same hand value
            result = "It's a tie!"
        elif player_hand.is_natural_blackjack():
            result = "You win!"
        elif dealer_hand.is_natural_blackjack():
            result = "Dealer wins!"
        elif player_hand_value > dealer_hand_value: # player has a hand value higher than dealer's
            result = "You win!"
        elif dealer_hand_value > player_hand_value: # dealer has a hand value higher than player's
            result = "Dealer wins!"
        
        return result
        
    def settle_bets(self, player, dealer):
        result = self.get_game_result(player, dealer)
        bet_value = self.get_player_bet(player).get_total_bet_value()
        if("Dealer" in result):
            player.update_wallet_balance('-', bet_value)
            self.game_room.balance = self.game_room.balance + bet_value
            self.game_room.save()
        elif("You" in result):
            player.update_wallet_balance('+', bet_value)
            self.game_room.balance = self.game_room.balance - bet_value
            self.game_room.save()




# ------------------------------------------------------------------------------------------------------------------------------#
# --- USER MODELS --- #
# ------------------------------------------------------------------------------------------------------------------------------#


class Profile(models.Model):
    #############################################################################################################################
    # @brief      :       Creates django form class for user profile
    #############################################################################################################################
    profile_user = models.ForeignKey(User, default=None, null=True, on_delete=models.PROTECT)
    user_picture = models.FileField(blank=True)
    content_type = models.CharField(max_length=50, default="None")

    # Game Attributes
    wallet_balance = models.IntegerField(default=1)
    # Player can only be in one multiplayer game at a time, single player is ongoing
    single_player_room = models.ForeignKey(GameRoom, default=None, null=True, on_delete=models.PROTECT, related_name="single_player_room")
    multiplayer_room = models.ForeignKey(GameRoom, default=None, on_delete=models.SET_NULL, blank=True, null=True, related_name="multiplayer_room")
    
    def update_wallet_balance(self, operator, value):
        if(operator == '-'):
            self.wallet_balance = self.wallet_balance - value
        elif(operator == '+'):
            self.wallet_balance = self.wallet_balance + value
        self.save()





# ------------------------------------------------------------------------------------------------------------------------------#
# --- DECK MODELS --- #
# ------------------------------------------------------------------------------------------------------------------------------#
class Card(models.Model):
    #############################################################################################################################
    # @brief      :       Creates django model for individual playing cards
    #############################################################################################################################
    SUIT_CHOICES = (("SPADE", "Spade"),
                    ("CLUB", "Club"),
                    ("DIAMOND", "Diamond"),
                    ("HEART", "Heart"),
    )

    RANK_CHOICES = (("A", "Ace"),
                    ("2", "Two"),
                    ("3", "Three"),
                    ("4", "Four"),
                    ("5", "Five"),
                    ("6", "Six"),
                    ("7", "Seven"),
                    ("8", "Eight"),
                    ("9", "Nine"),
                    ("10", "Ten"),
                    ("J", "Jack"),
                    ("Q", "Queen"),
                    ("K", "King"),
    )

    suit = models.CharField(max_length=10, choices=SUIT_CHOICES, default="SPADE")
    rank = models.CharField(max_length=10, choices=RANK_CHOICES, default="A")
    value = models.IntegerField(default=1)
    url = models.CharField(max_length=200, default="none")
    
    # Order by Hand Order
    class Meta:
        ordering = ('hand_order__hand_position',)

    # --- STATIC METHODS --- #
    """
    @brief      :    Create a new card
    @param[in]  :    suit - suit of new card
    @param[in]  :    rank - rank of new card
    @param[in]  :    value - value of card
    @param[in]  :    url - link to static file for img
    @param[in]  :    deck - deck to assign card
    @retval     :    Card Instance
    """
    @staticmethod
    def create_new_card(suit, rank, value, url):
        new_card = Card()
        new_card.rank = rank
        new_card.suit = suit
        new_card.value = value
        new_card.url = url
        new_card.save()



class Deck(models.Model):
    #############################################################################################################################
    # @brief      :       Creates django model class for a deck of Cards
    #############################################################################################################################
    remaining_cards = models.ManyToManyField(Card, related_name='remaining_cards_in_deck', blank=True, null=True)
    assigned_cards = models.ManyToManyField(Card, related_name='assigned_cards_to_deck', blank = True, null=True)
    dealer = models.ForeignKey(Dealer, default=None, null=True, on_delete=models.PROTECT) #<** A Deck of Cards is Assigned to a Dealer

    # -- STATIC METHODS --- #
    """
    @brief      :    Create a new instance of a deck populate with card instances
    @param[in]  :    dealer - dealer instance that deck is assigned to 
    @retval     :    new deck 
    """
    @staticmethod
    def create_new_deck(dealer):
        # Create new Deck Object
        new_deck = Deck()
        new_deck.dealer = dealer
        new_deck.save()

        new_deck.reset_deck()
        return new_deck
    
    # --- METHODS --- #
    """
    @brief      :    return all cards to deck
    @param[in]  :    
    @retval     :    
    """
    def reset_deck(self):
        self.remaining_cards.set(list(Card.objects.all()))
        self.assigned_cards.clear()
        self.save()


    """
    @brief      :    shuffle all remaining cards in deck
    @param[in]  :    
    @retval     :    
    """
    def shuffle_deck(self):
        remaining_cards_list = list(self.remaining_cards.all())
        random.shuffle(remaining_cards_list)

        # Reassign the shuffled cards to the remaining_cards attribute
        self.remaining_cards.set(remaining_cards_list)


    """
    @brief      :    get number of cards remaining in deck
    @param[in]  :    
    @retval     :    List of card objects
    """
    def get_remaining_num_cards(self):
        return self.remaining_cards.count()


    """
    @brief      :    Return a Card to be dealt
    @param[in]  :    
    @retval     :    Card - instance of Card object, None- if no cards left in deck
    """
    def deal_card(self):
        # Rabndomly Select Card from remaining cards
        remaining_cards = self.remaining_cards.all()
        if remaining_cards.exists():
            card = remaining_cards.order_by('?').first()
            if card:
                # Add the top card to assigned_cards
                self.assigned_cards.add(card)
                # Remove the top card from remaining_cards
                self.remaining_cards.remove(card)

                self.save()
                return card
        return None





class Hand(models.Model):
    #############################################################################################################################
    # @brief      :       Creates django model class for a hand of Cards
    #############################################################################################################################
    # Values of a Hand
    num_cards = models.IntegerField(default=0)
    hand_value = models.IntegerField(default=0) 
    
    # Assigning Hand to Game & Player --> NEED FOR QUERY FILTERING
    game = models.ForeignKey(Game, default=None, null=True, on_delete=models.PROTECT, related_name='game')   #<** Hands are assigned to specific games
    # @note : A Hand is assigned to either a player or a dealer
    #         -> if assigned a player, dealer = None
    #         -> if assigned to a dealer, player = None

    player = models.ForeignKey(Profile, default=None, on_delete=models.PROTECT, related_name='player_hand', null=True, blank=True) 
    dealer = models.ForeignKey(Dealer, default=None, on_delete=models.PROTECT, related_name='dealer_hand', null=True, blank=True) 
    is_dealer_hand = models.BooleanField(default=False)
    cards = models.ManyToManyField(Card, through='Hand_Order')

    

    # --- STATIC METHODS --- #
    """
    @brief      :    Create a new instance of a Hand for a player
    @param[in]  :    Player - User Instance, or None if Dealer
    @retval     :    new Hand Instance
    """
    @staticmethod
    def create_new_player_hand(player, game):
        # Have to init to nothing when game starts to account for UI!!
        new_hand = Hand()

        # Assign to a Game and a player 
        new_hand.player = player
        new_hand.game = game

        new_hand.save()
    
    """
    @brief      :    Create a new instance of a Hand for a dealer
    @param[in]  :    Dealer - Dealer instance
    @retval     :    new Hand Instance
    """
    @staticmethod
    def create_new_dealer_hand(dealer, game):
        # Have to init to nothing when game starts to account for UI!!
        new_hand = Hand()

        # Assign to a Game and a player 
        new_hand.dealer = dealer
        new_hand.is_dealer_hand = True
        new_hand.game = game

        new_hand.save()


    # --- METHODS --- #
    """
    @brief      :    Add a new Card to Current hand
    @param[in]  :    deck - instance of Deck object
    @retval     :    None
    """
    def add_card(self, new_card):
        # Deal a card from the deck
        #new_card = deck.deal_card()

        # Add the new card to the hand and card not already in hand
        if (new_card is not None) and (Card.objects.filter(hand=self).count != 0):

            # Add Card to Hand
            self.cards.add(new_card)
            self.num_cards += 1
            self.hand_value += new_card.value
            self.save()

            # Set position in hand via Hand Order Through model
            hand_order = Hand_Order.objects.filter(hand=self, card=new_card)[0]
            hand_order.hand_position = self.num_cards
            hand_order.save()

    """
    @brief      :    Get ordered list of cards in Hand
    @param[in]  :    deck - instance of Deck object
    @retval     :    None
    """    
    def get_hand_cards(self):
        return list(self.cards.all().order_by('hand_order__hand_position'))

    
    """
    @brief      :    Get the max value of the hand by taking value of Ace as 11
    @param[in]  :    
    @retval     :    max value of the hand
    """
    def get_max_hand_value(self):
        max_value = self.hand_value
        num_of_aces = self.cards.filter(rank='A').count()

        while num_of_aces > 0:
            max_value += 10
            num_of_aces -= 1

        return max_value     

    """
    @brief      :    Check if hand is over 21
    @param[in]  :    
    @retval     :    Bool
    """     
    def check_hand_bust(self):
        return self.hand_value > 21
    

    """
    @brief      :    Check if hand is under 17
    @param[in]  :    
    @retval     :    Bool
    """     
    def check_under_17(self):
        return self.hand_value < 17
    
    """
    @brief      :    Check if hand is a soft 17
    @param[in]  :    
    @retval     :    Bool (True if Soft17)
    """   
    def check_soft17(self):
        if self.hand_value != 17: return False
        if (self.cards.filter(rank='A').count() == 1):
            return True
        return False

    def is_natural_blackjack(self):
        if self.num_cards != 2:
            # A natural blackjack can only occur with 2 cards
            return False

        # Get the cards in the hand
        cards = self.cards.all()

        # Check if the hand contains an Ace and a 10, Jack, Queen or King
        has_ace = False
        has_ten_card = False
        for card in cards:
            if card.rank == 'A':
                has_ace = True
            elif card.rank in ('10', 'J', 'Q', 'K'):
                has_ten_card = True

        return has_ace and has_ten_card

#############################################################################################################################
# @brief      :       Through Model for Card and Hand to Get the Order of a Hand for UI
#############################################################################################################################
class Hand_Order(models.Model):
    card = models.ForeignKey(Card, null=True, default=None, related_name="hand_order", on_delete=models.CASCADE)
    hand = models.ForeignKey(Hand, null=True, default=None, related_name="hand_order", on_delete=models.CASCADE)
    hand_position = models.IntegerField(default=1) 

    # Allow Cards to be filtered by Order
    class Meta:
        ordering = ('hand_position',)

# ------------------------------------------------------------------------------------------------------------------------------#
# --- CURRENCY MODELS --- #
# ------------------------------------------------------------------------------------------------------------------------------#
class Bet(models.Model):
    #############################################################################################################################
    # @brief      :       Creates django model class for a deck of Cards
    #############################################################################################################################
    player = models.ForeignKey(Profile, default=None, on_delete=models.PROTECT, related_name='player_bet', null=True, blank=True) 
    game = models.ForeignKey(Game, default=None, null=True, on_delete=models.PROTECT, related_name='game_bet')  

    # Number of Chips
    num_chips_5 = models.IntegerField(default=0)
    num_chips_10 = models.IntegerField(default=0)
    num_chips_25 = models.IntegerField(default=0)
    num_chips_50 = models.IntegerField(default=0)
    num_chips_100 = models.IntegerField(default=0)
    bet_order = models.CharField(default="", max_length=200)
    
    # --- STATIC METHODS --- #
    @staticmethod
    def create_new_bet(player, game):
        new_bet = Bet()
        new_bet.player = player
        new_bet.game = game

        new_bet.save()

    # --- METHODS --- #
    """
    @brief      :    Update the Value of the current bet
    @param[in]  :    chip_values - Array of No. of each chip type in bet
    @retval     :    None
    """ 
    def update_bet(self, chip_values, bet_order):
        self.num_chips_5 += int(chip_values[0])
        self.num_chips_10 += int(chip_values[1])
        self.num_chips_25 += int(chip_values[2])
        self.num_chips_50 += int(chip_values[3])
        self.num_chips_100 += int(chip_values[4])
        self.bet_order = bet_order
        self.save()

    def get_total_bet_value(self):
        total = self.num_chips_5 * 5 + self.num_chips_10 * 10 + self.num_chips_25 * 25 + self.num_chips_50 * 50 + self.num_chips_100 * 100
        return total

#class Chip(models.Model):
    #############################################################################################################################
    # @brief      :       Creates django model class for a deck of Cards
    #############################################################################################################################
    #value = models.IntegerField(default=0)
    #img_url = models.CharField(max_length=200, default="None")



