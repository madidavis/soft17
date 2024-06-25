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
import random
import time
import datetime
import json
from django.http import HttpResponse, Http404

### Django Modules ####
from django.shortcuts import get_object_or_404, render, redirect, get_list_or_404
from django.urls import reverse
from django.db import transaction

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout


### Local Libraries ###
from soft17.models import Profile, Game, Card, GameRoom
from soft17.forms import LoginForm, RegisterForm, ProfileForm
from soft17.card_data import card_data

from django.core.cache import cache
from django.utils import timezone



def initialize_cards():
    # create the cards for the game. This should run only once for the entire life of the application
    # there should only be 52 cards existing across all games
    # once the cards are made we set the flag my_project_initialized to True in the cache so that its not executed again
    if not cache.get('my_project_initialized'):
        print("creating cards")
        for card in card_data[0]["cards"]:
            Card.create_new_card(card["suit"], card["rank"], card["value"], card["file"])
        cache.set('my_project_initialized', True)


# Create your views here.
# ------------------------------------------------------------------------------------------------------------------------------#
# --- BASE VIEWS --- #
# ------------------------------------------------------------------------------------------------------------------------------#

# ------------------------------------------------------------------------------------------------------------------------------#
# --- LOGIN & LOGOUT VIEWS --- #
# ------------------------------------------------------------------------------------------------------------------------------#
"""
    @brief      :    load login page upon site launch
    @param[in]  :    request - Http Request
    @retval     :    render login page
"""
@transaction.atomic
def login_action(request):
    initialize_cards()
    # Define Context
    context = {}
    context['page_name'] = "Login"

    # If GET -  Render Login Page
    if request.method == 'GET':
        form = LoginForm()
        context['form'] = form 
        return render(request, 'soft17/login.html', context)

    # Otherwise if POST - Parse Form
    form = LoginForm(request.POST)
    context['form'] = form

    # Validate form
    if not form.is_valid():
        return render(request, 'soft17/login.html', context)
    
    # Authenticate User and Log In
    new_user = authenticate(username=form.cleaned_data['username'],
                            password=form.cleaned_data['password'])


    login(request, new_user)
    return redirect(reverse('game'))


"""
    @brief      :    logout user
    @param[in]  :    request - Http Request
    @retval     :    render login page
"""
def logout_action(request):
    logout(request)
    return redirect(reverse('login'))

# ------------------------------------------------------------------------------------------------------------------------------#
# --- REGISTRATION VIEWS --- #
# ------------------------------------------------------------------------------------------------------------------------------#
"""
    @brief      :    load register page upon site launch
    @param[in]  :    request - Http Request
    @retval     :    render user registration page
"""
@transaction.atomic
def register_action(request):
    initialize_cards()
    # Define Context
    context = {}
    context['page_name'] = "Register"

    # If GET display the Regstration form
    if request.method == 'GET':
        context['form'] = RegisterForm()
        return render(request, 'soft17/register.html', context)

    # If POST Request
    form = RegisterForm(request.POST)
    context['form'] = form 

    # Validates the form
    if not form.is_valid():
        return render(request, 'soft17/register.html', context)
    
    # Otherwise return and create new user
    new_user = User.objects.create_user(username=form.cleaned_data['username'],
                                        password=form.cleaned_data['password'],
                                        email=form.cleaned_data['email'],
                                        first_name=form.cleaned_data['first_name'],
                                        last_name=form.cleaned_data['last_name'])

    # Create Profile Model for User 
    new_profile = Profile(profile_user=new_user)    

    # Create Game room for single player mode
    single_room = GameRoom.create_new_single_player_room()
    new_profile.single_player_room = single_room
    new_profile.save()
    # Create Game --> always have a game running in single player mode
    Game.create_new_game(single_room)

    login(request, new_user)
    return redirect(reverse('game'))

