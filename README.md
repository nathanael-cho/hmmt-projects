# Harvard-MIT Mathematics Tournament Projects

This is a place where all the software I write for the tournament will live. As a tournament director, I don't get to write as much software as I would like, but there's always time for a fun project here and there.

If you are an HMMT officer and would like to use the code here, make sure to fill out `user.py` with the appropriate information!

## General Overview

* `Assign Rooms`: generates room assignments for the teams at the tournament, given various restraints such as room size.
* `Generate Orders`: generates order slips for teams that pre-order shirts and/or pizzas.

## Required Packages

* `assign_rooms`: `selenium` (which itself requires a driver: the code assumes that the user has Google Chrome/ChromeDriver)
