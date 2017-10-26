###########################################
# Some High Level Assumptions and Details #
###########################################

# Organizations are guaranteed to have all their teams in the same building for the individual
#   and team rounds, and the same room for the guts round and award ceremony

# There will be enough organizations with only one or two teams

# If a room is used for guts and awards, the room capacity is higher for awards. If a room is used
#   for individual and team, the room capacity is higher for individual.


###########
# Imports #
###########

import csv
import sys
import os
import shutil
from time import sleep
from selenium import webdriver
from datetime import datetime


###########
# Globals #
###########

# flag to determine whether the user passed in a teams csv
teams_csv_flag = 0

# where files such as the downloads are sent, as where as where final csv files are stored
work_directory = "/Users/Nacho/Desktop/HMMT/2017-2018/hmmt-projects/assign_rooms/"

room_assignment_headers = ["orgid", "orgname", "teamid", "teamname", "shortname", "indbuilding", "indroom",
                           "teambuilding", "teamroom", "gutsbuilding", "gutsroom", "awardsbuilding", "awardsroom"]

# in relation to room_assignment_headers: get earlier indices from team objects and
#   later indices from organization objects
team_org_split = 9


############################
# General Helper Functions #
############################

def list_objectify(list, categories, file):
    if len(categories) != len(list):
        raise ValueError(file + " was parsed incorrectly.")

    list_object = {}
    for index in range(len(categories)):
        list_object[categories[index]] = list[index]
    return list_object


###################
# Check Arguments #
###################

# we can pass in two or three arguments: the team csv is optional, and the rooms csv and the
#   number of individual teams are required
if len(sys.argv) != 3 and len(sys.argv) != 4:
    print("Usage 1: assign_rooms.py [rooms .csv file] [number of individual teams]")
    print("Usage 2: assign_rooms.py [teams .csv file] [rooms .csv file] [number of individual teams]")
    sys.exit()

if len(sys.argv) == 4:
    teams_csv_flag = 1


#########################
# CSVs From Our Website #
#########################

def grab_csv(type):
    if type != "teams" and type != "orgs":
        raise ValueError("We only want the teams array or the organizations array.")

    driver = webdriver.Chrome()
    driver.get("http://www.hmmt.co/admin/login/")

    if driver.current_url == "http://www.hmmt.co/admin/login/":
        username = driver.find_element_by_id("id_username")
        username.send_keys("PUT YOUR USERNAME HERE")
        password = driver.find_element_by_id("id_password")
        password.send_keys("PUT YOUR PASSWORD HERE")
        driver.find_element_by_xpath("//input[@type='submit']").click()

    if type == "teams":
        driver.get("http://www.hmmt.co/admin/registration/team/export/?accepted__exact=1&month__exact=nov")
    else:
        driver.get("http://www.hmmt.co/admin/registration/organization/export/?")

    file_format = driver.find_element_by_id("id_file_format")
    file_options = file_format.find_elements_by_tag_name("option")
    for option in file_options:
        if option.get_attribute("value") == "0":
            option.click()
            break
    driver.find_element_by_xpath("//input[@type='submit']").click()

    # increase as needed if the downloads still fail
    sleep(0.5)

    download_directory = "/Users/Nacho/Downloads"
    download_destination = work_directory + type + "_download.csv"
    download_name = max([download_directory + "/" + f for f in os.listdir(download_directory)], key=os.path.getctime)
    shutil.move(download_name, download_destination)

    driver.close()

if not teams_csv_flag:
    grab_csv("teams")
    grab_csv("orgs")


##################
# Build Team CSV #
##################

