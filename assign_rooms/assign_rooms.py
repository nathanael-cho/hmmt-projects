###########################
# Some High Level Details #
###########################

# Organizations are guaranteed to have all their teams in the same room for the individual rounds,
#   guts round and award ceremony. Organizations will have all their teams in different rooms
#   for the team round.

# An organization's power index is the place of the top finishing team for that organization
#   last year if that team finished in the top 25, and 100 otherwise.


###############################
# Some High Level Assumptions #
###############################

# There are always enough enough organizations with only one or two teams.

# If a room is used for guts and awards, the room capacity is strictly higher for awards.

# If a room is used for individual and team, the room capacity is strictly higher for individual.

# We have already made the ad hoc organization for teams of individuals.


#########################
# Argument Requirements #
#########################

# TEAM_CSV: it must have the headers [orgid, orgname, teamid, teamname, shortname].
#   If the name is instead GRAB, the program will get the most recent team data from the website.

# ROOM_CSV: it must have the headers [building, number, indcap, teamcap, gutscap, awardscap].
#   The number does not necessarily have to be a number (e.g. Science Center *A*).

# ORGANIZATION_CSV: it must have the headers [id, name].
#   If the name is instead GRAB, the program will get the most recent team data from the website.

# POWERINDEX_CSV: it must have the headers [orgid, powerindex, teamids].
#   See above for an explanation of what the power index is.
#   The teamids must be delimited by a "^", e.g. "1^2^3".

# MONTH: it must be either "nov" or "feb".

# NUMBER OF INDIVIDUAL TEAMS: it should be either 3 or 4 (not a hard requirement though).

# INDIV_ROOM: it should be able to fit all the individuals, and it should be both
#   an individual room and a team room. The string should be formatted as follows:
#   "[BUILDING]^[ROOM NAME/NUMBER]"


###########
# Imports #
###########

import csv
import sys
import os
from operator import itemgetter

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

default = {
    "teams": "teams.csv",
    "orgs": "orgs.csv",
    "powerindices": "powerindices.csv",
    "rooms": "rooms.csv",
    "month": "nov",
    "indiv_room": "SC^A"
}

passed_in = {
    "teams": None,
    "orgs": None,
    "powerindices": None,
    "rooms": None,
    "month": None,
    "indiv_room": None
}

individual_org_name = "Individuals"

room_assignment_headers = ["orgid", "orgname", "teamid", "teamname", "shortname", "teambuilding", "teamroom",
                           "indbuilding", "indroom", "gutsbuilding", "gutsroom", "awardsbuilding", "awardsroom"]

# in relation to room_assignment_headers: get earlier indices from team objects and
#   later indices from organization objects
team_org_split = 7


##################
# Data Functions #
##################

#####################
## Check Arguments ##
#####################

def print_help():
    print("\nUsage: [ARGUMENTS]")

    print("\nArgument Options:")
    print("  -t TEAM_CSV                  File containing team information.")
    print("  -r ROOM_CSV                  File containing room information.")
    print("  -o ORGANIZATION_CSV          File containing organization information.")
    print("  -p POWERINDEX_CSV            File containing power indices.")
    print("  -m MONTH                     The month of the tournament.")
    print("  -i INDIV_ROOM                Where individuals will take the morning rounds.")

    print("\nThe requirements for the various arguments can be found at the top of `assign_rooms.py`.\n")
    sys.exit()

def parse_arguments():
    if len(sys.argv) == 2 and sys.argv[1] == "-h":
        print_help()

    if len(sys.argv) % 2 == 0:
        raise RuntimeError("Every argument must be preceded by a flag. " + \
                           "Use the -h flag to see all arguments/flags.")

    global passed_in
    for index in range(len(sys.argv))[1::2]:
        if sys.argv[index] == "-t":
            if (not os.path.isfile(sys.argv[index + 1])) and sys.argv[index + 1] != "GRAB":
                raise ValueError("The file " + sys.argv[index + 1] +  " passed in is not valid.")
            passed_in["teams"] = sys.argv[index + 1]
        elif sys.argv[index] == "-r":
            if not os.path.isfile(sys.argv[index + 1]):
                raise ValueError("The file " + sys.argv[index + 1] +  " passed in is not valid.")
            passed_in["rooms"] = sys.argv[index + 1]
        elif sys.argv[index] == "-o":
            if not os.path.isfile(sys.argv[index + 1]) and sys.argv[index + 1] != "GRAB":
                raise ValueError("The file " + sys.argv[index + 1] +  " passed in is not valid.")
            passed_in["orgs"] = sys.argv[index + 1]
        elif sys.argv[index] == "-p":
            if not os.path.isfile(sys.argv[index + 1]):
                raise ValueError("The file " + sys.argv[index + 1] +  " passed in is not valid.")
        elif sys.argv[index] == "-m":
            passed_in["month"] = sys.argv[index + 1]
        elif sys.argv[index] == "-i":
            passed_in["indiv_room"] = sys.argv[index + 1]
        else:
            raise RuntimeError("You used an invalid flag. Use the -h flag to see all arguments/flags.")

