import mysql.connector
import json

def fetch_webshop_urls():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="webshops"
        )
        cursor = connection.cursor()
        cursor.execute("SELECT webshop_url FROM webshop_info")
        urls = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        return urls

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return []

def print_apify_format(urls):
    apify_input = [{"url": url, "method": "GET"} for url in urls]
    print(json.dumps(apify_input, indent=4))

if __name__ == "__main__":
    urls = fetch_webshop_urls()
    if urls:
        print_apify_format(urls)
    else:
        print("No URLs found.")
