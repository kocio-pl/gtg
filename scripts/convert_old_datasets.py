#!/usr/bin/env python

import lxml.etree as ET
import uuid
from datetime import datetime


#############################################################
# Skeleton creation #########################################
#############################################################

# Create the root element
root = ET.Element("gtgData")

# Parse and append the projects.xml file
projects_tree = ET.parse("projects.xml")
projects_root = projects_tree.getroot()
root.append(projects_root)

# Parse and append the tags.xml file
tags_tree = ET.parse("tags.xml")
tags_root = tags_tree.getroot()
root.append(tags_root)

# Parse and append the gtg_tasks.xml file
gtg_tasks_tree = ET.parse("gtg_tasks.xml")
gtg_tasks_root = gtg_tasks_tree.getroot()
root.append(gtg_tasks_root)

# Add the searchlist element
searchlist_element = ET.SubElement(root, "searchlist")


#############################################################
# General tweaks ############################################
#############################################################

# Rename specific tags
for element in root.iter():
    if element.tag == "addeddate":
        element.tag = "added"
    elif element.tag == "duedate":
        element.tag = "due"
    elif element.tag == "donedate":
        element.tag = "done"
    elif element.tag == "tagstore":
        element.tag = "taglist"
    elif element.tag == "project":
        element.tag = "tasklist"
    elif element.tag == "startdate":
        element.tag = "start"
    elif element.tag == "modifieddate":
        element.tag = "modified"

# Remove the "@" sign from attribute values and add "id" attribute with generated uuid4 value in the taglist
taglist_element = root.find('taglist')
for tag_element in taglist_element.findall('.//tag'):
    for attribute in tag_element.attrib:
        tag_element.set(attribute, tag_element.get(attribute).replace('@', ''))
    tag_element.set("id", str(uuid.uuid4()))


#############################################################
# Subtasks and dates conversion #############################
#############################################################

# Find all tasks in the tasklist and perform the required modifications
tasklist_element = root.find('tasklist')
for task_element in tasklist_element.findall('.//task'):
    # Add a 'content' element if missing
    content_element = task_element.find('content')
    if content_element is None:
        content_element = ET.SubElement(task_element, "content")
        content_element.text = ""  # Set the content to an empty string if it is missing

    # Create a 'subtasks' element and move all 'subtask' elements there as 'sub'
    subtasks_element = ET.SubElement(task_element, "subtasks")
    for subtask_element in task_element.findall('.//subtask'):
        sub_element = ET.SubElement(subtasks_element, "sub")
        sub_element.text = subtask_element.text
        task_element.remove(subtask_element)

    # Create a 'dates' element
    dates_element = ET.SubElement(task_element, "dates")

    # Handle the 'added' tag
    added_element = task_element.find('added')
    if added_element is None:
        added_element = ET.SubElement(dates_element, "added")
        added_element.text = datetime.utcfromtimestamp(0).strftime('%Y-%m-%d')  # Set to Unix epoch date in the form 'y-m-d'
    else:
        task_element.remove(added_element)
        dates_element.append(added_element)

    # Handle the 'due' tag
    due_element = task_element.find('due')
    if due_element is None:
        due_element = ET.SubElement(dates_element, "due")
        due_element.text = ""
    else:
        task_element.remove(due_element)
        dates_element.append(due_element)

    # Handle the 'done' tag
    done_element = task_element.find('done')
    if done_element is None:
        done_element = ET.SubElement(dates_element, "done")
        done_element.text = ""
    else:
        task_element.remove(done_element)
        dates_element.append(done_element)

    # Handle the 'start' tag
    start_element = task_element.find('start')
    if start_element is None:
        start_element = ET.SubElement(dates_element, "start")
        start_element.text = ""
    else:
        task_element.remove(start_element)
        dates_element.append(start_element)

    # Handle the 'modified' tag
    modified_element = task_element.find('modified')
    if modified_element is None:
        modified_element = ET.SubElement(dates_element, "modified")
        modified_element.text = ""
    else:
        task_element.remove(modified_element)
        dates_element.append(modified_element)


#############################################################
# Tasks conversion ##########################################
#############################################################

# Create a dictionary for ID/UUID attributes in tasks
task_dict = {}

# Iterate over each tasklist element
for tasklist_element in root.findall("tasklist"):
    # Iterate over each task element in the tasklist
    for task_element in tasklist_element.findall("task"):
        # Get the task ID and UUID attributes
        task_id = task_element.get("id")
        task_uuid = task_element.get("uuid")

        # Store the ID/UUID attribute pair in the dictionary
        task_dict[task_id] = task_uuid

# Iterate over each tasklist element
for tasklist_element in root.findall("tasklist"):
    # Iterate over each task element in the tasklist
    for task_element in tasklist_element.findall("task"):
        # Find all "sub" elements and replace their value with the proper UUID
        for sub_element in task_element.findall(".//sub"):
            sub_id = sub_element.text
            if sub_id in task_dict:
                sub_element.text = task_dict[sub_id]

# Iterate over each tasklist element
for tasklist_element in root.findall("tasklist"):
    # Iterate over each task element in the tasklist
    for task_element in tasklist_element.findall("task"):
        # Replace the task ID attribute with the UUID
        task_uuid = task_element.get("uuid")
        task_element.set("id", task_uuid)
        task_element.attrib.pop("uuid", None)


#############################################################
# Tags conversion ###########################################
#############################################################

# Create a dictionary for tag ID/Name mapping
tag_dict = {}

# Iterate over each tag element in the taglist
for tag_element in root.findall("taglist/tag"):
    # Get the tag ID and Name
    tag_id = tag_element.get("id")
    tag_name = tag_element.get("name")

    # Store the ID/Name pair in the dictionary
    tag_dict[tag_id] = tag_name

# Iterate over each task element in the tasklist
for task_element in root.findall("tasklist/task"):
    # Get the tags attribute of the task
    tags_attribute = task_element.get("tags")

    # Remove the leading "@" sign from the tags attribute and split into tag names
    tag_names = [tag.lstrip("@") for tag in tags_attribute.split(",")]

    # Get tag IDs for tag names
    tag_ids = [tag_id for tag_id, name in tag_dict.items() if name in tag_names]

    # Create a "tags" item for the task
    tags_item = ET.SubElement(task_element, "tags")

    # Move the tag IDs inside the "tags" item as a value of "tag"
    for tag_id in tag_ids:
        tag_element = ET.SubElement(tags_item, "tag")
        tag_element.text = tag_id


#############################################################
# Cleaning multiple task parents ############################
#############################################################

# Find all task elements
task_elements = root.findall("tasklist/task")

# Create a list to store "task.subtasks.sub" values
sub_values = []

# Loop 1: Collect values
for task_element in task_elements:
    # Get the subtask elements
    subtask_elements = task_element.findall("subtasks/sub")
    for subtask_element in subtask_elements:
        sub_value = subtask_element.text

        # Add the sub value to the list
        sub_values.append(sub_value)

# Loop 2: Test and remove items
for task_element in task_elements:
    # Get all subtask elements
    subtask_elements = task_element.findall("subtasks/sub")
    for subtask_element in subtask_elements:
        sub_value = subtask_element.text

        # Check if the sub value is in the list
        if sub_value in sub_values:
            # Remove the sub item from the current task
            task_element.find("subtasks").remove(subtask_element)


#############################################################
# Writing file ##############################################
#############################################################        

# Create the final tree
final_tree = ET.ElementTree(root)

# Write the XML file with the header and human-readable formatting
final_tree.write("gtg_data.xml", encoding="utf-8", xml_declaration=True, pretty_print=True)

