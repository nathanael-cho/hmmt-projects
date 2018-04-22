###########
# Imports #
###########

import os
import shutil
from time import sleep
from selenium import webdriver

#############
# Functions #
#############

# no dest_dir => move the file to the current directory
def grab_csv(type, month, hmmt_user, hmmt_pass, dl_dir, dest_dir=None):
    if not type in ["indivs", "teams", "orgs"]:
        raise ValueError("The type must be 'teams' or 'orgs' or 'indivs'.")

    if not month in ["nov", "feb"]:
        raise ValueError("The month must be 'nov' or 'feb'.")

    driver = webdriver.Chrome()
    driver.get("http://www.hmmt.co/admin/login/")

    if driver.current_url == "http://www.hmmt.co/admin/login/":
        username = driver.find_element_by_id("id_username")
        username.send_keys(hmmt_user)
        password = driver.find_element_by_id("id_password")
        password.send_keys(hmmt_pass)
        driver.find_element_by_xpath("//input[@type='submit']").click()

        # give the browser some time to load
        sleep(0.25)

        if driver.current_url == "http://www.hmmt.co/admin/login/":
            raise RuntimeError("Bad username and/or password.")
        

    if type == "teams":
        driver.get("http://www.hmmt.co/admin/registration/team/export/?accepted__exact=1&month__exact=" + month)
    elif type == "orgs":
        driver.get("http://www.hmmt.co/admin/registration/organization/export/?")
    else:
        # TODO: wait for filter individual by month to be implemented on our website
        driver.get("http://www.hmmt.co/admin/registration/mathlete/export/?accepted=true")

    file_format = driver.find_element_by_id("id_file_format")
    file_options = file_format.find_elements_by_tag_name("option")
    for option in file_options:
        if option.get_attribute("value") == "0":
            option.click()
            break
    driver.find_element_by_xpath("//input[@type='submit']").click()

    # increase as needed if the downloads still fails
    sleep(0.5)

    dl_file = max([dl_dir + "/" + f for f in os.listdir(dl_dir)], key=os.path.getctime)
    dest_file = (dest_dir + "/" if dest_dir else "") + type + ("" if type == "orgs" else "_" + month) + ".csv"
    shutil.move(dl_file, dest_file)

    driver.close()
