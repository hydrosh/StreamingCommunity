# 02.12.24

from datetime import datetime
from typing import List, Dict

# External
import httpx

# Util
from StreamingCommunity.Util.headers import get_headers
from StreamingCommunity.Util.console import console, msg
from StreamingCommunity.Util._jsonConfig import config_manager

# Internal
from StreamingCommunity.Api.Site.streamingcommunity.costant import SITE_NAME
from StreamingCommunity.Api.Site.streamingcommunity.site import get_version_and_domain

# Variable
max_timeout = 10

def search_titles(title_search: str, domain: str) -> List[Dict]:
    """
    Searches for content using an API based on a title and domain.

    Args:
        title_search (str): The title to search for.
        domain (str): The domain of the API site to query.

    Returns:
        List[Dict[str, str | int]]: A list of dictionaries containing information about the found content.
    """
    titles = []

    try:
        # Se la ricerca è vuota, usa un carattere jolly
        search_query = title_search.replace(' ', '+') if title_search else '*'
        url = f"https://{SITE_NAME}.{domain}/api/search?q={search_query}"
        console.print(f"[blue]Searching at URL: {url}")

        response = httpx.get(
            url=url,
            headers={'user-agent': get_headers()},
            timeout=max_timeout
        )

        response.raise_for_status()
        
        # Log response status and content for debugging
        console.print(f"[blue]Response status: {response.status_code}")
        console.print(f"[blue]Response content: {response.text[:200]}...")  # Print first 200 chars
        
        # Parse JSON response
        data = response.json()
        
        if not isinstance(data, dict) or 'data' not in data:
            console.print("[red]Invalid response format")
            return []

        for dict_title in data.get('data', []):
            if dict_title.get('last_air_date'):
                release_year = datetime.strptime(dict_title['last_air_date'], '%Y-%m-%d').year
            else:
                release_year = ''

            images = {}
            for dict_image in dict_title.get('images', []):
                images[dict_image.get('type')] = f"https://cdn.{SITE_NAME}.{domain}/images/{dict_image.get('filename')}"
        
            titles.append({
                'id': dict_title.get("id", ""),
                'slug': dict_title.get("slug", ""),
                'name': dict_title.get("name", ""),
                'type': dict_title.get("type", ""),
                'seasons_count': dict_title.get("seasons_count", 0),
                'year': release_year,
                'images': images,
                'url': f"https://{SITE_NAME}.{domain}/titles/{dict_title.get('id')}-{dict_title.get('slug')}"
            })

    except httpx.HTTPError as e:
        console.print(f"[red]HTTP Error: {str(e)}")
        return []
    except json.JSONDecodeError as e:
        console.print(f"[red]JSON Decode Error: {str(e)}")
        console.print(f"[red]Response content: {response.text[:200]}...")
        return []
    except Exception as e:
        console.print(f"[red]Unexpected Error: {str(e)}")
        return []

    return titles

def get_infoSelectTitle(url_title: str, domain: str, version: str):
    console.print(f"[blue]Getting info for URL: {url_title}")

    try:
        headers = {
            'user-agent': get_headers(),
            'x-inertia': 'true',
            'x-inertia-version': version,
            'x-requested-with': 'XMLHttpRequest',
            'x-inertia-partial-component': 'Title',
            'x-inertia-partial-data': 'title,genres,loadedSeason',
            'accept': 'application/json',
            'referer': f'https://streamingcommunity.{domain}'
        }

        # Assicurati che l'URL sia completo
        if not url_title.startswith('http'):
            url_title = f"https://streamingcommunity.{domain}/titles/{url_title}"

        # Assicurati che l'URL non contenga /watch
        if url_title.endswith('/watch'):
            url_title = url_title[:-6]

        console.print(f"[blue]Making request to: {url_title}")
        response = httpx.get(url_title, headers=headers, timeout=10)
        console.print(f"[blue]Response status: {response.status_code}")
        console.print(f"[blue]Response headers: {response.headers}")
        console.print(f"[blue]Response content: {response.text[:500]}...")

        # Se la risposta non è 200, prova a seguire eventuali reindirizzamenti
        if response.status_code in [301, 302, 307, 308]:
            redirect_url = response.headers.get('location')
            if redirect_url:
                console.print(f"[blue]Following redirect to: {redirect_url}")
                response = httpx.get(redirect_url, headers=headers, timeout=10)

        response.raise_for_status()

        try:
            data = response.json()
        except json.JSONDecodeError:
            console.print("[red]Failed to decode JSON response")
            console.print(f"[red]Raw response: {response.text[:500]}")
            return None

        if 'props' not in data:
            console.print("[red]Invalid response format: missing 'props' key")
            console.print(f"[red]Response data: {data}")
            return None

        json_response = data['props']
        console.print(f"[blue]Props content: {json_response}")

        if 'title' not in json_response:
            console.print("[red]Invalid response format: missing 'title' key in props")
            return None

        generes = []
        for g in json_response.get("genres", []):
            generes.append(g.get("name", ""))
        
        trailer = None
        if json_response.get('title', {}).get('trailers', []):
            trailer = f"https://www.youtube.com/watch?v={json_response['title']['trailers'][0]['youtube_id']}"

        images = {}
        for dict_image in json_response.get('title', {}).get('images', []):
            images[dict_image.get('type')] = f"https://cdn.{SITE_NAME}.{domain}/images/{dict_image.get('filename')}"

        title_data = json_response.get('title', {})
        rsp = {
            'id': title_data.get('id'),
            'name': title_data.get('name'),
            'slug': title_data.get('slug'),
            'plot': title_data.get('plot'),
            'type': title_data.get('type'),
            'season_count': title_data.get('seasons_count'),
            'generes': generes,
            'trailer': trailer,
            'image': images
        }

        if title_data.get('type') == 'tv' and 'loadedSeason' in json_response:
            season = json_response["loadedSeason"].get("episodes", [])
            episodes = []

            for e in season:
                if e.get('images'):
                    image_url = f"https://cdn.{SITE_NAME}.{domain}/images/{e['images'][0]['filename']}"
                else:
                    image_url = None

                episode = {
                    "id": e.get("id"),
                    "number": e.get("number"),
                    "name": e.get("name"),
                    "plot": e.get("plot"),
                    "duration": e.get("duration"),
                    "image": image_url
                }
                episodes.append(episode)

            rsp["episodes"] = episodes

        return rsp
        
    except httpx.UnsupportedProtocol as e:
        console.print(f"[red]Protocol Error: {str(e)}")
        return None
    except httpx.HTTPError as e:
        console.print(f"[red]HTTP Error: {str(e)}")
        if hasattr(e, 'response'):
            console.print(f"[red]Response status: {e.response.status_code}")
            console.print(f"[red]Response content: {e.response.text[:500]}")
        return None
    except Exception as e:
        console.print(f"[red]Unexpected Error: {str(e)}")
        return None

def get_infoSelectSeason(url_title: str, number_season: int, domain: str, version: str):

    headers = {
        'user-agent': get_headers(),
        'x-inertia': 'true',
        'x-inertia-version': version
    }

    response = httpx.get(f"{url_title}/stagione-{number_season}", headers=headers, timeout=10)

    json_response = response.json().get('props').get('loadedSeason').get('episodes')
    json_episodes = []

    for json_ep in json_response:
        
        json_episodes.append({
            'id': json_ep.get('id'),
            'number': json_ep.get('number'),
            'name': json_ep.get('name'),
            'plot': json_ep.get('plot'),
            'image': f"https://cdn.{SITE_NAME}.{domain}/images/{json_ep.get('images')[0]['filename']}"
        })

    return json_episodes
