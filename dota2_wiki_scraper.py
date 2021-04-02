import requests
from bs4 import BeautifulSoup
import codecs
import re
import json
import html

def get_hero(hero_name):
    url_hero_name = '_'.join(hero_name.split(' '))
    URL = 'https://dota2.gamepedia.com/' + url_hero_name
    page = str(requests.get(URL).text)
    page = bs_preprocess(page)
    f = open('./heroes/' + url_hero_name + '.html', 'w')
    f.write(page)
    
    # page = codecs.open("abilities.html", 'r').read()
    soup = BeautifulSoup(page, 'html.parser')

    hero = {}
    hero['abilities'] = []

    abilities = soup.find_all(class_='ability-background')
    for ability in abilities:
        ability_data = get_ability(ability)
        hero['abilities'].append(ability_data)

    talents = soup.find(id='Talents').parent.next_sibling.table
    hero['talents'] = get_talents(talents)
    hero['base_stats'] = get_base_stats(soup)
    return hero
        
def get_ability(soup):
    ability_data = {}

    ability = soup.div

    # Top bar of ability
    top_bar = ability.div
    top_bar.div.decompose()
    ability_data['ability_name'] = top_bar.get_text().strip()

    # Ability Info
    ability_info = top_bar.next_sibling
    ability_data['ability_image_url'] = re.sub(r'/revision.*', '', ability_info.contents[0].a.img['src'])
    info = {}
    try:
        ability_info.contents[1].div.contents[0].b.decompose()
    except:
        pass
    info['target'] = ability_info.contents[1].div.contents[0].get_text()
    try:
        ability_info.contents[1].div.contents[1].b.decompose()
    except:
        pass
    info['affects'] = ability_info.contents[1].div.contents[1].get_text()
    try:
        ability_info.contents[1].div.contents[2].b.decompose()
    except:
        pass
    info['damage_type'] = ability_info.contents[1].div.contents[2].get_text()
    info['description'] = ability_info.contents[1].contents[1].get_text()
    ability_data['ability_info'] = info
    
    # Ability Numbers
    ability_numbers = ability_info.next_sibling
    numbers = []
    for element in ability_numbers.contents:
        try:
            if element.contents[0].name == 'b' and element.b.span == None:
                line = {}
                if element.span.a != None:
                    line["modifiers"] = {
                        "type": element.span.a["title"],
                        "value": element.span.span.get_text()
                    }
                    element.span.a.decompose()
                    element.span.span.decompose()
                line["title"] = element.b.get_text()
                line["value"] = element.span.get_text().replace('(', '').replace(')', '').strip()
                numbers.append(line)
                # print(numbers[-1])
        except:
            pass

        # Cooldowns
        try:
            cooldown_element = element.find("a", { "title": "Cooldown" }).parent.parent
        except:
            cooldown_element = None
            pass
        if cooldown_element != None:
            cooldown = {}
            modifier_element = cooldown_element.contents[-1]
            if modifier_element.name == 'span':
                cooldown["modifiers"] = {
                    "type": modifier_element.a["title"],
                    "value": modifier_element.get_text().replace('(', '').replace(')', '').strip()
                }
                modifier_element.decompose()
            cooldown["title"] = "Cooldown"
            cooldown["value"] = cooldown_element.get_text()
            numbers.append(cooldown)  
            # print(numbers[-1])

        # Mana Cost
        try:
            manacost_element = element.find("a", { "title": "Mana" }).parent.parent
        except:
            manacost_element = None
            pass
        if manacost_element != None:
            manacost = {}
            modifier_element = manacost_element.contents[-1]
            if modifier_element.name == 'span':
                manacost["modifiers"] = {
                    "type": modifier_element.a["title"],
                    "value": modifier_element.get_text().replace('(', '').replace(')', '').strip()
                }
                modifier_element.decompose()
            manacost["title"] = "Manacost"
            manacost["value"] = manacost_element.get_text()
            numbers.append(manacost)  
            # print(numbers[-1])
    ability_data['ability_numbers'] = numbers

    return ability_data

def get_talents(soup):
    talents = {}
    table_rows = soup.find_all('tr')
    for index, row in enumerate(table_rows, start=0):
        if index != 0:
            left_talent = ''
            for element in row.contents[0]:
                try:
                    left_talent += ' ' + element.get_text()
                except:
                    left_talent += ' ' + element  
            right_talent = ''
            for element in row.contents[2]:
                try:
                    right_talent += ' ' + element.get_text()
                except:
                    right_talent += ' ' + element
            talents[row.th.get_text()] = {
                'left_talent': left_talent.strip(),
                'right_talent': right_talent.strip()
            }
    return talents

def get_base_stats(soup):
    base_stats = {}
    stats = soup.find(id='primaryAttribute').parent
    base_stats['strength'] = {
        'base': stats.contents[3].b.text,
        'additional_per_level': stats.contents[3].b.next_sibling
    }
    base_stats['agility'] = {
        'base': stats.contents[4].b.text,
        'additional_per_level': stats.contents[4].b.next_sibling
    }
    base_stats['intelligence'] = {
        'base': stats.contents[5].b.text,
        'additional_per_level': stats.contents[5].b.next_sibling
    }
    base_stats['attack'] = soup.find(class_="evenrowsgray").tbody.contents[-1].contents[2].text
    base_stats['attack_range'] = soup.find(class_="oddrowsgray").tbody.contents[5].contents[1].get_text()
    base_stats['attack_time'] = soup.find(class_="oddrowsgray").tbody.contents[8].contents[1].get_text()
    return base_stats
    
