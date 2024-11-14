from flask import Flask
from flask import request
import pymongo
import time
import hashlib
from bson import ObjectId

app = Flask(__name__)

con = pymongo.MongoClient("mongodb://localhost:27017/")
db = con["vigyazzhat"]
tables = db["tables"]

def int_to_chars(integer):
    #Számjegysorozatból karakterláncot generál
    digit_to_letter = {
        '0': 'J', '1': 'A', '2': 'B', '3': 'C', '4': 'D', '5': 'E', '6': 'F', '7': 'G', '8': 'H', '9': 'I'
    }

    string = str(integer)
    string_out = ""

    for char in string:
        string_out += digit_to_letter[char]

    return string_out

def conv_to_hash(s):
    return hashlib.sha256(s.encode()).hexdigest()


def set_deck(game_id, deck):
    tables.update_one({ "_id" : game_id }, { "$set" : { "deck" : deck } })

def draw_from_deck(game_id, n):
    deck = tables.find_one({"_id" : game_id })["deck"]
    set_deck(game_id, deck[n:])
    return deck[:n]

def set_table(game_id):
    tables.update_one({ "_id" : game_id }, { "$set" : { "cards_in_play" : [[draw_from_deck(game_id, 1)[0], None, None, None, None] for _ in range(4)] } })

def get_players(game_id):
    return tables.find_one({ "_id" : game_id })["players"].keys()

def set_player_hand(game_id, player_id, cards):
    tables.update_one( { "_id" : game_id }, { "$set" : { f"players.{player_id}.hand" : cards } } )

@app.route("/create_table", methods=['POST'])
def create_table():
    owner = request.json["_playerName"]
    passwd = request.json["_password"]

    if tables.find_one( { 'owner' : conv_to_hash(owner) } ):
        return {}

    game = {
            "passwd": conv_to_hash(passwd),
            "owner": conv_to_hash(owner),
            "invite_string": conv_to_hash(owner)[-5:],
            "deck" : [],
            "cards_in_play": [
                [None, None, None, None, None, None],
                [None, None, None, None, None, None],
                [None, None, None, None, None, None],
                [None, None, None, None, None, None]
            ],
            "players": {}
        }
    
    game["players"][conv_to_hash(owner)] = {
        "player_name": owner,
        "hand": [],
        "ready" : False,
    }
    game_id = tables.insert_one(game).inserted_id

    ids = { 'table_id' : str(game_id), 'player_id' : conv_to_hash(owner), "inviteLink" : game["invite_string"]}

    return ids

@app.route("/join_game", methods=['POST'])
def join_game():
    player = request.json["_playerName"]
    inv_link = request.json["inviteLink"]
    passwd = request.json["_password"]

    ids = {}
    game = tables.find_one( { "invite_string" : inv_link } )
    if game["passwd"] == conv_to_hash(passwd):
        joining_player = { conv_to_hash(player) : { "player_name" : player , "hand" : [], "ready" : False }}
        tables.update_one( { "_id" : game['_id'] }, { "$set" : { f"players.{conv_to_hash(player)}" : joining_player[conv_to_hash(player)] } } )
        ids = { "table_id" : str(game['_id']), "player_id" : conv_to_hash(player) }

    return ids

@app.route("/get_game_state/<tableId>", methods=['GET'])
def get_game_state(tableId):
    try:
        game_id = ObjectId(tableId)
    except:
        return {}
    
    game = tables.find_one({"_id": game_id})
    return { "players" : {player_info["player_name"]: len(player_info["hand"]) for player_info in game["players"].values()}, "cards_in_play" : game["cards_in_play"] }
#           [ ,game["cards_in_play"]]

#print(get_game_state(ObjectId("673593f95dab2d87358385f1")))

@app.route("/ready", methods=['GET'])
def ready(player_id):
    # sets status of the player ready
    # check if all players are ready
    # admin's ready starts the game : start_game()  
    # returns initial game state
    pass

@app.route("/start_game", methods=['POST'])
def start_game():
    game_id = ObjectId(request.json["tableId"])
    player_id = request.json["playerId"]
    if tables.find_one( { "_id" : game_id } )["owner"] == player_id:
        from random import shuffle

        deck = list(range(1,105))
        shuffle(deck)

        set_deck(game_id, deck) # sets deck in the db
        set_table(game_id) # draw_from_deck gets info from database, slice the deck accordingly, writes remaining deck back and return the drawn cards # set_table sets the 2d array of the table in the db with the gotten cards
        
        players = get_players(game_id) # get player ids from db
        for player_id in players:
            set_player_hand(game_id, player_id, draw_from_deck(game_id, 10)) # draw 10 card and give to player in db
    return {"yes" : "you are"}
#start_game(ObjectId("673580670d90add60e6f1a59"))

if __name__  == '__main__':
    app.run()
    #client.close()