if not teams_csv_flag:
    # collect organizations into an object for building
    organizations_for_building = {}
    for organization in list(csv.reader(open(work_directory + "orgs_download.csv", "r")))[1:]:
        organizations_for_building[organization[0]] = organization[1]

    # build team csv
    team_list = [["orgid", "orgname", "teamid", "teamname", "shortname"]]
    for team in list(csv.reader(open(work_directory + "teams_download.csv", "r")))[1:]:
        team_list.append([
            team[4], # organization
            organizations_for_building[team[4]],
            team[1], # number
            team[2], # name
            team[3], # shortname
        ])

    with open(work_directory + "teams.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerows(team_list)

    # cleanup
    os.remove(work_directory + "orgs_download.csv")
    os.remove(work_directory + "teams_download.csv")


########
# Data #
########

###########
## Teams ##
###########

# minimum required columns: [orgid, orgname, teamid, teamname, shortname]
teams_raw = list(csv.reader(open(sys.argv[1], "r"))) if teams_csv_flag \
            else list(csv.reader(open(work_directory + "teams.csv", "r")))

team_categories = teams_raw[0]
teams_objectified = [list_objectify(x, team_categories, "teams.csv") for x in teams_raw[1:]]

def integrate_team(team):
    team["orgid"] = int(team["orgid"])
    team["teamid"] = int(team["teamid"])
    return team

teams = [integrate_team(x) for x in teams_objectified]


###########
## Rooms ##
###########

room_file = sys.argv[2] if teams_csv_flag else sys.argv[1]

# minimum required columns: [building, room, indcap, teamcap, gutscap, awardscap]
rooms_raw = list(csv.reader(open(room_file, "r")))

room_categories = rooms_raw[0]
rooms_objectified = [list_objectify(x, room_categories, room_file) for x in rooms_raw[1:]]

def integrate_room(room):
    room["indcap"] = int(room["indcap"])
    room["teamcap"] = int(room["teamcap"])
    room["gutscap"] = int(room["gutscap"])
    room["awardscap"] = int(room["awardscap"])
    return room

rooms = [integrate_room(x) for x in rooms_objectified]

################################
## Number of Individual Teams ##
################################

individual_team_count = int(sys.argv[3]) if teams_csv_flag else int(sys.argv[2])


###############################
## Data Processing Functions ##
###############################

def team_list_to_org_list(team_list):
    # sort teams first by orgid, then by teamid
    max_team_id = max([x["teamid"] for x in team_list])
    def team_key(team):
        return (team["orgid"] * (max_team_id + 1) + team["teamid"])
    teams_sorted = sorted(team_list, key=team_key)

    # get list of organizations with associated number of teams
    organizations = []
    org_teams = []
    for index in range(len(teams_sorted)):
        team = teams_sorted[index]
        org_teams.append(team)
        if index == len(teams_sorted) - 1 or team["orgid"] != teams_sorted[index + 1]["orgid"]:
            organizations.append({
                "orgid": team["orgid"],
                "orgname": team["orgname"],
                "teams": org_teams,
                "indbuilding": None,
                "teambuilding": None,
                "gutsbuilding": None,
                "gutsroom": None,
                "awardsbuilding": None,
                "awardsroom": None
            })
            org_teams = []

    # add individual team "organization" to the list
    #     we will try to keep the individual teams together
    individual_teams = [
        {"orgid": None, "orgname": "Individuals", "teamid": None, "teamname": "Individual " + str(x + 1), \
         "shortname": "Individual " + str(x + 1)} for x in range(individual_team_count)
    ]
    organizations.append({
        "orgid": None,
        "orgname": "Individuals",
        "teams": individual_teams,
        "indbuilding": None,
        "teambuilding": None,
        "gutsbuilding": None,
        "gutsroom": None,
        "awardsbuilding": None,
        "awardsroom": None
    })

    # sort organizations by number of teams
    def organization_key(org):
        # we want to sort in decreasing order
        return -len(org["teams"])
    organizations_sorted = sorted(organizations, key=organization_key)

    return organizations_sorted

# the difference here from the previous function is that we cared about an ordering on organizations
def room_list_to_building_object(room_list):
    # add useful fields to room objects
    def augment_room_object(room):
        room["indassigned"] = 0
        room["teamassigned"] = 0
        room["gutsassigned"] = 0
        room["awardsassigned"] = 0
        return room

    rooms_augmented = [augment_room_object(x) for x in room_list]

    # sort rooms by building
    def room_key(room):
        return room["building"]
    rooms_sorted = sorted(rooms_augmented, key=room_key)
    
    # get building capacity information
    buildings = {}
    room_data = {
        "rooms": [],
        "indcap": 0,
        "teamcap": 0,
        "gutscap": 0,
        "awardscap": 0,
    }
    for index in range(len(rooms_sorted)):
        room = rooms_sorted[index]
        room_data["rooms"].append(room)
        room_data["indcap"] += room["indcap"]
        room_data["teamcap"] += room["teamcap"]
        room_data["gutscap"] += room["gutscap"]
        room_data["awardscap"] += room["awardscap"]

        if index == len(rooms_sorted) - 1 or room["building"] != rooms_sorted[index + 1]["building"]:
            buildings[room["building"]] = {
                "indcap": room_data["indcap"],
                "indassigned": 0,
                "teamcap": room_data["teamcap"],
                "teamassigned": 0,
                "gutscap": room_data["gutscap"],
                "awardscap": room_data["awardscap"],
                "rooms": room_data["rooms"]
            }
            room_data = {
                "rooms": [],
                "indcap": 0,
                "teamcap": 0,
                "gutscap": 0,
                "awardscap": 0
            }

    return buildings


########
# Main #
########

if __name__ == '__main__':
    # set up more useful versions of the data passed in
    organizations = team_list_to_org_list(teams)
    buildings = room_list_to_building_object(rooms)

    # assign team buildings
    for org in organizations:
        for building in buildings:
            data = buildings[building]
            if len(org["teams"]) <= data["teamcap"] - data["teamassigned"]:
                org["teambuilding"] = building
                buildings[building]["teamassigned"] += len(org["teams"])
                break

    # assign team rooms
    for org in organizations:
        for team in org["teams"]:
            team["teambuilding"] = org["teambuilding"]

            building_data = buildings[org["teambuilding"]]
            for room in building_data["rooms"]:
                if room["teamcap"] > room["teamassigned"]:
                    team["teamroom"] = room["room"]
                    room["teamassigned"] += 1
                    break
        

    # first pass to maximize the number of teams that do not have to switch buildings from team to individual
    for org in organizations:
        for building in buildings:
            data = buildings[building]
            if org["teambuilding"] == building and len(org["teams"]) <= data["indcap"] - data["indassigned"]:
                org["indbuilding"] = building
                buildings[building]["indassigned"] += len(org["teams"])
                break

    # second pass to assign individual buildings to the rest of the organizations
    for org in organizations:
        if org["indbuilding"]:
            continue
        for building in buildings:
            data = buildings[building]
            if len(org["teams"]) <= data["indcap"] - data["indassigned"]:
                org["indbuilding"] = building
                buildings[building]["indassigned"] += len(org["teams"])
                break

    # first pass to assign individual rooms to maximize the number of teams that do not have to switch rooms
    for org in organizations:
        for team in org["teams"]:
            team["indbuilding"] = org["indbuilding"]            
            building_data = buildings[org["indbuilding"]]
            for room in building_data["rooms"]:
                if room["indcap"] > 0 and team["indbuilding"] == team["teambuilding"] and team["teamroom"] == room["room"]:
                    team["indroom"] = room["room"]
                    room["indassigned"] += 1
                    break

    # second pass to assign the rest of the individual rooms
    for org in organizations:
        for team in org["teams"]:
            if "indroom" in team:
                continue
            building_data = buildings[org["indbuilding"]]
            for room in building_data["rooms"]:
                if room["indcap"] > room["indassigned"]:
                    team["indroom"] = room["room"]
                    room["indassigned"] += 1
                    break

    # collect guts rooms
    guts_rooms = []
    for building in buildings:
        data = buildings[building]
        if data["gutscap"] > 0:
            for room in data["rooms"]:
                if room["gutscap"] > 0:
                    guts_rooms.append(room)
    stride_limit = len(guts_rooms)


    # assign guts rooms
    stride = 0
    for org in organizations:
        guts_room_index = stride
        guts_room_original_index = stride
        while (not org["gutsbuilding"]):
            room = guts_rooms[guts_room_index]
            if len(org["teams"]) <= room["gutscap"] - room["gutsassigned"]:
                org["gutsbuilding"] = room["building"]
                org["gutsroom"] = room["room"]
                room["gutsassigned"] += len(org["teams"])
                break
            guts_room_index = (guts_room_index + 1) % stride_limit
            if (guts_room_index == guts_room_original_index):
                raise RuntimeError("Not able to assign the organization " + org["orgname"])
        stride = (stride + 1) % stride_limit

    # collect awards rooms
    awards_rooms = []
    for building in buildings:
        data = buildings[building]
        if data["awardscap"] > 0:
            for room in data["rooms"]:
                if room["awardscap"] > 0:
                    awards_rooms.append(room)

    # first pass to assign awards rooms to maximize the number of teams that do not have to switch rooms
    for org in organizations:
        for room in awards_rooms:
            if org["gutsbuilding"] == room["building"] and org["gutsroom"] == room["room"]:
                org["awardsbuilding"] = room["building"]
                org["awardsroom"] = room["room"]
                room["awardsassigned"] += len(org["teams"])
                break

    # second pass to assign the rest of the awards rooms
    for org in organizations:
        if org["awardsroom"]:
            continue
        for room in awards_rooms:
            if len(org["teams"]) <= room["awardscap"] - room["awardsassigned"]:
                org["awardsbuilding"] = room["building"]
                org["awardsroom"] = room["room"]
                room["awardsassigned"] += len(org["teams"])
                break

    # generate new csv
    room_assignment_list = [room_assignment_headers]
    for org in organizations:
        for team in org["teams"]:
            room_assignment_list.append(
                [team[x] for x in room_assignment_headers[:team_org_split]] + \
                [org[x] for x in room_assignment_headers[team_org_split:]]
            )

    with open(work_directory + "room_assignment_output.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerows(room_assignment_list)
