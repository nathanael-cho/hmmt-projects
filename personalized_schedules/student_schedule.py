###########
# Imports #
###########

import csv
import sys
import os
from pylatex import Document, NewPage, LineBreak, LongTabu, LargeText, \
    SmallText, MultiColumn, TextColor, Command, Package, MiniPage, Center
from pylatex.utils import bold, NoEscape


############################
# General Helper Functions #
############################

def bold_sans_serif(string):
    return Command('textsf', bold(string))

def large_bss(string):
    return LargeText(bold_sans_serif(string))

def table_date(date):
    return [MultiColumn(3, align='c', color="black", data=TextColor("white", date))]

def table_header(table, date):
    table.add_row(table_date(date))
    table.add_row(["Time", "Event", "Location"], mapper=[bold_sans_serif])
    table.add_hline(color="black")


########
# Data #
########

################
## Data Check ##
################

def check_number_of_arguments():
    if len(sys.argv) != 2:
        print("Usage: student_schedule.py [room assignments .csv file]")
        sys.exit()

#################
## Assignments ##
#################

def assignment_objectify(list, headers):
    if len(headers) != len(list):
        raise ValueError(assignment_file + " was parsed incorrectly.")

    assignment_object = {}
    for index in range(len(headers)):
        assignment_object[headers[index]] = list[index]
    return assignment_object

def assignment_key(assignment):
    return (assignment["shortname"])

def get_room_assignments():
    assignment_file = sys.argv[1]

    # minimum required columns: [orgid, orgname, teamid, teamname, shortname, indbuilding, indroom,
    #   teambuilding, teamroom, gutsbuilding, gutsroom, awardsbuilding, awardsroom]
    room_assignments_raw = list(csv.reader(open(assignment_file, "r")))

    headers = room_assignments_raw[0]
    room_assignments = [assignment_objectify(x, headers) for x in room_assignments_raw[1:]]

    return sorted(room_assignments, key=assignment_key)

###############
## Schedules ##
###############

# TODO: read in spreadsheet with this data, for generalization
friday_schedule = [
    ["7:00PM", "8:00PM", "Early Registration", "E51"],
    ["7:00PM", "7:45PM", "Pizza and Ice Cream", "E51"],
    ["7:45PM", "8:00PM", "Mini-Events Preview", "E51"],
    ["8:00PM", "9:00PM", "Mini-Events", "E51"]
]

# the "Varies" entry is just a placeholder for readability
saturday_schedule = [
    ["8:00AM", "9:00AM", "Breakfast", "Science Center Lobby"],
    ["8:00AM", "9:00AM", "Breakfast", "Science Center Lobby"],
    ["9:00AM", "10:15AM", "Individual Round", "Varies"],
    ["10:30AM", "11:45AM", "Theme Round", "Varies"],
    ["12:00PM", "1:00PM", "Team Round", "Varies"],
    ["1:00PM", "2:30PM", "Lunch", "On your own*"],
    ["2:30PM", "4:15PM", "Guts Round", "Varies"],
    ["4:30PM", "6:00PM", "Award Ceremony", "Varies"]
]

###########################
## Data Helper Functions ##
###########################

def style_room(room, building):
    if building == "SC":
        return bold_sans_serif("Science Center " + room)
    return bold_sans_serif(building + " " + room)

def schedule_entry_to_row_entry(entry, assign):
    assert len(entry) == 4

    room = None
    if entry[2] == "Individual Round" or entry[2] == "Theme Round":
        room = style_room(assign["indroom"], assign["indbuilding"])
    elif entry[2] == "Team Round":
        room = style_room(assign["teamroom"], assign["teambuilding"])
    elif entry[2] == "Guts Round":
        room = style_room(assign["gutsroom"], assign["gutsbuilding"])
    elif entry[2] == "Award Ceremony":
        room = style_room(assign["awardsroom"], assign["awardsbuilding"])
    else:
        room = entry[3]

    return [NoEscape(entry[0] + " -- " + entry[1]), entry[2], room]

def add_schedule_row(table, entry, assignment, index):
    if (index % 2 == 0):
        table.add_row(schedule_entry_to_row_entry(entry, assignment), color="lightgray")
    else:
        table.add_row(schedule_entry_to_row_entry(entry, assignment))


########
# Main #
########

if __name__ == '__main__':
    check_number_of_arguments()

    room_assignments = get_room_assignments()

    geometry_options = {"margin": "1.25in"}
    doc = Document(geometry_options=geometry_options, indent=False, document_options=['11pt'])
    doc.preamble.append(Command('pagenumbering', arguments=["gobble"]))

    doc.add_color(name="lightgray", model="gray", description="0.80")

    for assignment in room_assignments:
        doc.append(large_bss("Org: " + assignment["orgname"]))
        doc.append(NoEscape(r'\smallskip'))
        doc.append(large_bss("\nTeam: " + assignment["teamname"]))
        doc.append(NoEscape(r'\smallskip'))
        doc.append(large_bss("\nTeam Nickname: " + assignment["shortname"]))
        doc.append(NoEscape(r'\smallskip'))

        doc.append(large_bss("\n\nStudent Schedule"))

        with doc.create(Center()):
            with doc.create(MiniPage(width=r"0.95\textwidth")):
                # @{} removes white space between columns
                with doc.create(LongTabu("X[l] @{} X[l] @{} X[l]", row_height=1.5, col_space="5pt")) as data_table:
                    table_header(data_table, "Friday, November 10, 2017 (MIT)")
                    for index in range(len(friday_schedule)):
                        add_schedule_row(data_table, friday_schedule[index], assignment, index)
                    
                doc.append(NoEscape(r'\bigskip'))

                with doc.create(LongTabu("X[l] @{} X[l] @{} X[l]", row_height=1.5, col_space="5pt")) as data_table:
                    table_header(data_table, "Saturday, November 11, 2017 (Harvard)")
                    for index in range(len(saturday_schedule)):
                        add_schedule_row(data_table, saturday_schedule[index], assignment, index)

        doc.append(NoEscape(r'\bigskip'))

        doc.append(SmallText("Locations in "))
        doc.append(SmallText(bold("bold ")))
        doc.append(SmallText("are "))
        doc.append(SmallText(bold("team specific")))
        doc.append(".")

        doc.append(NoEscape('\medskip'))
        
        doc.append(SmallText("\n*Teams that pre-ordered pizzas will be able to pick them up "))
        doc.append(SmallText("in the Science Center Lobby during lunchtime."))

        doc.append(NewPage())

    doc.generate_pdf('student_schedule', clean_tex=False)
