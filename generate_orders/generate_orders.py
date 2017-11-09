###########
# Credits #
###########

# Inspired the label generating python script written by Calvin Deng, Harvard Class of 2017.
#   In particular, the function `latex_escape` was taken directly from his code.


##############
# High Level #
##############

# Generates the text files `shirt_orders.txt` and `pizza_orders.txt`, which are used by the
#   LaTeX file.
# The workflow is `python3 generate_orders.py [ORDERS_CSV]` => `pdflatex orders.tex` (or equivalent)


#########################
# Argument Requirements #
#########################

# ORGANIZATION_CSV: it must have the headers [orgid, orgname, teamid, teamname, shortname].

# ORDERS_CSV: it must have the headers[orgid, orgname, xs, s, m, l, xl, xxl, cheese, pepperoni]


###########
# Imports #
###########

import csv
import sys
import os
from itertools import product


###########
# Globals #
###########

default = {
    "orders": "orders.csv"
}

passed_in = {
    "orders": None
}

shirt_order_xs = [0.5, 4.25]
shirt_order_ys = [0.5, 2.5, 4.5, 6.5, 8.5]

shirt_order_yxs = list(product(shirt_order_ys, shirt_order_xs))

shirt_orders_per_page = len(shirt_order_yxs)


##################
# Data Functions #
##################

#####################
## Check Arguments ##
#####################

# Usage: python3 generate_orders.py [ARGUMENTS]

def print_help():
    print("\nUsage: [ARGUMENTS]")

    print("\nArgument Options:")
    print("  -r ORDERS_CSV                 File containing pizza and shirt orders.")

    print("\nThe requirements for the various arguments can be found")
    print("at the top of `generate_rooms.py`.\n")
    sys.exit()

def parse_arguments():
    if len(sys.argv) == 2 and sys.argv[1] == "-h":
        print_help()

    if len(sys.argv) % 2 == 0:
        raise RuntimeError("Every argument must be preceded by a flag. " + \
                           "Use the -h flag to see all arguments/flags.")

    global passed_in
    for index in range(len(sys.argv))[1::2]:
        if sys.argv[index] == "-r":
            if not os.path.isfile(sys.argv[index + 1]):
                raise ValueError("The file " + sys.argv[index + 1] +  " passed in is not valid.")
            passed_in["orders"] = sys.argv[index + 1]
        else:
            raise RuntimeError("You used an invalid flag. Use the -h flag to see all arguments/flags.")

###################
## LaTeX Helpers ##
###################

def latex_escape(s):
    # handle characters that require an escape in LaTeX
    s = s.replace('&', '\\&')
    s = s.replace('<', '\\textless')
    s = s.replace('#', '\\#')

    # handle quotes
    tokens = s.split('"')
    l = []
    for i, token in enumerate(tokens):
        if i > 0 and i % 2 == 0:
            l.append("''")
        elif i > 0 and i % 2 == 1:
            l.append("``")
        l.append(token)
    s = ''.join(l)
    return s

############
## Orders ##
############

def orders_file_to_object(orders_file):
    orders = {}
    for order in list(csv.DictReader(open(orders_file, "r"))):
        orders[int(order["orgid"])] = order
    return orders

def shirt_order_string(x, y, order):
    return "\\mylabel{%f}{%f}{%s\\\\%s}{S: %d\\\\M: %d\\\\L: %d\\\\XL: %d\\\\XXL: %d}" % (
        x,
        y,
        "\\underline{Shirt Orders}",
        latex_escape(order["orgname"]),
        int(order["s"]),
        int(order["m"]),
        int(order["l"]),
        int(order["xl"]),
        int(order["xxl"]),
    )

def pizza_order_string(x, y, order):
    return "\\mylabel{%f}{%f}{%s\\\\%s}{Cheese: %d\\\\Pepperoni: %d}" % (
        x,
        y,
        "\\underline{Pizza Orders}",
        latex_escape(order["orgname"]),
        int(order["cheese"]),
        int(order["pepperoni"]),
    )


########
# Main #
########

if __name__ == '__main__':
    parse_arguments()

    orders = orders_file_to_object(passed_in["orders"] if passed_in["orders"] else default["orders"])

    with open("shirt_orders.txt", "w") as f:
        shirt_page_index = 0
        page_flushed = False
        for orgid in orders:
            if shirt_page_index % shirt_orders_per_page == 0 and not page_flushed:
                print("\\myflush", file = f)
                page_flushed = True

            order = orders[orgid]

            if int(order["s"]) + int(order["m"]) + int(order["l"]) + int(order["xl"]) + int(order["xxl"]) > 0:
                y, x = shirt_order_yxs[shirt_page_index]
                print(shirt_order_string(x, y, order), file = f)

                shirt_page_index = (1 + shirt_page_index) % shirt_orders_per_page
                page_flushed = False

    with open("pizza_orders.txt", "w") as f:
        pizza_page_index = 0
        page_flushed = False
        for orgid in orders:
            if pizza_page_index % shirt_orders_per_page == 0 and not page_flushed:
                print("\\myflush", file = f)
                page_flushed = True

            order = orders[orgid]

            if int(order["cheese"]) + int(order["pepperoni"]) > 0:
                y, x = shirt_order_yxs[pizza_page_index]
                print(pizza_order_string(x, y, order), file = f)

                pizza_page_index = (1 + pizza_page_index) % shirt_orders_per_page
                page_flushed = False
