import mysql.connector

# Functie om webshop-URL + naam op te slaan in DB (indien nog niet aanwezig)
def store_webshops(webshops: dict):
    try:
        # Verbind met MySQL
        db_connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="py_diski_webshops"
        )
        cursor = db_connection.cursor()

        for webshop_name, url in webshops.items():

            # Check of deze URL al in de database zit
            cursor.execute(
                "SELECT id FROM webshop_info WHERE webshop_url = %s",
                (url,)
            )
            existing = cursor.fetchone()

            if existing:
                print(f"Webshop already exists in DB: {webshop_name} ({url})")
                continue

            # Voeg toe aan DB
            insert_query = """
                INSERT INTO webshop_info (webshop_url, webshop_name)
                VALUES (%s, %s)
            """
            cursor.execute(insert_query, (url, webshop_name))
            db_connection.commit()
            print(f"Inserted: {webshop_name} ({url})")

        # Sluit verbinding
        cursor.close()
        db_connection.close()

    except mysql.connector.Error as err:
        print(f"Database error: {err}")

# Test block
if __name__ == "__main__":
    webshops = {
        "shein": "https://nl.shein.com/",
        "gymshark": "https://nl.gymshark.com/",
        "temu": "https://www.temu.com/nl-en",
        "aliexpress": "http://nl.aliexpress.com/",
        "pullandbear": "https://www.pullandbear.com/nl/",
        "cabaulifestyle": "https://cabaulifestyle.com/",
        "lookfantastic": "https://www.lookfantastic.nl",
        "lounge by zalando": "https://www.zalando-lounge.nl/",
        "mediamarkt": "https://www.mediamarkt.nl/",
        "amazon": "https://www.amazon.nl/",
        "meetmethere": "https://meet-me-there.com/?country=NL",
        "burga": "https://burga.nl/",
        "thuisbezorgd": "https://www.thuisbezorgd.nl/",
        "aybl": "https://nl.aybl.com",
        "greetz.nl": "https://www.greetz.nl/nl/",
        "upfront": "https://upfront.nl/",
        "adidas": "https://www.adidas.nl/",
        "hema": "https://www.hema.nl/",
        "idealofsweden": "https://idealofsweden.nl/",
        "myproteinnl": "https://nl.myprotein.com/",
        "sizzthebrand": "https://sizzthebrand.com/",
        "jdsports": "https://www.jdsports.nl/",
        "otrium": "https://www.otrium.nl/dames",
        "smartphonehoesjes.nl": "https://www.smartphonehoesjes.nl/",
        "creamyfabrics": "https://creamyfabrics.com/nl",
        "albelli": "https://www.albelli.nl/",
        "paulaschoice.nl": "https://www.paulaschoice.nl/nl",
        "emyjewels": "https://emyjewels.com/",
        "westwing": "https://www.westwing.nl/",
        "bodyandfit.com": "https://www.bodyandfit.com",
        "desenio": "https://desenio.nl/",
        "ninjakitchen": "https://ninjakitchen.nl/",
        "dilling": "https://www.dilling.nl/",
        "lyko": "https://lyko.com/nl",
        "bjornborg": "https://www.bjornborg.com/nl/",
        "thingsilikethingsilove": "https://www.thingsilikethingsilove.com/",
        "etos": "https://www.etos.nl/",
        "coolblue": "https://www.coolblue.nl/",
        "spacenk.com": "https://www.spacenk.com/nl/home",
        "only": "https://www.only.com/en-nl",
        "dyson": "https://www.dyson.nl/nl",
        "mimamsterdam": "https://www.mimamsterdam.com/nl/",
        "hellofresh.nl": "https://www.hellofresh.nl/",
        "charlottetilbury": "https://www.charlottetilbury.com/nl",
        "merodacosmetics": "https://merodacosmetics.nl/",
        "loopearplugs": "https://www.loopearplugs.com/?country=NL",
        "xxlnutrition": "https://xxlnutrition.com/nl",
        "footlocker": "https://www.footlocker.nl/",
        "kaartje2go": "https://www.kaartje2go.nl/",
        "sellpy": "https://www.sellpy.nl/",
        "veromoda": "https://www.veromoda.com/nl-nl",
        "hollandandbarrett": "https://www.hollandandbarrett.nl/",
        "bylashbabe": "https://bylashbabe.nl/",
        "yoursurprise": "https://www.yoursurprise.nl/",
        "parfumado": "https://parfumado.com/",
        "geurwolkje": "https://geurwolkje.nl/",
        "haarshop.nl": "https://www.haarshop.nl/",
        "cider": "https://www.shopcider.com/",
        "koreanskincare": "https://koreanskincare.nl/",
        "colourfulrebel": "https://colourfulrebel.com/",
        "kaptenandson": "https://kapten-son.com/nl",
        "parfumdreams.nl": "https://www.parfumdreams.nl/",
        "xoxowildhearts": "https://www.xoxowildhearts.com/",
        "plutosport": "https://www.plutosport.nl/",
        "zelesta.nl": "https://zelesta.nl/",
        "leolive": "https://le-olive.com/",
        "famousstore": "https://www.famous-store.nl/",
        "emmasleepnl": "https://www.emma-sleep.nl/"
    }

    store_webshops(webshops)
