#################################################################################################################################
#     @file     :    urls.py   
#
#     @brief    :    Maps web request to soft17 application views.py functions & templates 
#
#     @authors  :    Madi Davis (madelind@andrew.cmu.edu) & Aishwarya Yadav (ayadav2@andrew.cmu.edu)
#################################################################################################################################

# ------------------------------------------------------------------------------------------------------------------------------#
# --- INCLUDES --- #
# ------------------------------------------------------------------------------------------------------------------------------#
### Django Modules ####
from django.urls import path

### Local Libraries ###
from soft17 import views


# ------------------------------------------------------------------------------------------------------------------------------#
# --- URL DEFINITIONS --- #
# ------------------------------------------------------------------------------------------------------------------------------#
urlpatterns = [
    # --- LOAD VIEW PAGES --- #
    path('', views.game_action, name='home'),
    path('login', views.login_action, name='login'),
    path('logout', views.logout_action, name='logout'),
    path('register', views.register_action, name='register'),
    path('profile', views.profile_action, name='profile'),
    path('game', views.game_action, name='game'),
    path('photo/<int:id>', views.get_photo, name='photo'),
    

    # --- ASYNC UPDATES --- #
    #path('get-cards', views.get_game_cards, name="get-cards"),
    path('single-curr-state', views.single_player_curr_state, name="single-curr-state"),
    path('single-next-state', views.single_player_next_state, name="single-next-state"),
    # path('hit', views.player_hit_action, name="hit"),
    # path('stand', views.player_stand_action, name="stand"),
    # path('double', views.player_double_action, name="double")

]


