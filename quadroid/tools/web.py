"""
Quadroid Web Tools — Browser automation, web searching, email composing, weather, and news.
"""
import urllib.parse
import webbrowser
import requests
from typing import Dict, Any, List


def open_url(url: str) -> Dict[str, Any]:
    """
    Open any website, video, or link in the user's default web browser (e.g. Google Chrome, Edge).
    
    :param url: Web URL or domain to open (e.g. 'https://github.com', 'youtube.com', 'mail.google.com').
    """
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        webbrowser.open(url)
        return {"success": True, "message": f"Opened {url} in web browser."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def web_search(query: str, engine: str = "google") -> Dict[str, Any]:
    """
    Search the web for queries, topics, or sites and open the search results in the browser.
    
    :param query: Query string to search for on the web (e.g. 'GitHub', 'Python tutorials', 'latest movies').
    :param engine: Search engine ('google', 'bing', 'duckduckgo', 'youtube', 'github').
    """
    query = query.strip()
    if not query:
        return {"success": False, "error": "Query cannot be empty."}

    encoded = urllib.parse.quote_plus(query)
    
    engine_urls = {
        "google": f"https://www.google.com/search?q={encoded}",
        "github": f"https://github.com/search?q={encoded}",
        "youtube": f"https://www.youtube.com/results?search_query={encoded}",
        "bing": f"https://www.bing.com/search?q={encoded}",
        "duckduckgo": f"https://duckduckgo.com/?q={encoded}"
    }
    
    search_url = engine_urls.get(engine.lower(), engine_urls["google"])
    
    try:
        webbrowser.open(search_url)
        return {"success": True, "message": f"Searching for '{query}' on {engine.title()}.", "url": search_url}
    except Exception as e:
        return {"success": False, "error": str(e)}


def compose_email(to: str = "", subject: str = "", body: str = "") -> Dict[str, Any]:
    """
    Open Gmail or default email client with a pre-filled draft to compose an email.
    
    :param to: Recipient email address (e.g. 'friend@example.com').
    :param subject: Email subject line.
    :param body: Email message body content.
    """
    encoded_to = urllib.parse.quote(to.strip())
    encoded_su = urllib.parse.quote(subject.strip())
    encoded_body = urllib.parse.quote(body.strip())
    
    # Direct Gmail Web Compose URL
    gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={encoded_to}&su={encoded_su}&body={encoded_body}"
    
    try:
        webbrowser.open(gmail_url)
        return {
            "success": True,
            "message": f"Opened Gmail draft to '{to or 'new recipient'}' with subject '{subject or 'No subject'}'.",
            "url": gmail_url
        }
    except Exception as e:
        # Fallback to mailto protocol
        mailto_url = f"mailto:{encoded_to}?subject={encoded_su}&body={encoded_body}"
        try:
            webbrowser.open(mailto_url)
            return {"success": True, "message": "Opened default email client compose window."}
        except Exception as e2:
            return {"success": False, "error": f"Failed to open email composer: {str(e2)}"}


def get_weather(city: str = "") -> Dict[str, Any]:
    """
    Get live weather information for any city or user's current location.
    
    :param city: City name (e.g. 'New York', 'London', 'Tokyo') or leave blank for local weather.
    """
    city_clean = city.strip().replace(" ", "+")
    try:
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