###########
## Rooms ##
###########

def integrate_room(room):
    room["indcap"] = int(room["indcap"])
    room["teamcap"] = int(room["teamcap"])
    room["gutscap"] = int(room["gutscap"])
    room["awardscap"] = int(room["awardscap"])
    return room

def room_key(room):
    return -room["indcap"]

def get_rooms():
    rooms_file = passed_in["rooms"] if passed_in["rooms"] else default["rooms"]

    # minimum required columns: [building, number, indcap, teamcap, gutscap, awardscap]
    with open(rooms_file, "r") as file:
        return sorted([integrate_room(x) for x in list(csv.DictReader(file))], key=room_key)

##################
## Organization ##
##################

def orgs_file_to_list(orgs_file):
    organizations = {}
    for organization in list(csv.DictReader(open(orgs_file, "r"))):
        organizations[organization["id"]] = organization["name"]
    return organizations

def get_organizations(month):
    if passed_in["orgs"] and passed_in["orgs"] == "GRAB":
        grab_csv("orgs", month, user_info.hmmt_user, user_info.hmmt_pass, user_info.dl_dir, user_info.work_dir)
        orgs_file = user_info.work_dir + "/orgs.csv"
        return orgs_file_to_list(orgs_file)

    orgs_file = passed_in["orgs"] if passed_in["orgs"] else default["orgs"]
    return orgs_file_to_list(orgs_file)

#################
## Power Index ##
#################

def get_powerindices():
    pi_file = passed_in["powerindices"] if passed_in["powerindices"] else default["powerindices"]
    pi_object = {}
    pi_list = list(csv.DictReader(open(pi_file, "r")))
    for pi in pi_list:
        pi_object[int(pi["orgid"])] = {
            "index": int(pi["powerindex"]),
            "teamids": [int(x) for x in pi["teamids"].split("^")]
        }
    return pi_object

# checks if a team with a power index has already been assigned to a (team) room
def power_present(teams):
    for team in teams:
        if "powerindex" in team:
            return True
    return False

# checks whether a team with a power index can be placed in a given room
def power_possible(team, list):
    return not "powerindex" in team or not power_present(list)

###########
## Month ##
###########

def get_month():
    return passed_in["month"] if passed_in["month"] else default["month"]

##########################
## Individual Team Room ##
##########################

def get_indiv_team_room():
    return  passed_in["indiv_room"] if passed_in["indiv_room"] else default["indiv_room"]

###########
## Teams ##
###########

def integrate_team(team):
    team["orgid"] = int(team["orgid"])
    team["teamid"] = int(team["teamid"])
    return team

def get_teams(month):
    # build team csv if it was not passed in
    if passed_in["teams"] and passed_in["teams"] == "GRAB":
        # grab data from the website
        grab_csv("teams", month, user_info.hmmt_user, user_info.hmmt_pass, user_info.dl_dir, user_info.work_dir)

        # collect organizations into an object for building
        organizations_for_building = get_organizations(month)

        # build team csv
        team_list = [["orgid", "orgname", "teamid", "teamname", "shortname"]]
        for team in list(csv.DictReader(open(user_info.work_dir + "/teams_"+ month + ".csv", "r"))):
            team_list.append([
                team["organization"],
                organizations_for_building[team["organization"]],
                team["number"],
                team["name"],
                team["shortname"]
            ])

        # cleanup old teams file
        os.remove(user_info.work_dir + "/teams_" + month + ".csv")

        # this seems redundant, but this is to have a copy in csv form
        with open(user_info.work_dir + "/teams.csv", "w") as file:
            writer = csv.writer(file)
            writer.writerows(team_list)

        with open(user_info.work_dir + "/teams.csv", "r") as file:
            return [integrate_team(x) for x in list(csv.DictReader(file))]

    teams_file = passed_in["teams"] if passed_in["teams"] else default["teams"]

    with open(teams_file, "r") as file:
        return [integrate_team(x) for x in list(csv.DictReader(file))]


###############################
## Data Processing Functions ##
###############################

# sort organizations by number of teams
def organization_key(org):
    # we want to sort in decreasing order, putting individuals at the head
    if org["orgname"] == individual_org_name:
        # all other power indices are >= 1, and 10  is sufficiently larger than
        #   the maximum number of teams an organization can have
        return (0, -10)
    return (org["powerindex"], -len(org["teams"]))