# ------------------------------------------------------------------------------------------------------------------------------#
# --- PROFILE VIEWS --- #
# ------------------------------------------------------------------------------------------------------------------------------#
"""
    @brief      :    loads user's profile page 
    @param[in]  :    request - Http Request
    @retval     :    render user profile page
"""
@login_required
@transaction.atomic
def profile_action(request):
    # Define Context
    context = {}
    context['page_name'] = "Profile"
    context['id'] = request.user.id
    context['name'] = request.user.first_name + " " + request.user.last_name
    context['email'] = request.user.email
    context['username'] = request.user.username

    # If GET display the Regstration form
    if request.method == 'GET':
        profile_details = Profile.objects.get(profile_user__id=request.user.id)
        initial_data = {'wallet_balance': profile_details.wallet_balance}
        if not profile_details.user_picture:
            context['profileImage'] = "../../static/Assets/default.png"
        context['form'] = ProfileForm(initial=initial_data)
        context['wallet_balance'] = profile_details.wallet_balance
        return render(request, 'soft17/profile.html', context)
    
    profile = Profile.objects.get(profile_user__id=request.user.id)
    context['wallet_balance'] = profile.wallet_balance
    form = ProfileForm(request.POST, request.FILES)
    if form.is_valid():
        if form.cleaned_data['user_picture'] is not None:
            profile.content_type = form.cleaned_data['user_picture'].content_type
            profile.user_picture = form.cleaned_data['user_picture']
        if form.cleaned_data['wallet_balance']:
            profile.wallet_balance = form.cleaned_data['wallet_balance']
        profile.save()
        return redirect(profile_action)
    else:
        context['form'] = form
        if not profile.user_picture:
            context['profileImage'] = "../../static/Assets/default.png"
        return render(request, 'soft17/profile.html', context)

@login_required
def get_photo(request, id):
    profile = Profile.objects.get(profile_user__id = id)
    item = get_object_or_404(Profile, id=profile.id)
    if not item.user_picture:
        raise Http404

    return HttpResponse(item.user_picture, content_type=item.content_type)




# ------------------------------------------------------------------------------------------------------------------------------#
# --- GAME VIEWS --- #
# ------------------------------------------------------------------------------------------------------------------------------#
"""
    @brief      :    loads home / game page 
                        --> This is the single player Game
                        --> resume single player game from last stae 
    @param[in]  :    request - Http Request
    @retval     :    render soft17 home / game page 
"""
@login_required
@transaction.atomic
def game_action(request):
    context = {}
    context['id'] = request.user.id
    # Check for User's Single Player Current Game 
    profile = Profile.objects.get(profile_user=request.user)
    game_room = profile.single_player_room
    current_game = game_room.get_current_game()

    # Get User's Current Wallet Balance and Bet & Load into hidden fields
    player_bet = current_game.get_player_bet(profile)
    context["wallet_balance"] = profile.wallet_balance
    context["bet_value"] = player_bet.get_total_bet_value()
    context["num_chips_5"] = player_bet.num_chips_5
    context["num_chips_10"] = player_bet.num_chips_10
    context["num_chips_25"] = player_bet.num_chips_25
    context["num_chips_50"] = player_bet.num_chips_50
    context["num_chips_100"] = player_bet.num_chips_100
    context["bet_order"] = player_bet.bet_order

    # Get game room Info 
    context["room_balance"] = game_room.balance

    profile_details = Profile.objects.get(profile_user__id=request.user.id)
    if not profile_details.user_picture:
        context['profileImage'] = "../../static/Assets/default.png"

    return render(request, 'soft17/game.html', context)


