#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
League of Legends random champion picker for ranked play.
Created on Thu Oct 18 18:19:06 2018 by Tanyu Tanev <ttanev34@gmail.com>
"""

# Libraries needed to extract information from OP.GG
import requests
import bs4

import sys
import random

# Libraries needed to manipulate the configuration file.
import os
import configparser
import json
config_file = "cfg.ini"


def get_champions_from_site(role):
    """
    Get champions for given role from OP.GG. Additional filters are
    choosable in the beginning, which determine how "meta" the fetched
    champions will be.

    Args:
        role (str) - the champions for which role have to be fetched

    Returns:
        result (list) - list of champions in the respective role, optionally
                        filtered by how the user wants to play.

    """
    result = []
    # OP.GG classifies champions by tiers.
    appropriate_tiers = []
    mode = input("How do you feel like playing?\n" +
                 "1) Tryhard\n" +
                 "2) Not too troll\n" +
                 "3) Feed my ass off\n" +
                 "4) Just hit me with something, fam\n").upper()
    counter = 1
    while True:
        if (mode == "TRYHARD" or mode == "1" or mode == "1)"):
            appropriate_tiers.extend(["OP", "1"])
            break
        elif (mode == "NOT TOO TROLL" or mode == "2" or mode == "2)"):
            appropriate_tiers.extend(["2", "3"])
            break
        elif (mode == "FEED MY ASS OFF" or mode == "3" or mode == "3)"):
            appropriate_tiers.extend(["4", "5"])
            break
        elif (mode == "JUST HIT ME WITH SOMETHING, FAM" or mode == "4"
              or mode == "4)"):
            appropriate_tiers.extend(["OP", "1", "2", "3", "4", "5"])
            break
        else:
            # Exit program, if input is invalid 3 times in a row.
            if (counter > 2):
                print("\nYou're trolling again")
                sys.exit(1)
            counter += 1

    # Fetch contents of main champions webpage.
    r = requests.get("https://euw.op.gg/champion/statistics")
    # Represent document as nested data structure with help of Beautiful Soup.
    soup = bs4.BeautifulSoup(r.text, "lxml")
    # Find the specific part of the HTML page, which represents
    # how strong champions are in a certain role. (This corresponds
    # to the right part of the webpage, under "Champion Rankings")
    tbody = soup.find("tbody", {"class":
                                "champion-trend-tier-" + role})
    # The contents of tbody are in the form of
    # <tr>...</tr>
    # <tr>...</tr>
    #      .
    #      .
    #      .
    # ,where each component contains meta information about a certain champion
    # in that role.
    for tr in tbody.contents:
        # Somehow some contents + first and last one (always!) are blank lines.
        # Skip them.
        if (tr == "\n"):
            continue
        # Explanation:
        # tr.contents[-2].contents[1] point to an <img /> component. The image
        # determines what tier the champion is, according to OP.GG. If the
        # tier of the champion is as wanted, the program goes on to extract
        # the name of the champion from a <td> component, which contains it.
        for tier in appropriate_tiers:
            if (tr.contents[-2].contents[1]["src"].endswith(tier + ".png")):
                result.append(tr.contents[7].contents[1].contents[1].string)
    return result


def get_unowned_champions(champions):
    """
    Construct a list of unowned champions from those given.

    Args:
        champions (list) - a list of champions

    Returns:
        res (list) - a list of unowned champions from those given

    """
    res = []
    print("\nPlease indicate, if you don't own any champions\n" +
          "or press Enter, if all champions are owned: ")
    champion_id = 1
    for champion in champions:
        print("%d. %s" % (champion_id, champion))
        champion_id += 1
    unowned_input = input("Format [x-y],z,..., where [x-y] is a range" +
                          "and\nz is a single number next to " +
                          "a champion: ").split(',')
    indeces = construct_list(unowned_input)
    for index in indeces:
        res.append(champions[index])
    return res


def write_in_configuration_file(config_file, section, option, value):
    """
    Write given option and value in given section
    in configuration file. (Without clearing file)

    NOTE: Config (Instance of ConfigParser) is globally defined.

    Args:
        config_file (str)
        section (str) - how in what section should the option/value pair be
                        written
        option (str)
        value (str)
    """
    cfgfile = open(config_file, 'a')
    Config.add_section(section)
    Config.set(section, option, json.dumps(value))
    Config.write(cfgfile)
    cfgfile.close()


def modify_past_configuration(past_conf):
    """
    Modify past_configuration in-place.

    Args:
        past_conf (list) - past configuration of unowned champions

    """
    print("\nPlease indicate what new champions were bought: ")
    champion_id = 1
    for champion in past_conf:
        print(str(champion_id) + ". " + champion)
        champion_id += 1
    new_champions_input = input("Format [x-y],z,..., where [x-y] is a" +
                                "range and\nz is a single number next " +
                                "to a champion: ").split(',')
    indeces = construct_list(new_champions_input)
    for index in sorted(indeces, reverse=True):
        past_conf.pop(index)


def construct_list(ls):
    """
    Construct a list of integers/strings from a list in the form of
        [[x-y], z, w, ...], with [x-y] - range from x to y
                                 z, w  - single values

    NOTE: Appended values are -1, because data structures are 0-based.

    Args:
        ls (list) - list in the form shown above

    Returns
        res (list) - list in proper form
    """
    res = []
    # If input isn't [''] ...
    if ls[0]:
        for value in ls:
            # If value is a range [x-y], append all numbers between x and y.
            if (value.startswith("[")):
                tmp = value.split('-')
                start = int(tmp[0][1:])
                end = int(tmp[1][:-1])
                for i in range(start, end + 1):
                    res.append(i - 1)
            # If value is single number, append it.
            else:
                res.append(int(value) - 1)
    return res


def remove_unowned_champions(champions, unowned_champions):
    """
    Removed the unowned champions from the pool of available ones.
    Copied and used from:
    https://goo.gl/Db6ea8 (Mark Byers)

    Args:
        champions (list) - list of possible champions
        unowned_champions (list) - list of unowned champions from the possible

    Returns:
        (list) - list of available champions to pick

    """
    s = set(unowned_champions)
    return [x for x in champions if x not in s]


def write_in_stats(champion):
    """
    Check if champion has been picked randomly before. If he has
    increment the pick count by 1. If not, create an option after him
    under the section "Stats".

    Args:
        champion (str) - the champion, which was randomly picked

    """
    # Create Stats section, if not already in config file.
    if ("Stats" not in sections):
        Config.add_section("Stats")

    # Get all champions, which were picked until now.
    all_values = dict(Config.items("Stats"))
    # Check if latest champion is among them. (Options are always lowercase)
    if (champion.lower() in all_values):
        old_count = Config.get("Stats", champion)
        new_count = str(int(old_count) + 1)
        with open(config_file, "w") as f:
            Config.set("Stats", champion, new_count)
            Config.write(f)
    else:
        with open(config_file, "w") as f:
            Config.set("Stats", champion, "1")
            Config.write(f)


if __name__ == "__main__":
    # If there is no configuration file on hand, create it.
    if not os.path.isfile(config_file):
        with open(config_file, 'a'):
            os.utime(config_file, None)

    Config = configparser.ConfigParser()
    Config.read(config_file)
    sections = Config.sections()

    while True:
        # What does the user want to do?
        function = input("Welcome to LoL random champion picker!" +
                         "Please select what you want to do:\n" +
                         "1) Pick a random champion\n" +
                         "2) See stats about picked champions\n" +
                         "3) Exit program\n")
        if (function == "Pick a random champion"
            or function == "1" or function == "1)"):  # noqa: E129
            champions = []
            counter = 1
            role = ""
            while True:
                role = input("Please type what role you're going to play:\n" +
                             "1) Top\n" +
                             "2) Jungle\n" +
                             "3) Mid\n" +
                             "4) ADC\n" +
                             "5) Support\n").upper()
                if (role == "TOP" or role == "1" or role == "1)"):
                    role = "Top"
                    champions = get_champions_from_site(role.upper())
                    break
                elif (role == "JUNGLE" or role == "2" or role == "2)"):
                    role = "Jungle"
                    champions = get_champions_from_site(role.upper())
                    break
                elif (role == "MID" or role == "3" or role == "3)"):
                    role = "Mid"
                    champions = get_champions_from_site(role.upper())
                    break
                elif (role == "ADC" or role == "4" or role == "4)"):
                    role = "ADC"
                    champions = get_champions_from_site(role.upper())
                    break
                elif (role == "SUPPORT" or role == "5" or role == "5)"):
                    role = "Support"
                    champions = get_champions_from_site(role.upper())
                    break
                else:
                    # Exit program, if input is invalid 3 times in a row.
                    if (counter > 2):
                        print("\nYou're trolling")
                        sys.exit(1)
                    counter += 1

            # The following list is used later, when the user
            # has select his unowned champions.
            unowned_champions = []
            # This boolean keeps track of whether or not something needs to be
            # written in the configuration file.
            write_in_role = False

            # This option is in a variable, so that it can be modified if
            # the user modifies the configuration. (option 4)
            first_option = "1) Use past configuration\n"
            # Has the user already given which champions he doesnt own?
            if (role in sections):
                counter = 1
                while True:
                    ans = input("Detected past configuration of unowned" +
                                "champions.\n" +
                                first_option +
                                "2) Reset configuration of role\n" +
                                "3) Show configuartion\n" +
                                "4) Remove champion (Bought him)\n")

                    if (ans == "Use past configuration"
                        or ans == "1" or ans == "1)"):  # noqa: E129
                        # Load unowned champions from configuration file.
                        unowned_champions = json.loads(
                                Config.get(role, "Unowned"))
                        break

                    elif (ans == "Reset configuration of role"
                          or ans == "2" or ans == "2)"):
                        # Remove previous configuration.
                        Config.remove_section(role)
                        with open(config_file, "w") as f:
                            Config.write(f)

                        # Set up new one.
                        unowned_champions = get_unowned_champions(champions)
                        write_in_role = True
                        break

                    elif (ans == "Show configuration"
                          or ans == "3" or ans == "3)"):
                        past_conf = json.loads(Config.get(role, "Unowned"))
                        for champion in past_conf:
                            print(champion)
                        continue

                    elif (ans == "Remove champion (Bought him)"
                          or ans == "4" or ans == "4)"):
                        # Get the past configuration and modify it.
                        past_conf = json.loads(Config.get(role, "Unowned"))
                        modify_past_configuration(past_conf)
                        # Rewrite configuration file.
                        with open(config_file, "w") as f:
                            Config.set(role, "Unowned", json.dumps(past_conf))
                            Config.write(f)
                        first_option = "1) Use new configuration\n"
                    # Exit program, if input is invalid 3 times in a row.
                    else:
                        if (counter > 2):
                            print("\nYou're trolling again")
                            sys.exit(1)
                        counter += 1
            # If not, set up a fresh configuration.
            else:
                unowned_champions = get_unowned_champions(champions)
                write_in_role = True

            # Remove unowned champions from the pool of possible ones.
            champions = remove_unowned_champions(champions, unowned_champions)

            # If a configuration for a role was reset earlier, write it in.
            if write_in_role:
                write_in_configuration_file(config_file, role,
                                            "Unowned", unowned_champions)

            # Check if pool of available champions is empty.
            if not champions:
                print("\nNo more champions left to choose from.")
                sys.exit(1)

            while True:
                if not champions:
                    print("\nNo more champions left to choose from." +
                          "Now you have to play the very first chosen one!")
                    break

                random_champ = random.choice(champions)
                print("\nRandomly picked champions is: %s" % (random_champ))
                satisfied = input("Satisfied with the result? [yes/no] ")
                if (satisfied == "yes"):
                    write_in_stats(random_champ)
                    break
                else:
                    champions.remove(random_champ)
                    print("\nChampion removed from pool. Try again!")
        elif (function == "See stats about picked champions"
            or function == "2" or function == "2)"):  # noqa: E129
            # Is there already a stats section?
            try:
                stats = dict(Config.items("Stats"))
                for key in stats:
                    print(key.capitalize() + " - " + stats[key])

            # If not, notify the user.
            except configparser.NoSectionError:
                print("\nNo stats available in the moment!")
        else:
            print("\nThank you for using the application!")
            break