def get_items():
    print('Getting Items')
    # URL = 'https://dota2.gamepedia.com/Items'
    # page = str(requests.get(URL).text)
    page = open('items.html', 'r').read()

    # with open('items.html', 'w') as f:
    #     f.write(page)

    page = bs_preprocess(page)
    
    soup = BeautifulSoup(page, 'html.parser')
    current_element = soup.find(id='Items').parent.next_sibling

    all_items = {}

    while current_element.name != 'h2':
        try:
            if current_element['class'] == ['itemlist']:
                for section_item in current_element.contents:
                    item_name = re.sub(r'\(\d*\)', '', section_item.get_text())
                    try:
                        all_items[item_name] = get_item(section_item.a['href'])
                    except Exception as e2:
                        print(e2)
                    print('Retrieved Item: ' + item_name)
        except Exception as e:
            pass
        current_element = current_element.next_sibling
    return all_items

def get_item(href):
    print('\tGetting Item: ' + href)
    URL = 'https://dota2.gamepedia.com' + href
    page = str(requests.get(URL).text)

    # with open('greaves.html', 'w') as f:
        # f.write(page)
    # page = open('greaves.html', 'r').read()

    page = bs_preprocess(page)
    
    soup = BeautifulSoup(page, 'html.parser')
    itembox = soup.find(class_='infobox').tbody

    item = {}
    itembox.tr.div.decompose()
    item['item_name'] = itembox.tr.get_text()
    item['image_src'] = re.sub(r'/revision.*', '', itembox.find(id='itemmainimage').a.img['src'])
    if itembox.find(id='itemsmallimages') == None:
        item['item_cost'] = re.sub(r' \(\d*\)', '', itembox.contents[3].th.div.div.br.next_sibling)
    else:
        item['item_cost'] = re.sub(r' \(\d*\)', '', itembox.contents[4].th.div.div.br.next_sibling)
    try:
        item_details = itembox.contents[-1].td.table.tbody
        for row in item_details.contents:
            try:
                if re.sub(r'\[\?\]', '', row.th.text) == 'Active':
                    item['active'] = { 'name': row.td.a.text }
                if re.sub(r'\[\?\]', '', row.th.text) == 'Passive':
                    item['passive'] = { 'name': row.td.a.text }
                if re.sub(r'\[\?\]', '', row.th.text) == 'Bonus':
                    bonus = ''
                    bonuses = []
                    for element in row.td.contents:
                        try:
                            if element.name != 'br':
                                bonus += ' ' + element.text
                            else:
                                bonuses.append(bonus.strip())
                                bonus = ''
                        except:
                            bonus += ' ' + element
                    item['bonuses'] = bonuses
            except:
                pass
        item_components = item_details.contents[-1].td.contents[-1].div
        components = []
        for component in item_components:
            components.append({
                'name': re.sub(r' \(\d*\)', '', component.a['title']),
                'image_src': re.sub(r'/revision.*', '', component.a.img['src'])
            })
        item['components'] = components
    except:
        pass

    soup.find_all(class_='ability-background')
    for ability in soup.find_all(class_='ability-background'):
        try:
            ability.div.div.div.decompose()
        except:
            pass
        if 'active' in item and item['active']['name'] == ability.div.div.text:
            item['active']['effect'] = ability.find(class_='ability-description adItemOrRune').contents[1].get_text()
            active_notes = []
            for row in ability.find(class_='ability-head').next_sibling:
                if len(row.attrs) == 0:
                    active_notes.append({
                        'title': row.b.text,
                        'value': row.contents[-1].text
                    })
                active_cooldown = row.find(title='Cooldown')
                if active_cooldown != None:
                    item['active']['cooldown'] = active_cooldown.parent.next_sibling
            item['active']['notes'] = active_notes
        if 'passive' in item and item['passive']['name'] == ability.div.div.text:
            item['passive']['effect'] = ability.find(class_='ability-description adItemOrRune').contents[1].get_text()
            passive_notes = []
            for row in ability.find(class_='ability-head').next_sibling:
                if len(row.attrs) == 0:
                    passive_notes.append({
                        'title': row.b.text,
                        'value': row.contents[-1].text
                    })
                passive_cooldown = row.find(title='Cooldown')
                if passive_cooldown != None:
                    item['passive']['cooldown'] = passive_cooldown.parent.next_sibling
            item['passive']['notes'] = passive_notes

    return item

""" Thanks to https://stackoverflow.com/questions/23241641/how-to-ignore-empty-lines-while-using-next-sibling-in-beautifulsoup4-in-python """
def bs_preprocess(html):
    """remove distracting whitespaces and newline characters"""
    pat = re.compile('(^[\s]+)|([\s]+$)', re.MULTILINE)
    html = re.sub(pat, '', html)       # remove leading and trailing whitespaces
    html = re.sub('\n', ' ', html)     # convert newlines to spaces
                                    # this preserves newline delimiters
    html = re.sub('[\s]+<', '<', html) # remove whitespaces before opening tags
    html = re.sub('>[\s]+', '>', html) # remove whitespaces after closing tags
    return html 

def main():
    heroes = {}
    with open('heroes.json', 'r') as json_file:
        heroes_to_get = json.load(json_file)
        for hero_to_get in heroes_to_get['heroes']:
            hero_name = hero_to_get['localized_name']
            print("Retrieving Hero: " + hero_name)
            hero = get_hero(hero_name)
            heroes[hero_to_get['id']] = {
                "name": hero_to_get['name'],
                "heroId": hero_to_get['id'],
                "display_name": hero_to_get['localized_name'],
                "data": hero
            }
    with open('heroes_data.json', 'w') as outfile:
        json.dump(heroes, outfile)
    items = get_items()
    with open('items_data.json', 'w') as outfile:
        json.dump(items, outfile)

if __name__ == "__main__":
    main()