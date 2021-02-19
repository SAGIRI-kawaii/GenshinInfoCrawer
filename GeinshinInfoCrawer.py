import requests
from bs4 import BeautifulSoup
import json


class GenshinInfoCrawer:

    @staticmethod
    def get_character_info():
        print("get_character_info")
        base_url = "https://bbs.mihoyo.com"
        url = "https://bbs.mihoyo.com/ys/obc/channel/map/25?bbs_presentation_style=no_header"
        data_dict = {}
        try:
            resp = requests.get(url)
            if resp.status_code != 200:
                print("response code:", resp.status_code)
                return None
        except TimeoutError:
            print("网络超时")
            return None
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")
        character_divs = soup.find("div", {"class": "channel-detail__list"})
        character_uls = character_divs.find("ul", {"class": "channel-list"})
        character_uls = character_uls.find_all("ul", {"class": "position-list__list position-list__list--avatar"})
        for ul in character_uls:
            character_li = ul.find_all("li", {"class": "position-list__item"})
            for character in character_li:

                # 基本信息部分
                character_a = character.find_all("a")[0]
                character_name = character_a["title"]
                character_url = base_url + character_a["href"]
                data_dict[character_name] = {}
                data_dict[character_name]["url"] = character_url
                print(character_name, character_url)
                if "勿过审" in character_name:
                    continue
                try:
                    character_resp = requests.get(character_url)
                    if character_resp.status_code != 200:
                        print("response code:", character_resp.status_code)
                        continue
                except TimeoutError:
                    print("网络超时")
                    continue

                character_html = character_resp.text
                character_soup = BeautifulSoup(character_html, "html.parser")
                character_div = character_soup.find("div", {"class": "detail__content"})

                # 角色展示部分
                character_show_div = character_div.find("div", {"data-part": "painting"})
                character_show_uls = character_show_div.find_all("ul")
                character_show_dict = {}
                character_show_label = character_show_uls[0].find_all("li")
                character_show_data = character_show_uls[1].find_all("li")
                if len(character_show_label) == len(character_show_data):
                    for i in range(len(character_show_label)):
                        character_show_dict[character_show_label[i].get_text().strip()] = {
                            "url": character_show_data[i].find_all("img")[0]["src"].split("?")[0]
                        }
                data_dict[character_name]["角色展示"] = character_show_dict

                # 角色主要信息部分
                character_main = character_div.find("div", {"data-part": "main"})
                character_avatar = character_main.find_all("td", {"class": "obc-tmpl-character__avatar"})[0].find("img")["src"]
                data_dict[character_name]["avatar"] = character_avatar
                character_main_trs = character_main.find_all("tr")
                character_main_info = {}
                for tr in character_main_trs:
                    tds = tr.find_all("td")
                    if len(tds) == 1:
                        character_main_info["角色介绍"] = tds[0].get_text().strip()
                        continue
                    elif len(tds) == 3:
                        character_main_info[tds[1].get_text().strip()] = tds[2].get_text().strip()
                        continue
                    character_main_info[tds[0].get_text().strip()] = tds[1].get_text().strip()
                # print(character_main_info)
                data_dict[character_name]["角色信息"] = character_main_info

                # 角色介绍部分
                character_describe = character_div.find("div", {"data-part": "describe"})
                tds = character_describe.find_all("td")
                data_dict[character_name]["角色信息"][tds[0].get_text().strip()] = tds[1].get_text().strip()
                data_dict[character_name]["角色信息"][tds[2].get_text().strip()] = tds[3].get_text().strip()
                data_dict[character_name]["角色信息"][tds[len(tds) - 2].get_text().strip()] = tds[
                    len(tds) - 1].get_text().strip()

                # cv部分
                character_cv = character_div.find("div", {"data-part": "cv"})
                ps = character_cv.find_all("p")
                character_cv_data = {}
                for p in ps:
                    cv_text = p.get_text().strip()
                    if "：" in cv_text:
                        language = cv_text.split("：")[0]
                        voice_actor_name = cv_text.split("：")[1]
                        character_cv_data[language] = {"name": voice_actor_name}
                        if a := p.find_all("a"):
                            character_cv_data[language]["cv_url"] = a[0]["href"]
                if cv_a := ps[len(ps) - 1].find_all("a"):
                    cv_detail_url = cv_a[0]["href"]
                else:
                    data_dict[character_name]["cv"] = character_cv_data
                    data_dict[character_name]["语音"] = {}
                    continue
                cv_detail_url = (base_url if "https" not in cv_detail_url else "") + cv_detail_url
                # print(cv_detail_url)
                try:
                    cv_detail_resp = requests.get(cv_detail_url)
                    if cv_detail_resp.status_code != 200:
                        print("response code:", cv_detail_resp.status_code)
                        continue
                except TimeoutError:
                    print("网络超时")
                    continue
                cv_soup = BeautifulSoup(cv_detail_resp.text, "html.parser")
                character_voice_div = cv_soup.find("div", {"class": "detail__content"})
                ps = character_voice_div.find_all("p")
                character_voices = {}
                temp_text = ""
                title_before = ""
                start = False
                count = 1
                for p in ps:
                    if (title := p.find_all("strong")) and str(count) in p.find_all("strong")[0].get_text():
                        if start:
                            character_voices[title_before] = temp_text[:-1]
                        start = True
                        title_before = title[0].get_text().strip().replace(str(count), "").replace(".", "")
                        count += 1
                        temp_text = ""
                    elif start:
                        temp_text += f"{p.get_text().strip()}\n"

                character_voices[title_before] = temp_text[:-1]
                data_dict[character_name]["cv"] = character_cv_data
                data_dict[character_name]["语音"] = character_voices

                # 基础属性部分
                character_basic_attr = character_div.find("div", {"data-part": "basicAttr"})
                basic_attr_data = {}
                trs = character_basic_attr.find_all("tr")
                for tr in trs:
                    tds = tr.find_all("td")
                    divs = tr.find_all("div")
                    basic_attr_data[tds[0].get_text().strip()] = divs[0].get_text().strip()
                data_dict[character_name]["基础属性"] = basic_attr_data

                # 角色突破部分
                character_breach = character_div.find("div", {"data-part": "breach"})
                character_breach_uls = character_breach.find_all("ul")
                character_breach_label = character_breach_uls[0].find_all("li")
                character_breach_info = character_breach_uls[1].find_all("li", {"data-target": "breach.attr"})
                breach_data = {}
                if len(character_breach_label) == len(character_breach_info):
                    for i in range(len(character_breach_label)):
                        trs = character_breach_info[i].find_all("tr")
                        breach_materials = trs[0].find_all("li", {"data-target": "breach.attr.material"})
                        materials = []
                        for breach_material in breach_materials:
                            material_temp = breach_material.get_text().strip().split("*")
                            material_data = {
                                "name": "无" if not breach_material.get_text().strip() else material_temp[0]}
                            # print(breach_material.get_text().strip())
                            quantity = int(material_temp[1]) if breach_material.get_text().strip() and material_temp[
                                1] else 0
                            material_data["quantity"] = quantity
                            if a := breach_material.find_all("a"):
                                material_data["url"] = base_url + a[0]["href"]
                                if img := a[0].find_all("img"):
                                    material_data["icon"] = img[0]["src"]
                            materials.append(material_data)

                        breach_data[character_breach_label[i].get_text().strip()] = {
                            "materials": materials
                        }

                        for j in range(1, len(trs)):
                            tds = trs[j].find_all("td")
                            count = 1
                            key = ""
                            for td in tds:
                                if count % 2 == 1:
                                    if temp_key := td.get_text().strip():
                                        breach_data[character_breach_label[i].get_text().strip()][temp_key] = ""
                                        key = temp_key
                                else:
                                    if img := td.find_all("img"):
                                        breach_data[character_breach_label[i].get_text().strip()][key] = {}
                                        breach_data[character_breach_label[i].get_text().strip()][key][
                                            "name"] = td.get_text().strip()
                                        breach_data[character_breach_label[i].get_text().strip()][key]["icon"] = img[0][
                                            "src"]
                                    else:
                                        if value := td.get_text().strip():
                                            breach_data[character_breach_label[i].get_text().strip()][key] = value
                                count += 1
                    # print(breach_data)
                data_dict[character_name]["角色突破"] = breach_data

                # 命之座部分
                character_life = character_div.find("div", {"data-part": "life"})
                trs = character_life.find_all("tr")
                character_life_info = {}
                for i in range(1, len(trs)):
                    tds = trs[i].find_all("td")
                    life_name = tds[0].get_text().strip()
                    character_life_info[life_name] = {}
                    character_life_info[life_name]["icon"] = tds[0].find_all("img")[0]["src"]
                    character_life_info[life_name]["materials"] = tds[1].get_text().strip()
                    character_life_info[life_name]["introduction"] = tds[2].get_text().strip()
                # print(character_life_info)
                data_dict[character_name]["命之座"] = character_life_info

                # 天赋部分
                character_skill = character_div.find("div", {"data-part": "skill"})
                character_skill_uls = character_skill.find_all("ul")
                character_skill_dict = {}
                character_skill_label = character_skill_uls[0].find_all("li")
                character_skill_data = character_skill_uls[1].find_all("li")
                if len(character_skill_label) == len(character_skill_data):
                    for i in range(len(character_skill_label)):
                        skill_name = character_skill_label[i].get_text().strip()
                        character_skill_dict[skill_name] = {}
                        character_skill_dict[skill_name]["name"] = ""
                        character_skill_dict[skill_name]["icon"] = ""
                        character_skill_dict[skill_name]["description"] = ""
                        character_skill_dict[skill_name]["detail"] = {}
                        if description := character_skill_data[i].find_all("pre"):
                            character_skill_dict[skill_name]["description"] = description[0].get_text().strip()

                        if h3 := character_skill_data[i].find_all("h3"):
                            character_skill_dict[skill_name]["name"] = h3[0].get_text().strip()
                            if img := h3[0].find_all("img"):
                                character_skill_dict[skill_name]["icon"] = img[0]["src"]

                        trs = character_skill_data[i].find_all("tr")[1:]
                        if len(trs) <= 1:
                            continue
                        for j in range(len(trs) - 1):
                            tds = trs[j].find_all("td")
                            for k in range(1, len(tds)):
                                if f"LV{k}" not in character_skill_dict[skill_name]["detail"]:
                                    character_skill_dict[skill_name]["detail"][f"LV{k}"] = {}
                            skill_attr = tds[0].get_text().strip()
                            for k in range(1, len(tds)):
                                character_skill_dict[skill_name]["detail"][f"LV{k}"][skill_attr] = tds[
                                    k].get_text().strip()

                        upgrade_materials_tds = trs[len(trs) - 1].find_all("td")
                        character_skill_dict[skill_name]["detail"]["升级材料"] = {}
                        for j in range(1, len(upgrade_materials_tds)):
                            temp_list = []
                            if a := upgrade_materials_tds[j].find_all("a"):
                                for material in a:
                                    if img := material.find_all("img"):
                                        temp_list.append({
                                            "name": material.get_text().strip(),
                                            "icon": img[0]["src"],
                                            "url": base_url + material["href"]
                                        })
                                    else:
                                        temp_list.append({
                                            "name": material.get_text().strip(),
                                            "url": base_url + material["href"]
                                        })
                            # print(skill_name)
                            character_skill_dict[skill_name]["detail"][f"LV{j}"]["升级材料"] = temp_list[:]
                data_dict[character_name]["天赋"] = character_skill_dict

                # 故事部分
                character_stories_name = character_div.find_all("div",
                                                                {"class": "obc-tmpl__rich-text obc-tmpl-fold__title"})
                character_stories = character_div.find_all("div",
                                                           {"class": "obc-tmpl__paragraph-box obc-tmpl__rich-text"})
                stories_data = {}
                if len(character_stories_name) == len(character_stories):
                    for i in range(len(character_stories_name)):
                        stories_data[character_stories_name[i].get_text().strip()] = character_stories[
                            i].get_text().strip()
                data_dict[character_name]["角色故事"] = stories_data

        return data_dict


print(GenshinInfoCrawer.get_character_info())