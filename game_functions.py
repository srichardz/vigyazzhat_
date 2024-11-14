import random
import uuid
import time
from bson.objectid import ObjectId

def shuffle_cards():
    #Összekeveri a kártyákat
    deck = [value for value in range(1,105)]
    random.shuffle(deck)
    return deck

def set_deck(deck):
    #A kevert paklit megkapja, visszaad négy random kártyát amik a sorkezdők lesznek
    starter_four = [deck.pop() for i in range(4)]
    return starter_four

def set_player_hands(deck):
    #A kevert pakli maradékát kiosztja 10 embernek (szerintem mindenképpen kioszthatjuk mindet, max nem játszanak velük)
    all_hands = [[deck.pop() for i in range(10)] for j in range(10)]
    return all_hands

def set_table(game_id):
    #A fenti függvényeket meghívva kiosztja a lapokat, amikkel megkezdhető a játék. Frissíti a játék adattábláját
    game = db.table.find_one({"_id": ObjectId(game_id)})

    deck = shuffle_cards()
    starter_four = set_deck(game_id,deck)
    hands = set_player_hands(game_id,deck)

    game["cards_in_play"][0][0] = starter_four[0]
    game["cards_in_play"][1][0] = starter_four[1]
    game["cards_in_play"][2][0] = starter_four[2]
    game["cards_in_play"][3][0] = starter_four[3]

    db.table.update_one(
        {"_id": ObjectId(game_id)},
        {"$set": {"cards_in_play": game["cards_in_play"]}}
    )

    i = 0
    for player_id, player_data in game["players"].items():
        player_data["hand"] = hands[i]
        i += 1
        db.table.update_one(
            {"_id": ObjectId(game_id)},
            {"$set": {f"players.{player_id}.hand": player_data["hand"]}}
        )

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

def init_game(player_name,passwd):
    #Létrehozza a kezdetleges táblát
    game = {
            "passwd": str(hash(passwd)),
            "owner": player_name,
            "invite_string": int_to_chars(hash(player_name+str(time.time()))[:5]),
            "cards_in_play": [
                [None, None, None, None, None, None],
                [None, None, None, None, None, None],
                [None, None, None, None, None, None],
                [None, None, None, None, None, None]
            ],
            "players": {}
        }
    unique_player_id = f"{uuid}"
    game["players"][unique_player_id] = {
        "player_name": "",
        "hand": []
    }
    game_id = db.table.insert_one(game).inserted_id

    return game_id

def player_to_game(player_name, invite_link, passwd):
    #Amennyiben a jelszó helyes és a link is megfelelő, a játékost hozzáadjuk a játékos collectionhöz
    game = db.table.find_one({"invite_link": ObjectId(invite_link)})
    if game["passwd"] == passwd:
        joining_player = {f"{uuid}": {"player_name":player_name,"hand":[]}}
        db.table.update_one(
        {"_id": game["_id"]},
        {"$set": joining_player}
    )
        
def get_game_state(game_id):
    #Visszaadja a játékosok nevét a lapjaik számával ellenőrzés céljából, valamint a lent lévő 4 sor állapotát
    game = db.table.find_one({"_id": ObjectId(game_id)})
    return [[[player_info["name"],len(player_info["hand"])] for player_info in game["players"].values()],game["cards_in_play"]]
