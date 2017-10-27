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

sys.path.append("..")
from user import UserInfo

sys.path.append("../grab_data")
from grab_data import grab_csv


###########
# Globals #
###########

user_info = UserInfo()

# flag to determine whether the user passed in a teams csv
teams_csv_flag = 0

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
if len(sys.argv) != 4 and len(sys.argv) != 5:
    print("Usage 1: assign_rooms.py [rooms .csv file] [month] [number of individual teams]")
    print("Usage 2: assign_rooms.py [teams .csv file] [rooms .csv file] [month] [number of individual teams]")
    sys.exit()

if len(sys.argv) == 5:
    teams_csv_flag = 1


########
# Data #
########

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

###########
## Month ##
###########

month = sys.argv[3] if teams_csv_flag else sys.argv[2]

################################
## Number of Individual Teams ##
################################

individual_team_count = int(sys.argv[4]) if teams_csv_flag else int(sys.argv[3])

###########
## Teams ##
###########

# build team csv if it was not passed in
if not teams_csv_flag:
    # grab data from the website
    grab_csv("teams", month, user_info.dl_dir, user_info.work_dir, user_info.hmmt_user, user_info.hmmt_pass)
    grab_csv("orgs", month, user_info.dl_dir, user_info.work_dir, user_info.hmmt_user, user_info.hmmt_pass)

    # collect organizations into an object for building
    organizations_for_building = {}
    for organization in list(csv.reader(open(user_info.work_dir + "/orgs.csv", "r")))[1:]:
        organizations_for_building[organization[0]] = organization[1]

    # build team csv
    team_list = [["orgid", "orgname", "teamid", "teamname", "shortname"]]
    for team in list(csv.reader(open(user_info.work_dir + "/teams_"+ month + ".csv", "r")))[1:]:
        team_list.append([
            team[4], # organization
            organizations_for_building[team[4]],
            team[1], # number
            team[2], # name
            team[3], # shortname
        ])

    with open(user_info.work_dir + "/teams.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerows(team_list)

    # cleanup
    os.remove(user_info.work_dir + "/orgs.csv")
    os.remove(user_info.work_dir + "/teams_" + month + ".csv")

# minimum required columns: [orgid, orgname, teamid, teamname, shortname]
team_file = sys.argv[1] if teams_csv_flag else user_info.work_dir + "/teams.csv"
teams_raw = list(csv.reader(open(team_file, "r")))

team_categories = teams_raw[0]
teams_objectified = [list_objectify(x, team_categories, team_file) for x in teams_raw[1:]]

def integrate_team(team):
    team["orgid"] = int(team["orgid"])
    team["teamid"] = int(team["teamid"])
    return team

teams = [integrate_team(x) for x in teams_objectified]


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
    room_assignment_list = []
    for org in organizations:
        for team in org["teams"]:
            room_assignment_list.append(
                [team[x] for x in room_assignment_headers[:team_org_split]] + \
                [org[x] for x in room_assignment_headers[team_org_split:]]
            )
    def room_assignment_key(assignment):
        return assignment[4] # shortname
    room_assignment_list = sorted(room_assignment_list, key=room_assignment_key)

    with open(user_info.work_dir + "/room_assignment_output.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(room_assignment_headers)
        writer.writerows(room_assignment_list)
