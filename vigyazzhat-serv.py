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

def conv_to_hash(s):
    """
    generating hashes from playername (for id purposes) and password (yes)
    """
    return hashlib.sha256(s.encode()).hexdigest()

@app.route("/create_table", methods=['POST'])
def create_table():
    """
    initialize a game and a player and return their ids
    """
    owner = request.json["_playerName"]
    passwd = request.json["_password"]
    
    own_hash = conv_to_hash(owner)
    
    # TODO: exception handling
    if tables.find_one( { 'owner' : own_hash } ):
        return {}

    game = {
            "passwd": conv_to_hash(passwd),
            "owner": own_hash,
            "invite_string": own_hash[-5:],
            "status" : "lobby",
            "cards_in_play": [
                [],
                [],
                [],
                []
            ],
            "round_buffer" : [],
            "players": {}
        }
    
    game["players"][own_hash] = {
        "player_name": owner,
        "hand": [],
        "ready" : False,
        "bullheads" : 0,
        "eligible" : False
    }

    game_id = tables.insert_one(game).inserted_id
    ids = { 'table_id' : str(game_id), 'player_id' : own_hash, "inviteLink" : game["invite_string"]}

    return ids

@app.route("/join_game", methods=['POST'])
def join_game():
    """
    initialize player in db
    """
    player = request.json["_playerName"]
    inv_link = request.json["inviteLink"]
    passwd = request.json["_password"]

    ids = {"message" : "Table already full!"}
    game = tables.find_one( { "invite_string" : inv_link } )
    if game["passwd"] == conv_to_hash(passwd) and len(game["players"]) < 6:
        joining_player = { conv_to_hash(player) : { "player_name" : player , "hand" : [], "ready" : False, "bullheads" : 0, "eligible" : False}}
        tables.update_one( { "_id" : game['_id'] }, { "$set" : { f"players.{conv_to_hash(player)}" : joining_player[conv_to_hash(player)] } } )
        ids = { "table_id" : str(game['_id']), "player_id" : conv_to_hash(player) }

    return ids

@app.route("/get_game_state/<tableId>", methods=['GET'])
def get_game_state(tableId):
    """
    short polling, this gives all the necessary info to the frontend
    """
    try:
        game_id = ObjectId(tableId)
    except:
        return {}
    
    game = tables.find_one({"_id": game_id})
    if game["status"] == "lobby":
        return { "players" : {player_info["player_name"]: player_info["ready"] for player_info in game["players"].values()}, "cards_in_play" : game["cards_in_play"], "status" : game["status"] }
    elif game["status"] == "started" or game["status"] == "ended":
        return { "players" : {player_info["player_name"]: player_info["bullheads"] for player_info in game["players"].values()}, "cards_in_play" : game["cards_in_play"], "status" : game["status"] }

@app.route("/get_hand", methods=['POST'])
def get_hand():
    """
    redundant, could use select_card endpoint for the same purpose, also this gets called exactly once per match per player,
    select_card endpoint does its job after that
    """
    print("REDUNDANT ENDPOINT /get_hand, could get deprecated and removed in the future")
    game_id = ObjectId(request.json["tableId"])
    player_id = request.json["playerId"]
    game = tables.find_one({"_id": game_id})
    hand = game["players"][player_id]["hand"]
    return {"hand" : hand, "message" : "redundant endpoint, could get deprecated and removed in the future. Use /select_card instead."}

@app.route("/ready", methods=['POST'])
def ready():
    """
    Handle optional ready for match function
    """
    game_id = ObjectId(request.json["tableId"])
    player_id = request.json["playerId"]

    game = tables.find_one({"_id": game_id})
    print(not game["players"][player_id]["ready"]*-1)
    tables.update_one( { "_id" : game['_id'] }, { "$set" : { f"players.{player_id}.ready" : not game["players"][player_id]["ready"] } } )
    
    return {'message' : 'success'}

@app.route("/start_game", methods=['POST'])
def start_game():
    """
    initialize game and start it
    """
    game_id = ObjectId(request.json["tableId"])
    player_id = request.json["playerId"]
    if tables.find_one( { "_id" : game_id } )["owner"] == player_id:
        from random import shuffle

        deck = list(range(1,105))
        shuffle(deck)

        tables.update_one({ "_id" : game_id }, { "$set" : { "cards_in_play" : [[deck[i]] for i in range(4)] } }) # set table
        deck = deck[4:]
        
        players = tables.find_one({ "_id" : game_id })["players"].keys()
        for player_id in players:
            tables.update_one( { "_id" : game_id }, { "$set" : { f"players.{player_id}.eligible" : True } } )
            tables.update_one( { "_id" : game_id }, { "$set" : { f"players.{player_id}.hand" : deck[:10] } } )
            deck = deck[10:]

        game = tables.find_one({"_id": game_id})
        tables.update_one( { "_id" : game['_id'] }, { "$set" : { f"status" : "started" } } )

    return {"message" : "Game started successfully"}

@app.route("/leave", methods=['DELETE'])
def leave():
    game_id = ObjectId(request.json["tableId"])
    player_id = request.json["playerId"]
    
    tables.update_one(
        {"_id": game_id},  # Find the table by ID
        {"$unset": {f"players.{player_id}": ""}}  # Remove the player with the specific playerid
    )
    return {"message" : "table left successfully"}

