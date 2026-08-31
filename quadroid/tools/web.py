import urllib.parse
import webbrowser
import requests
from typing import Dict, Any, List


def open_url(url: str) -> Dict[str, Any]:
    """
    Open any website, video, or link in the user's default web browser.
    
    :param url: Web URL to open (e.g. 'https://youtube.com', 'https://github.com').
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        webbrowser.open(url)
        return {"success": True, "message": f"Opened {url} in browser."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def web_search(query: str) -> Dict[str, Any]:
    """
    Search the web for queries or topics and open the search results.
    
    :param query: Query string to search for on the web.
    """
    query = query.strip()
    if not query:
        return {"success": False, "error": "Query cannot be empty."}

    encoded = urllib.parse.quote_plus(query)
    search_url = f"https://www.google.com/search?q={encoded}"
    try:
        webbrowser.open(search_url)
        return {"success": True, "message": f"Searching web for '{query}'", "url": search_url}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_weather(city: str = "") -> Dict[str, Any]:
    """
    Get live weather information for any city or user's current location (Free, no API key required).
    
    :param city: City name (e.g. 'New York', 'London', 'Tokyo') or leave blank for local weather.
    """
    city_clean = city.strip().replace(" ", "+")
    try:
        # Use wttr.in format=j1 for clean JSON
        url = f"https://wttr.in/{city_clean}?format=j1" if city_clean else "https://wttr.in/?format=j1"
        response = requests.get(url, timeout=5, headers={"User-Agent": "curl/7.68.0"})
        if response.status_code == 200:
            data = response.json()
            current = data.get("current_condition", [{}])[0]
            temp_c = current.get("temp_C", "N/A")
            temp_f = current.get("temp_F", "N/A")
            desc = current.get("weatherDesc", [{}])[0].get("value", "N/A")
            humidity = current.get("humidity", "N/A")
            wind = current.get("windspeedKmph", "N/A")
            loc_area = data.get("nearest_area", [{}])[0].get("areaName", [{}])[0].get("value", city or "Current Location")
            
            summary = f"Weather in {loc_area}: {temp_c}°C ({temp_f}°F), {desc}. Humidity: {humidity}%, Wind: {wind} km/h."
            return {
                "success": True,
                "location": loc_area,
                "temp_c": temp_c,
                "temp_f": temp_f,
                "condition": desc,
                "humidity": humidity,
                "wind_speed_kmph": wind,
                "summary": summary
            }
    except Exception as e:
        # Fallback to opening browser weather
        if city_clean:
            webbrowser.open(f"https://www.google.com/search?q=weather+{city_clean}")
        return {"success": False, "error": f"Could not fetch weather: {str(e)}"}


def get_latest_news(topic: str = "technology") -> Dict[str, Any]:
    """
    Fetch the latest news headlines on a topic.
    
    :param topic: News category/topic (e.g. 'technology', 'world', 'business', 'science').
    """
    topic_clean = topic.strip()
    try:
        # Fetch RSS news feed parsed safely
        rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote_plus(topic_clean)}&hl=en-US&gl=US&ceid=US:en"
        import xml.etree.ElementTree as ET
        resp = requests.get(rss_url, timeout=5)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            items = root.findall(".//item")[:5]
            headlines = []
            for item in items:
                title = item.find("title")
                if title is not None and title.text:
                    headlines.append(title.text)
            
            return {
                "success": True,
                "topic": topic_clean,
                "headlines": headlines,
                "summary": f"Latest headlines on {topic_clean}:\n" + "\n".join(f"- {h}" for h in headlines)
            }
    except Exception as e:
        webbrowser.open(f"https://news.google.com/search?q={urllib.parse.quote_plus(topic_clean)}")
        return {"success": False, "error": f"Could not parse news: {str(e)}"}
