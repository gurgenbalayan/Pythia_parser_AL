import aiohttp
from bs4 import BeautifulSoup
from utils.logger import setup_logger
import os


STATE = os.getenv("STATE")
logger = setup_logger("scraper")



async def fetch_company_details(url: str) -> dict:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
                return await parse_html_details(html)
    except Exception as e:
        logger.error(f"Error fetching data for query '{url}': {e}")
        return {}
async def fetch_company_data(query: str) -> list[dict]:
    url = "https://arc-sos.state.al.us/cgi/corpname.mbr/output"
    payload = f'search={query}&type=ALL&place=ALL&city=&stat=ALL'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, data=payload) as response:
                response.raise_for_status()
                html = await response.text()
                return await parse_html_search(html)
    except Exception as e:
        logger.error(f"Error fetching data for query '{query}': {e}")
        return []

async def parse_html_search(html: str) -> list[dict]:
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    table = soup.find('table')
    if not table:
        return results
    rows = table.find_all('tr')
    for row in rows[1:]:
        cols = row.find_all('td')
        if len(cols) == 5:
            entity_id_link = cols[0].find('a')
            entity_name_link = cols[1].find('a')

            entity_id = entity_id_link.text
            entity_id_url = entity_id_link['href'] if entity_id_link and 'href' in entity_id_link.attrs else None
            entity_name = entity_name_link.text
            status = cols[4].text

            results.append({
                "state": STATE,
                'name': entity_name,
                'status': status,
                'id': entity_id,
                'url': 'https://arc-sos.state.al.us' + entity_id_url
            })

    return results


async def parse_html_details(html: str) -> dict:
    soup = BeautifulSoup(html, 'html.parser')

    async def get_value(label):
        row = soup.find('td', string=lambda t: t and label in t)
        if row:
            value_td = row.find_next_sibling('td', class_='aiSosDetailValue')
            if value_td:
                return value_td.get_text(separator=' ', strip=True)
        return None

    name = soup.select_one('.aiSosDetailHead')
    name = name.get_text(strip=True) if name else None

    registration_number = await get_value('Entity ID Number')
    status = await get_value('Status')
    date_registered = await get_value('Formation Date')
    entity_type = await get_value('Entity Type')
    agent_name = await get_value('Registered Agent Name')
    principal_address = await get_value('Principal Address')
    mailing_address = await get_value('Principal Mailing Address')

    # Documents
    document_images = []

    return {
        "state": STATE,
        "name": name,
        "status": status,
        "registration_number": registration_number,
        "date_registered": date_registered,
        "entity_type": entity_type,
        "agent_name": agent_name,
        "principal_address": principal_address,
        "mailing_address": mailing_address,
        "document_images": document_images
    }