@app.route("/select_card", methods=['POST'])
def select_card():
    """
    could have bugs
    a bit overcrowded
    but it works-ish
    """
    game_id = ObjectId(request.json["tableId"])
    player_id = request.json["playerId"]
    card = request.json["card"]
    
    game = tables.find_one({"_id": game_id})

    # Checking if player posesses card chosen by player and if player is allowed to place card (haven't already, not end of the turn etc.)
    if card in game["players"][player_id]["hand"] and game["players"][player_id]["eligible"]:
        # Disallow any more card placing in turn
        tables.update_one( { "_id" : game_id }, { "$set" : { f"players.{player_id}.eligible" : False } } )
        
        # Update players hand
        new_hand = [h for h in game["players"][player_id]["hand"] if h != card]
        tables.update_one( { "_id" : game_id }, { "$set" : { f"players.{player_id}.hand" : new_hand } } )
        
        # Place card in round buffer
        round_buf = list(game["round_buffer"])
        round_buf.append(card)
        tables.update_one( { "_id" : game_id }, { "$set" : { f"round_buffer" : round_buf} } )
        game = tables.find_one({"_id": game_id})

        # Will be explained at function call below, necessary for the placement decision
        set_zero = lambda x: 105 if x < 0 else x

        # If this player was the last one to chose a card, initiate placement of cards from the buffer
        # Here it would make sense to call a function that implements this, but at first I didnt want
        # additional db setup, didn't think at first this gets big
        if len(game["round_buffer"]) == len(game["players"]):
            for i, card in enumerate(sorted(game["round_buffer"])):
                cards_in_play = game["cards_in_play"]

                # card - last_card_of_row
                # there are 3 options
                # ~ All of the last cards of rows are bigger than chosen card => takes row with smallest bullhead number
                # ~ All of the last cards of rows are smaller than chosen card => place it in row where card - last_card_of_row is smallest (closest to zero)
                # ~ Mixed => Can only be put in rows where card - last_card_of_row > 0, then option 2
                # This is implemented via setting all the n < 0 numbers to 105, an impossible and highest in game value so their row never gets chosen ("they are furthest away")
                print(cards_in_play, card)
                row_dist = [card-c[-1] for c in cards_in_play]
                row_idx = [set_zero(ele) for ele in row_dist].index(min([set_zero(ele) for ele in row_dist]))

                # If all last of rows are bigger
                if all([True if ele < 0 else False for ele in row_dist]):
                    # calculate bullheads of all rows
                    bh_in_cin = [
                        sum([
                            (2 if str(card)[-1] == '5' else 0) + (3 if str(card)[-1] == '0' else 0) + (5 if len(str(card)) != 1 and str(card)[0] == str(card)[1] else 0) + (1 if str(card)[-1] != '5' and str(card)[-1] != '0' and not (len(str(card)) != 1 and str(card)[0] == str(card)[1]) else 0) for card in row
                        ]) 
                    
                        for row in cards_in_play
                    ]

                    # take smallest valued row and update the bullheads value for the player, place their card as the first of that row
                    lowest_bh_idx = bh_in_cin.index(min(bh_in_cin))
                    bullheads = game["players"][player_id]["bullheads"] + bh_in_cin[lowest_bh_idx]
                    tables.update_one( { "_id" : game_id }, { "$set" : { f"players.{player_id}.bullheads" : bullheads } } )
                    if bullheads > 66:
                        end_game(game_id)
                    cards_in_play[lowest_bh_idx] = [card]
                    tables.update_one( { "_id" : game_id }, { "$set" : { f"cards_in_play" : cards_in_play} } )

                # check if the card would be the sixth, if yes that row will be taken and the bullheads will be added to the player
                elif len(cards_in_play[row_idx]) == 5:
                    bullheads = game["players"][player_id]["bullheads"] + sum((2 if str(card)[-1] == '5' else 0) + (3 if str(card)[-1] == '0' else 0) + (5 if len(str(card)) != 1 and str(card)[0] == str(card)[1] else 0) + (1 if str(card)[-1] != '5' and str(card)[-1] != '0' and not (len(str(card)) != 1 and str(card)[0] == str(card)[1]) else 0) for card in cards_in_play[row_idx])
                    tables.update_one( { "_id" : game_id }, { "$set" : { f"players.{player_id}.bullheads" : bullheads} } )
                    if bullheads > 66:
                        end_game(game_id)
                    cards_in_play[row_idx] = [card]
                    tables.update_one( { "_id" : game_id }, { "$set" : { f"cards_in_play" : cards_in_play} } )
                
                # if nothing special happens, place the card to the end of the appropriate row
                else:
                    cards_in_play[row_idx].append(card)

                tables.update_one( { "_id" : game_id }, { "$set" : { f"cards_in_play" : cards_in_play} } )
            # empty round buffer, make players eligible for card placement
            tables.update_one( { "_id" : game_id }, { "$set" : { f"round_buffer" : []} } )

            for _id in game["players"].keys():
                if len(game["players"][_id]["hand"]) == 0:
                    end_game(game_id)
                tables.update_one( { "_id" : game_id }, { "$set" : { f"players.{_id}.eligible" : True } } )

    return {'hand' : game["players"][player_id]["hand"]}

def end_game(game_id):
    game = tables.find_one({"_id": game_id})
    
    for _id in game["players"].keys():
        tables.update_one( { "_id" : game_id }, { "$set" : { f"players.{_id}.eligible" : False } } )
    
    tables.update_one( { "_id" : game['_id'] }, { "$set" : { f"status" : "ended" } } )

if __name__  == '__main__':
    app.run()
    #client.close()