import requests
from datetime import datetime

def handler(pd: "pipedream"):
    # Your Notion API token
    notion_token = pd.inputs["notion"]["$auth"]["oauth_access_token"]

    # Define your database and template IDs
    clients_database_id = "01d60b02ab8f4dc48cb2081bc08872c5"
    tasks_database_id = "c19166634c39401783b9013f0904865e"
    update_template = "67283d7b53784976a566d59cb3f40c98" 
    review_template = "84cffcd367d242a79e4018086fb173a8"
    dev_template = "20367a60ded248f6b00dc7b12e073692"

    # Set up headers for the API requests
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    # Step 1: Query the Clients database to find pages with "Phase" = "Ongoing Support"
    query_url = f"https://api.notion.com/v1/databases/{clients_database_id}/query"
    query_payload = {
        "filter": {
            "property": "Phase",
            "select": {
                "equals": "Ongoing Support"
            }
        }
    }

    response = requests.post(query_url, json=query_payload, headers=headers)
    print("Query Response:", response.json())

    clients = response.json().get("results", [])

    if not clients:
        print("No clients found with 'Ongoing Support'.")
    else:
        for client in clients:
            client_id = client["id"]
            client_name = client["properties"]["Name"]["title"][0]["text"]["content"]
            task_date = datetime.today().strftime('%Y-%m-%d')

            # Get the current Week in Program and Program Length
            update_counter = client["properties"].get("Week in Program", {}).get("number", 0)
            update_freq_weeks = client["properties"].get("Program Length", {}).get("number", 0)
            update_client_url = f"https://api.notion.com/v1/pages/{client_id}"

            # Fetch the template page's update_icon, update_cover, and content
            template_page_response = requests.get(
                f"https://api.notion.com/v1/pages/{update_template}",
                headers=headers
            )
            template_page = template_page_response.json()
            update_icon = template_page.get("icon")
            update_cover = template_page.get("cover")

            template_content_response = requests.get(
                f"https://api.notion.com/v1/blocks/{update_template}/children",
                headers=headers
            )
            template_content = template_content_response.json().get("results", [])

            # Step 1: Increment the "Week in Program" property for the client
            new_update_counter = update_counter + 1

            if new_update_counter > update_freq_weeks:
                # Update counter to 1 once threshold reached
                new_update_counter = 1

            # create update payload
            update_client_payload = {
                    "properties": {
                        "Week in Program": {
                            "number": new_update_counter
                        }
                    }
                }
                
            create_task_url = "https://api.notion.com/v1/pages"

            update_client_response = requests.patch(update_client_url, json=update_client_payload, headers=headers)
            
            if update_client_response.status_code != 200:
                print(f"Error updating counter for {client_name}: {update_client_response.status_code}")
                print(f"Error response: {update_client_response.json()}")

            # Step 2: Check if not final week of program
            if new_update_counter != update_freq_weeks:
                task_name = f"{client_name} Workout Update"
                
                create_task_payload = {
                    "parent": {
                        "database_id": tasks_database_id
                    },
                    "properties": {
                        "Name": {
                            "title": [
                                {
                                    "text": {
                                        "content": task_name
                                    }
                                }
                            ]
                        },
                        "Client": {
                            "relation": [
                                {
                                    "id": client_id
                                }
                            ]
                        },
                        "Date": {
                            "date": {
                                "start": task_date
                            }
                        }
                    },
                    "children": template_content,  # Use the content fetched from the primary template
                    "icon": update_icon,                   # Include the update_icon (emoji) from the template
                    "cover": update_cover                  # Include the update_cover image from the template
                }

                task_response = requests.post(create_task_url, json=create_task_payload, headers=headers)
                
                if task_response.status_code != 200:
                    print(f"Error creating task for {client_name}: {task_response.status_code}")
                    print(f"Error response: {task_response.json()}")
                else:
                    task_id = task_response.json().get("id")
                    print(f"Created task for {client_name}: {task_id}")

            # Step 3: Check if next week requires program update
            if new_update_counter == update_freq_weeks:
                # Fetch the dev template content
                dev_template_content_response = requests.get(
                    f"https://api.notion.com/v1/blocks/{dev_template}/children",
                    headers=headers
                )
                dev_template_content = dev_template_content_response.json().get("results", [])

                # Create a new task in the Tasks database using the dev template content
                dev_task_name = f"{client_name} Program Development"

                # Fetch the template page's dev_icon, dev_cover, and content
                template_page_response = requests.get(
                    f"https://api.notion.com/v1/pages/{dev_template}",
                    headers=headers
                )
                template_page = template_page_response.json()
                dev_icon = template_page.get("icon")
                dev_cover = template_page.get("cover")

                template_content_response = requests.get(
                    f"https://api.notion.com/v1/blocks/{dev_template}/children",
                    headers=headers
                )
                template_content = template_content_response.json().get("results", [])

                create_dev_task_payload = {
                    "parent": {
                        "database_id": tasks_database_id
                    },
                    "properties": {
                        "Name": {
                            "title": [
                                {
                                    "text": {
                                        "content": dev_task_name
                                    }
                                }
                            ]
                        },
                        "Client": {
                            "relation": [
                                {
                                    "id": client_id
                                }
                            ]
                        },
                        "Date": {
                            "date": {
                                "start": task_date
                            }
                        }
                    },
                    "children": dev_template_content,  # Use the content fetched from the primary template
                    "icon": dev_icon,                   # Include the update_icon (emoji) from the template
                    "cover": dev_cover                  # Include the update_cover image from the template
                }

                dev_task_response = requests.post(create_task_url, json=create_dev_task_payload, headers=headers)
                
                if dev_task_response.status_code != 200:
                    print(f"Error creating dev task for {client_name}: {dev_task_response.status_code}")
                    print(f"Error response: {dev_task_response.json()}")
                else:
                    dev_task_id = dev_task_response.json().get("id")
                    print(f"Created dev task for {client_name}: {dev_task_id}")
                
            # Step 4: Check if next week requires check in
            if new_update_counter == update_freq_weeks - 2:
                print(f"Creating additional task for {client_name} using the check_in template")

                # Fetch the check_in template content
                check_in_template_content_response = requests.get(
                    f"https://api.notion.com/v1/blocks/{review_template}/children",
                    headers=headers
                )
                check_in_template_content = check_in_template_content_response.json().get("results", [])

                # Create a new task in the Tasks database using the check_in template content
                check_in_task_name = f"{client_name} Check In"

                # Fetch the template page's dev_icon, dev_cover, and content
                template_page_response = requests.get(
                    f"https://api.notion.com/v1/pages/{review_template}",
                    headers=headers
                )
                template_page = template_page_response.json()
                dev_icon = template_page.get("icon")
                dev_cover = template_page.get("cover")

                template_content_response = requests.get(
                    f"https://api.notion.com/v1/blocks/{review_template}/children",
                    headers=headers
                )
                template_content = template_content_response.json().get("results", [])

                create_check_in_task_payload = {
                    "parent": {
                        "database_id": tasks_database_id
                    },
                    "properties": {
                        "Name": {
                            "title": [
                                {
                                    "text": {
                                        "content": check_in_task_name
                                    }
                                }
                            ]
                        },
                        "Client": {
                            "relation": [
                                {
                                    "id": client_id
                                }
                            ]
                        },
                        "Date": {
                            "date": {
                                "start": task_date
                            }
                        }
                    },
                    "children": check_in_template_content,  # Use the content fetched from the primary template
                    "icon": dev_icon,                   # Include the update_icon (emoji) from the template
                    "cover": dev_cover                  # Include the update_cover image from the template
                }

                check_in_task_response = requests.post(create_task_url, json=create_check_in_task_payload, headers=headers)
                
                if check_in_task_response.status_code != 200:
                    print(f"Error creating check_in task for {client_name}: {check_in_task_response.status_code}")
                    print(f"Error response: {check_in_task_response.json()}")
                else:
                    check_in_task_id = check_in_task_response.json().get("id")
                    print(f"Created check_in task for {client_name}: {check_in_task_id}")
                