# --- AJAX CALLS --- #
"""
    @brief      :    format game data as a JSON
    @param[in]  :    player, dealer, current_game, game_room
    @retval     :    json
"""
def format_game_state_json(profile, dealer,current_game, game_room, last_action):
    dealer_cards_response = []
    # User info
    player_cards_response = []
    
    ''' @note: format user info '''
    # Get a List of all Cards in Player's (Main User) Hand
    player_hand = current_game.get_player_hand(profile)
    player_cards = player_hand.get_hand_cards()
    for card in player_cards:
        card = {
            'id': card.id,
            'url': card.url,
            'value': card.value,
        }
        player_cards_response.append(card)
    
    # Add User info 
    player_info = {
        'id': profile.id,
        'username': profile.profile_user.username,
        'cards': player_cards_response,
        'hand_value': get_player_hand_value(player_hand),
        'wallet': profile.wallet_balance
    }


    ''' @note: format dealer info '''
    # Get a List of all Cards in Dealer's Hand
    dealer_hand = current_game.get_dealer_hand(dealer)
    dealer_cards = dealer_hand.get_hand_cards()
    for card in dealer_cards:
        card = {
            'id': card.id,
            'url': card.url,
            'value': card.value,
        }
        dealer_cards_response.append(card)
    
    # Add dealer info 
    dealer_info = {
        'cards': dealer_cards_response,
        'hand_value' : get_player_hand_value(dealer_hand),
        'pot' : game_room.balance
    }

    result = current_game.get_game_result(profile, dealer)

    ''' @note: format additional state & ui info '''
    
    ''' @note: format final json '''
    game_state_json = json.dumps({'player_info': [player_info], 'dealer_info': [dealer_info], 'game_state': str(current_game.curr_state), 'result': result, 'last_action': last_action})

    return game_state_json




def _my_json_error_response(message, game_state, status=200):
    # You can create your JSON by constructing the string representation yourself (or just use json.dumps)
    response_json = '{"error": "' + message + '", "game_state": "' + str(game_state) + '"}'
    return HttpResponse(response_json, content_type='application/json', status=status)



def get_player_hand_value(hand):
    max_hand_value = hand.get_max_hand_value()
    hand_value = hand.hand_value
    hand_value_text = str(hand_value)
    if(hand_value != max_hand_value):
        if(max_hand_value > 21):
            pass
        elif max_hand_value == 21:
            hand_value_text = str(max_hand_value)
        elif(max_hand_value < 21):
            hand_value_text = str(hand_value) + " OR " + str(max_hand_value)
    return hand_value_text




"""
    @brief      :    finite state machine single player - exzecute game code depensing on current game state 
                        - Checks values and actions associated with CURRENT STATE
                        - This function is called by front-end to get game context
                        - Will check current state and perform changes to model
                        - Will produce a json and send to UI based on current game state
    @param[in]  :    request - Http Request
    @retval     :    render soft17 home / game page 
"""
@login_required
@transaction.atomic
def single_player_curr_state(request):
    # Create Data Structure to send out info as json
    json_output = {}
    # Get All Current Game models
    # -- MODEL DATA REFERENCES -- #
    profile = Profile.objects.get(profile_user=request.user)
    game_room = profile.single_player_room
    dealer = game_room.get_dealer()
    current_game = game_room.get_current_game()
    player_hand = current_game.get_player_hand(profile)
    dealer_hand = current_game.get_dealer_hand(dealer)
    last_action = ""


    # Case through States
    if current_game.curr_state == 0: # reset game
        """ STATE 0 => RESET GAME """
        pass
    elif current_game.curr_state == 1: # start game
        """ STATE 1 => START GAME """
        current_game.curr_state = Game.Game_State.PLACE_BET
    elif current_game.curr_state == 2: # Place bets
        """ STATE 2 => PLACE BETS           """
        # Model Data is Obtained from hidden fields 
        # Betting Actions Performed in JS
        pass
    elif current_game.curr_state == 3:     # DEAL_PLAYERS
        """ STATE 3 => DEAL PLAYERS """
        # Deal Player 2 cards
        if (player_hand.num_cards < 2):
            current_game.deal_card_to_player(profile)

    elif current_game.curr_state == 4:     # DEAL_DEALER
        """ STATE 4 => DEAL DEALERS"""
        # Deal Dealer 2 cards
        if (dealer_hand.num_cards < 2):
            current_game.deal_card_to_dealer(dealer)

    elif current_game.curr_state == 5:     # PLAYER_TURN
        """ STATE 5 => PLAYER TURN """
        # State Dependent on UI Updates
        pass

    elif current_game.curr_state == 6:     # PLAYER_SCORE
        """ STATE 6 => PLAYER SCORE """
        # Only involves next state calculation
        pass
    elif current_game.curr_state == 7:     # DEALER_TURN
        """ STATE 7 => DEALER TURN """
        current_game.dealer_move(dealer)
        pass
        #play_dealers_turn(current_game)
        #play_dealers_turn(current_game)
    elif current_game.curr_state == 8:     # COMPUTE_SCORES
        """ STATE 9 => COMPUTE SCORE / RESULTS """
        compute_scores_of_single_player_game(current_game, profile, dealer)

    current_game.save()
    
    json_output = format_game_state_json(profile, dealer,current_game, game_room, last_action)

    # Send JSON to UI
    return HttpResponse(json_output, content_type="applications/json")

