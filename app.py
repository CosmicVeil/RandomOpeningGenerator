from flask import Flask, render_template, request, redirect, url_for
import requests, random
from openai import OpenAI
import os

app = Flask(__name__)

# Initialize the OpenAI client
OPENAI_API_KEY = os.environ.get(API_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)

# Lichess API Base URL
LICHESS_BASE_URL = "https://lichess.org/paste?fen="

choseOpenings = []

openings = {"black": {"aggressive": ["Scandinavian Defense", "Alekhine's Defense", "Pirc Gambit"], "safe": ["Sicilian Defense", "Caro-Kann Defense", "French Defense"]},
                      "white": {"aggressive": ["King's Gambit", "Ruy Lopez", "Italian"], "safe": ["Queen's Gambit", "English", "London System"]}}
fenValue = {"Scandinavian Defense": "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", "Alekhine's Defense": "rnbqkb1r/pppppppp/5n2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 1 2", "Pirc Gambit": "rnbqkb1r/ppp1pppp/3p1n2/8/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 1 3",
            "Sicilian Defense": "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", "Caro-Kann Defense": "rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            "French Defense": "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            "King's Gambit": "rnbqkbnr/pppp1ppp/8/4p3/4PP2/8/PPPP2PP/RNBQKBNR b KQkq - 0 2", "Ruy Lopez": "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
            "Italian" : "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3", "Queen's Gambit": "rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2",
            "English ": "rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq - 0 1", "London System": "rnbqkbnr/ppp1pppp/8/3p4/3P1B2/8/PPP1PPPP/RN1QKBNR b KQkq - 1 2"}

gameValues = {"Italian": ["Sxov6E94"], "Scandinavian Defense": ["qGeCrW3o"],"Alekhine's Defense": ["J1tOgIW5"],
              "Pirc Gambit": ["czkdJ4Am"], "Sicilian Defense": ["CA4oVUCt"], "Caro-Kann Defense": ["PIyXpond"], "French Defense": ["study/87BSSiOv/Vye856mM"],
              "King's Gambit": ["aZ6oVKX6"], "Ruy Lopez": ["aGgqaZWK"], "Queen's Gambit": ["csT4wq1I"], "English": ["6znQRbJd"], "London System": ["751DRMPG"]}

# Home route for the input form
@app.route('/')
def index():
    return render_template('index.html')

def get_opening_stats_from_lichess(fen):
    url = f"https://explorer.lichess.ovh/master?fen={fen}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        win_white = data.get('white', 0)
        win_black = data.get('black', 0)
        draw = data.get('draws', 0)

        win_rate_white =round(win_white/(win_black+win_white+draw)*100)
        win_rate_black =round(win_black/(win_black+win_white+draw)*100)
        draw_rate =round(draw/(win_black+win_white+draw)*100)
        
        #games = data.get('topGames', [])
        print(win_rate_black, win_rate_white, draw_rate)
        return {
            "white": win_rate_white,
            "black": win_rate_black,
            "draw": draw_rate,
        }
    else:
        return None

# Generate opening based on user input
@app.route('/generate', methods=['POST'])
def generate_opening():
    color = request.form.get('color')
    style = request.form.get('style')

    # Call OpenAI API to get the opening details
    opening_fen, name, description = get_opening_from_db(color, style)

    if opening_fen:
        return redirect(url_for('show_opening', fen=opening_fen, name=name, description=description))
    else:
        return "No opening found", 404

# Show the opening with the chess information using Lichess viewer
@app.route('/opening')
def show_opening():
    fen = request.args.get('fen')
    name = request.args.get('name')  # Get the name from the query parameters
    description = request.args.get('description')  # Get the description from the query parameters

    opening_stats = get_opening_stats_from_lichess(fen)
    whiteWinMsg = f"White Win Rate: {opening_stats["white"]}%"
    blackWinMsg = f"Black Win Rate: {opening_stats["black"]}%"
    drawWinMsg = f"Draw Rate: {opening_stats["draw"]}%"

    msgStats = [whiteWinMsg,blackWinMsg,drawWinMsg]

    color = ""

    for i in range(len(fen)):
        c = fen[i]
        if c == 'w' and fen[i-1] == " " and fen[i+1] == " ":
            color = "black"
            break

        elif c== 'b' and fen[i-1] == " " and fen[i+1] == " ":
            color = "white"
            break

    lichessLink = f"https://lichess.org/analysis/{fen}?color={color}"
    
    gameLink = random.choice(gameValues[name])

    matchLink = f"https://lichess.org/{gameLink}?color={color}"

    return render_template('opening.html', fen=fen, name=name, description=description,stats=msgStats, link=lichessLink,match=matchLink)

# # Function to call OpenAI and get the chess opening
# def get_opening_from_openai(color, style, memorizationLevel):
#     prompt = f"""Generate a {style} chess opening for {color}. It should be {memorizationLevel} to memorize. 
#     It shoud also be pre-exisiting, with given names. Give the name on line 1. fen on line 2. The fen should be complete with play dfor both sides
#     And a short description (3 sentences on line 3). There should be no extra spaces between the lines. Make sure
#     the opening is not in {choseOpenings}"""

#     response = client.chat.completions.create(
#         model="gpt-4-turbo",
#         messages=[{"role": "user", "content": prompt}]
#     )
    
#     # Extract the name, fen, and description from the response
#     lines = response.choices[0].message.content.splitlines()

#     name = lines[0]  # Name of the opening
#     fen = lines[1]  # fen moves
#     description = lines[2]  # Description of the opening

#     choseOpenings.append(name);
    
#     return fen, name, description

# Function to call OpenAI and get the chess opening
def get_opening_from_db(color, style):

    opening = random.choice(openings[color][style])
    openings[color][style].remove(opening);

    prompt = f"""Generate a description for chess {opening}, should be 2-3 sentences"""

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Extract the name, fen, and description from the response
    lines = response.choices[0].message.content.splitlines()

    fen = fenValue[opening]
    description = lines[0]  # Description of the opening

    
    return fen, opening, description


if __name__ == '__main__':
    app.run(debug=True)
