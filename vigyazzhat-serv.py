from flask import Flask
import pymongo
import uuid

app = Flask(__name__)

con = pymongo.MongoClient("mongodb://localhost:27017/")
db = con["vigyazzhat"]
tables = db["tables"]
tables.insert_one({"passwd" : "jelszo", "cards_in_play" : [[3, 3], [2, 2], [1, 1], [0, 0]], "players" : [{"hand" : []}, {"hand" : []}, {"hand" : []}, {"hand" : []}]})
@app.route("/login/<username>", methods=['GET'])
def login(username):
    user = tables.insert_one({"username" : username, "hand" : []})
    return str(user.inserted_id)
    # create user in db:
    # username (string)          - will be seen
    # uuid     (hash)            - used to communicate with the server, not public
    # hand     (array<int|byte>) - used to store cards as numbers/values, init to empty array
    # returns uuid (player_id)
    #pass
    return "<p>oooooo</p>"

@app.route("/create_table", methods=['POST'])
def create_table(passwd):
    # create table in db:
    # game_id (hash)
    # passwd  convert <string> to (hash) if present
    # invite_string (short sequence of characters converted from the hash)
    # table (2d array of int|byte)
    # returns uuid (game_id)
    pass

@app.route("/join_game", methods=['POST'])
def join_game(game_id, passwd):
    # connect a player to a table in db
    # returns other players' names
    pass

@app.route("/ready", methods=['GET'])
def ready(player_id):
    # sets status of the player ready
    # check if all players are ready
    # admin's ready starts the game : start_game()  
    # returns initial game state
    pass

def start_game(game_id):
    from random import shuffle

    deck = list(range(1,105))
    shuffle(deck)

    set_deck(game_id, deck) # sets deck in the db
    table = set_table(game_id, draw_from_deck(game_id, 20)) # draw_from_deck gets info from database, slice the deck accordingly, writes remaining deck back and return the drawn cards # set_table sets the 2d array of the table in the db with the gotten cards
    players = get_players(db, game_id) # get player ids from db
    for player_id in players:
        hand = set_player_hand(db, player_id, draw_from_deck(game_id, 10)) # draw 10 card and give to player in db

    # return game_state
    pass

def set_deck(game_id, deck):
    
    pass

if __name__  == '__main__':
    app.run()
    #client.close()