"""
    @brief      :    finite state machine single player - exzecute game code depensing on current game state 
                        - MAKES CHANGES TO UPDATE FSM STATE
                        - This function is called by front-end in response to player action or ui event
                        - Will make corresponding changes to database and update game state 
    @param[in]  :    request - Http Request
    @retval     :    render soft17 home / game page 
"""
@login_required
@transaction.atomic
def single_player_next_state(request):
    print("Calling next state function")
    # -- REQUEST DATA -- #
    bet_data = (request.POST["bet_data"]).split(",")
    bet_order = request.POST["bet_order"]
    game_action = request.POST["game_action"]

    # -- MODEL DATA REFERENCES -- #
    profile = Profile.objects.get(profile_user=request.user)
    game_room = profile.single_player_room
    current_game = game_room.get_current_game()
    dealer = current_game.get_dealer()
    last_action = "" # Last Game Action --> Need this for UI timing
    player_hand = current_game.get_player_hand(profile)
    dealer_hand = current_game.get_dealer_hand(dealer)

    # Case through States
    if current_game.curr_state == 0:     # RESET GAME
        """ STATE 0 => RESET GAME """
        pass
    elif current_game.curr_state == 1:     # START GAME
        """ STATE 1 => START GAME """
        pass
        #current_game.curr_state = Game.Game_State.PLACE_BET
    elif current_game.curr_state == 2:     # PLACE_BET
        """ STATE 2 => PLACE BET """
        # Update if Bet Submitted
        if (game_action == "submit_bet"):
            # Get reference to player bet for curr game
            player_bet = current_game.get_player_bet(profile)
            # Update model data based on inputs from UI
            player_bet.update_bet(bet_data, bet_order)
            # Update Game State
            current_game.curr_state = Game.Game_State.DEAL_PLAYERS
    elif current_game.curr_state == 3:     
        """ STATE 3 => DEAL PLAYER """
        # Wait for UI Event Listener
        if (game_action == "finished_dealing" and player_hand.num_cards == 2):
            # Update State
            current_game.curr_state = Game.Game_State.DEAL_DEALER
    elif current_game.curr_state == 4:     
        """ STATE 4 => DEAL DEALER """
        # Wait for UI Event Listener
        if (game_action == "finished_dealing" and dealer_hand.num_cards == 2):
            # Check for Natural Blackjack & Update State
            if(player_hand.is_natural_blackjack()):
               current_game.curr_state = Game.Game_State.DEALER_TURN
            else:
               current_game.curr_state = Game.Game_State.PLAYER_TURN 

        #if (dealer_hand.num_cards == 0):
           # current_game.deal_card_to_dealer(dealer)
            #current_game.deal_card_to_dealer(dealer)
       # else:
            #player_hand = current_game.get_player_hand(profile)
           # if(player_hand.is_natural_blackjack()):
               # current_game.curr_state = Game.Game_State.DEALER_TURN
           # else:
               # current_game.curr_state = Game.Game_State.PLAYER_TURN
    elif current_game.curr_state == 5:     # PLAYER_TURN
        """ STATE 5 => PLAYER TURN """
        # Wait for UI Button Actions
        print("player_turn")
        if (game_action == "player_hit"):
            hit_result = current_game.player_hit(profile)
            print("HIT")
            if not hit_result:
                # Update State if Hit >= 21
                current_game.curr_state = Game.Game_State.PLAYER_SCORE
        elif (game_action == "player_stand"):
            # Update State to Dealer turn
            current_game.player_stand()
        elif (game_action == "player_double"):
            # Update Bet & Call Double Function
            current_game.player_double(profile, bet_data, bet_order)
            current_game.curr_state = Game.Game_State.PLAYER_SCORE


        #if current_game.curr_state != Game.Game_State.PLAYER_TURN:
            # If it's not player's turn
            #return _my_json_error_response("It is not your turn to play!", current_game.curr_state, status=400)
        # If Action == HIT 
        #if (game_action == "player_hit"):
           # current_game.player_hit(profile)
            #last_action = "player_hit"
        #elif (game_action == "player_stand"):
            #current_game.player_stand()
            #last_action = "player_stand"
        #elif (game_action == "player_double"):
            #last_action = "player_double"
           # player_hand = current_game.get_player_hand(profile)
            # If player's hand is empty deal two cards
            #if (player_hand.num_cards == 2):
                #current_game.player_double(profile, bet_data, bet_order)
    elif current_game.curr_state == 6:     # PLayer SCORE
        """ STATE 6 => PLAYER SCORE """
        # Wait for UI Event Listener to check if finished Dealing
        if (game_action == "finished_dealing"):
            # Only 1 card 
            current_game.curr_state = Game.Game_State.DEALER_TURN

    elif current_game.curr_state == 7:     # DEALER_TURN
        """ STATE 7 => DEALER TURN """
        # Check Card Deal Finished
        if (game_action == "finished_dealing"):
            # update if bust
            print("finished")
            if not dealer_hand.check_under_17() or dealer_hand.check_soft17():
                current_game.curr_state = Game.Game_State.COMPUTE_SCORES
        #dealer_hit_successful = current_game.dealer_move(dealer)
        #if not dealer_hit_successful:
            # Only Finish Dealers turn if bust occurs
            #print("hi")
            #current_game.curr_state = Game.Game_State.COMPUTE_SCORES
        #last_action = "dealer_hit"
    elif current_game.curr_state == 8:     # COMPUTE SCORES
        """ STATE 9 => COMPUTE SCORE / RESULTS """
        pass
        #compute_scores_of_single_player_game(current_game, profile, dealer)
    
    current_game.save()
    
    # Construct New JSON to output to UI
    json_output = format_game_state_json(profile, dealer,current_game, game_room, last_action)

    # Case through All States
    return HttpResponse({}, content_type="applications/json")



def play_dealers_turn(current_game):
    dealer_hit_successful = True
    dealer = current_game.get_dealer()
    while dealer_hit_successful:
        dealer_hit_successful = current_game.dealer_move(dealer)
    current_game.save()



# Method to divide the bets according to the result of the game
def compute_scores_of_single_player_game(current_game, profile, dealer):
    current_game.curr_state = Game.Game_State.COMPUTE_SCORES
    current_game.is_completed = True
    current_game.completed = timezone.now()
    current_game.settle_bets(profile, dealer)
    current_game.save()



# Note --> i just ended up separating these functions to make it easier
# if we have a separate html file for single player / mutliplaye it should be fine
# to do this and still have 1 model definition for game 
"""
    @brief      :    finite state machine multiplayer - exzecute game code depensing on current game state 
                        - This function is called every time action action is done to change game
                          state in the UI
                        - Will check current state and perform back-end changes to model
    @param[in]  :    request - Http Request
    @retval     :    render soft17 home / game page 
"""
@login_required
def multiplayer_player_game_state(request):
    # Get All Current Game models
    pass