def team_list_to_org_list(team_list):
    teams_sorted = sorted(team_list, key=itemgetter("orgid", "teamid"))

    powerindices = get_powerindices()

    # get list of organizations with associated number of teams
    organizations = []
    org_teams = []
    for index in range(len(teams_sorted)):
        team = teams_sorted[index]
        org_teams.append(team)
        if index == len(teams_sorted) - 1 or team["orgid"] != teams_sorted[index + 1]["orgid"]:
            powerindex = powerindices[team["orgid"]]["index"] if team["orgid"] in powerindices else 100
            if powerindex < 100:
                for org_team in org_teams:
                    if org_team["teamid"] in powerindices[team["orgid"]]["teamids"]:
                        org_team["powerindex"] = powerindex

            organizations.append({
                "orgid": team["orgid"],
                "orgname": team["orgname"],
                "teams": org_teams,
                "number_of_teams": len(org_teams),
                "powerindex": powerindex,
                "indbuilding": None,
                "indroom": None,
                "teambuilding": None,
                "teamrooms": [],
                "gutsbuilding": None,
                "gutsroom": None,
                "awardsbuilding": None,
                "awardsroom": None
            })
            org_teams = []

    return sorted(organizations, key=organization_key)

# add useful fields to room objects
def augment_room_object(room):
    room["indassigned"] = 0
    room["teamassigned"] = 0
    room["teamroundteams"] = []
    room["gutsassigned"] = 0
    room["awardsassigned"] = 0
    return room

# the difference here from the organizations is that we cared about an
#   ordering on organizations
def room_list_to_building_object(room_list):
    rooms_augmented = [augment_room_object(x) for x in room_list]

    buildings = {}
    for room in rooms_augmented:
        room_key = room["building"] + " " + room["number"]
        if room["building"] in buildings:
            building = buildings[room["building"]]
            building["rooms"][room_key] = room
            building["indcap"] += room["indcap"]
            building["teamcap"] += room["teamcap"]
            building["gutscap"] += room["gutscap"]
            building["awardscap"] += room["awardscap"]
        else:
            buildings[room["building"]] = {
                "name": room["building"],
                "rooms": {room_key: room},
                "indcap": room["indcap"],
                "indassigned": 0,
                "teamcap": room["teamcap"],
                "teamassigned": 0,
                "gutscap": room["gutscap"],
                "awardscap": room["awardscap"]
            }

    return buildings


########
# Main #
########

if __name__ == '__main__':
    parse_arguments()

    month = get_month()
    teams = get_teams(month)

    # starts off sorted by individual capacity in decreasing order
    rooms = get_rooms()

    # put teams and rooms into their larger groups
    organizations = team_list_to_org_list(teams)
    buildings = room_list_to_building_object(rooms)

    # set individual team rooms first
    indiv_org = organizations[0]
    indiv_team_count = len(indiv_org["teams"])

    if indiv_org["orgname"] != individual_org_name:
        raise RuntimeError("The organizations list does not start with the individuals organization.")

    indiv_room_parsed = get_indiv_team_room().split("^")
    indiv_room_key = indiv_room_parsed[0] + " " + indiv_room_parsed[1]

    indiv_building = buildings[indiv_room_parsed[0]]
    indiv_room = indiv_building["rooms"][indiv_room_key]
    if indiv_room["indcap"] < indiv_team_count or indiv_room["teamcap"] < indiv_team_count:
        raise ValueError("The room cannot hold all the individual teams.")

    indiv_room["indassigned"] += indiv_team_count
    indiv_room["teamassigned"] += indiv_team_count
    indiv_building["indassigned"] += indiv_team_count
    indiv_building["teamassigned"] += indiv_team_count
    indiv_org["indbuilding"] = indiv_room_parsed[0]
    indiv_org["indroom"] = indiv_room_parsed[1]
    indiv_org["teamrooms"].append(indiv_room_key)

    for team in indiv_org["teams"]:
        team["teambuilding"] = indiv_room_parsed[0]
        team["teamroom"] = indiv_room_parsed[1]

    # assign individual buildings, and assign a single team per organization
    #   to that room if it is also a team room
    for org in organizations[1:]:
        # all modifications will happen to the rooms within the buildings object
        for room_facade in rooms:
            room_key = room_facade["building"] + " " + room_facade["number"]
            building = buildings[room_facade["building"]]
            room = building["rooms"][room_key]

            if len(org["teams"]) <= room["indcap"] - room["indassigned"]:
                room["indassigned"] += org["number_of_teams"]
                building["indassigned"] += org["number_of_teams"] # just for bookkeeping
                org["indbuilding"] = room["building"]
                org["indroom"] = room["number"]

                if room["teamcap"] > room["teamassigned"]:
                    for team in org["teams"]:
                        if power_possible(team, room["teamroundteams"]):
                            room["teamassigned"] += 1
                            building["teamassigned"] += 1 # mostly for bookkeeping
                            room["teamroundteams"].append(team)

                            team["teambuilding"] = room["building"]
                            team["teamroom"] = room["number"]
                            org["teamrooms"].append(room_key)
                            break
                break

    # first pass to keep as many teams as possible in the same building
    for org in organizations[1:]:
        if len(org["teamrooms"]) == org["number_of_teams"]:
            continue

        building = buildings[org["indbuilding"]]
        rooms_in_building = building["rooms"]
        for room_key in rooms_in_building:
            if len(org["teamrooms"]) == org["number_of_teams"]:
                break

            room = rooms_in_building[room_key]
            if room["teamcap"] > room["teamassigned"] and not room_key in org["teamrooms"]:
                for team in org["teams"]:
                    if not "teambuilding" in team and power_possible(team, room["teamroundteams"]):
                        room["teamassigned"] += 1
                        building["teamassigned"] += 1
                        room["teamroundteams"].append(team)

                        team["teambuilding"] = room["building"]
                        team["teamroom"] = room["number"]
                        org["teamrooms"].append(room_key)
                        break

    # assign the rest of the team buildings
    for org in organizations[1:]:
        if len(org["teamrooms"]) == org["number_of_teams"]:
            continue

        for team in org["teams"]:
            if "teambuilding" in team:
                continue

            for room_facade in rooms:
                room_key = room_facade["building"] + " " + room_facade["number"]
                building = buildings[room_facade["building"]]
                room = building["rooms"][room_key]
                if room["teamcap"] > room["teamassigned"] and \
                   (not room_key in org["teamrooms"]) and power_possible(team, room["teamroundteams"]):
                    room["teamassigned"] += 1
                    building["teamassigned"] += 1
                    room["teamroundteams"].append(team)

                    org["teamrooms"].append(room_key)
                    team["teambuilding"] = room["building"]
                    team["teamroom"] = room["number"]
                    break

    # collect awards rooms
    awards_rooms = [x for x in rooms if x["awardscap"] > 0]
    award_stride_limit = len(awards_rooms)

    # arrange teams by powerindex, then by size
    def awards_key(room):
        return(room["powerindex"], -room["number_of_teams"])
    organizations = sorted(organizations, key=awards_key)

    # assign awards rooms
    award_stride = 0
    for org in organizations:
        awards_room_index = award_stride
        awards_room_original_index = award_stride
        while (not org["awardsbuilding"]):
            room = awards_rooms[awards_room_index]
            if len(org["teams"]) <= room["awardscap"] - room["awardsassigned"]:
                org["awardsbuilding"] = room["building"]
                org["awardsroom"] = room["number"]
                room["awardsassigned"] += len(org["teams"])
                break
            awards_room_index = (awards_room_index + 1) % award_stride_limit
            if (awards_room_index == awards_room_original_index):
                raise RuntimeError("Not able to assign the organization " + \
                                   org["orgname"] + " to an awards room.")
        award_stride = (award_stride + 1) % award_stride_limit

    # collect guts rooms
    guts_rooms = [x for x in rooms if x["gutscap"] > 0]

    # first pass to ensure that most (if not all) of the teams in a guts room
    #   that becomes an awards room stay there
    stride = 0
    for org in organizations:
        for room in guts_rooms:
            if room["building"] == org["awardsbuilding"] and \
               room["number"] == org["awardsroom"] and \
               room["gutscap"] - room["gutsassigned"] >= org["number_of_teams"]:
                org["gutsbuilding"] = room["building"]
                org["gutsroom"] = room["number"]
                room["gutsassigned"] += org["number_of_teams"]
                break

    # second pass to assign the rest of the guts rooms
    for org in organizations:
        if org["gutsroom"]:
            continue
        for room in guts_rooms:
            if len(org["teams"]) <= room["gutscap"] - room["gutsassigned"]:
                org["gutsbuilding"] = room["building"]
                org["gutsroom"] = room["number"]
                room["gutsassigned"] += len(org["teams"])
                break

    # generate new csv
    room_assignment_list = []
    for org in organizations:
        for team in org["teams"]:
            room_assignment_list.append(
                [team[x] for x in room_assignment_headers[:team_org_split]] + \
                [org[x] for x in room_assignment_headers[team_org_split:]]
            )
    room_assignment_list = sorted(room_assignment_list, key=itemgetter(4))

    with open(user_info.work_dir + "/room_assignments.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(room_assignment_headers)
        writer.writerows(room_assignment_list)
